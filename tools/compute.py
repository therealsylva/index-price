#!/usr/bin/env python3
"""Advance one RC3.1 state with a manifest-bound batch of completed facts.

This is the reusable provider adapter and incremental calculator. It carries the
saved movement/cap state forward and applies only completed, in-scope matches
declared by the supplied batch manifest. The sealed historical corpus is read
only for source-frozen component baselines and identity-resolved rosters; it is
never replayed or retuned.

Run with Python 3.11+.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_INDEX: Path
CATALOG: Path
CANONICAL_FACTS: Path
SOURCE_LOCK: Path
BASE_FORWARD_INDEX: Path
BASE_MOVEMENT_EVENTS: Path
PARAMS: Path
INPUT: Path
OUTPUT: Path
EXPECTED_MATCH_IDS: set[str]

PPM = 1_000_000
SECONDS_90 = 5_400
SNAPSHOT_CUT = ""
AS_OF = ""

COMPONENTS = [
    "attack", "creation", "progression", "control", "defence",
    "goalkeeping", "set_piece", "discipline",
]

COMPETITION_IDS = {
    "LaLiga": "football:esp:la-liga",
    "Premier League": "football:eng:premier-league",
    "Ligue 1": "football:fra:ligue-1",
    "Serie A": "football:ita:serie-a",
    "Bundesliga": "football:deu:bundesliga",
    "Champions League Qualification": "football:uefa:champions-league",
    "Europa League Qualification": "football:uefa:europa-league",
    "Conference League Qualification": "football:uefa:conference-league",
}

OPTA_COMPETITIONS = {
    "football:esp:la-liga": "La_Liga",
    "football:eng:premier-league": "EPL",
    "football:fra:ligue-1": "Ligue_1",
    "football:ita:serie-a": "Serie_A",
    "football:deu:bundesliga": "Bundesliga",
    "football:uefa:champions-league": "UCL",
    "football:uefa:europa-league": "UEL",
    "football:uefa:conference-league": "Conference_League",
}

# FotMob's short names versus the Opta public feed's registered names.
CLUB_ALIASES = {
    "agf": "aarhus gymnastikforening",
    "atalanta": "atalanta bergamasca calcio",
    "besiktas": "besiktas jimnastik kulubu",
    "braga": "sporting braga",
    "deportivo a coruna": "rc deportivo de a coruna",
    "egnatia": "ks egnatia rrogozhine",
    "atletico madrid": "club atletico de madrid",
    "malaga": "malaga cf",
    "rayo vallecano": "rayo vallecano de madrid",
    "real betis": "real betis balompie",
    "real sociedad": "real sociedad de futbol",
    "sevilla": "sevilla fc",
    "valencia": "valencia cf",
    "celta vigo": "real club celta de vigo",
    "espanyol": "rcd espanyol de barcelona",
    "real madrid": "real madrid cf",
    "arsenal": "arsenal fc",
    "coventry city": "coventry city fc",
    "hull city": "hull city afc",
    "manchester united": "manchester united fc",
    "crystal palace": "crystal palace fc",
    "ipswich town": "ipswich town fc",
    "sunderland": "sunderland afc",
    "nottingham forest": "nottingham forest fc",
    "leeds united": "leeds united fc",
    "brentford": "brentford fc",
    "tottenham hotspur": "tottenham hotspur fc",
    "marseille": "olympique de marseille",
    "strasbourg": "rc strasbourg alsace",
    "lens": "racing club de lens",
    "auxerre": "association jeunesse auxerroise",
    "le mans": "le mans fc",
    "brest": "stade brestois 29",
    "nice": "ogc nice cote d azur",
    "lorient": "fc lorient",
    "toulouse": "toulouse fc",
    "lyon": "olympique lyonnais",
    "troyes": "estac troyes",
    "inter": "fc internazionale milano",
    "monza": "ac monza",
    "udinese": "udinese calcio",
    "como": "como 1907",
    "genoa": "genoa cfc",
    "napoli": "ssc napoli",
    "parma": "parma calcio 1913",
    "cagliari": "cagliari calcio",
    "angers": "angers sporting club de l ouest",
    "racing santander": "real racing club",
    "rennes": "stade rennais fc",
    "fenerbahce": "fenerbahce spor kulubu",
    "gent": "kaa gent",
    "hoffenheim": "tsg 1899 hoffenheim",
    "kups": "kuopion palloseura",
    "lask": "linzer athletik sport klub",
    "lille": "lille osc",
    "nec nijmegen": "nec",
    "ofi crete": "ofi fc",
    "rapid wien": "sk rapid",
    "rb leipzig": "rasenballsport leipzig",
}

# Clubs whose current registered ID is present in the frozen catalog but whose
# promoted/current league schedule was not yet populated in the small fixture
# mapping asset at its build time.
CLUB_ID_OVERRIDES = {
    "auxerre": ("9bxav814mkuhueiyivyive82d", "Association Jeunesse Auxerroise"),
    "nice": ("bx0cdmzr2gwr70ez72dorx82p", "OGC Nice Côte d'Azur"),
    "lyon": ("121le8unjfzug3iu9pgkqa1c7", "Olympique Lyonnais"),
    "troyes": ("3unkqo2g6ag99gd5ynz1j7vse", "Espérance Sportive Troyes Aube Champagne"),
    "angers": ("75qj99fhg5c0ztj2tva5u4uii", "Angers Sporting Club de l'Ouest"),
    "racing santander": ("bzkwzatvwahmbzok1ymm5vqa1", "Real Racing Club"),
    "rennes": ("z1wbqtd0fz5t5eezjvrbld3h", "Stade Rennais FC"),
    "lask": ("boxkkgnpn38ywao4kzu7dx58h", "Linzer Athletik Sport Klub"),
    "nec nijmegen": ("8iawijq7s9s6d85mjz8wdslki", "NEC"),
}

# Clubs making their first eligible appearance after the sealed catalog cut.
# The namespace keeps the provider identity explicit instead of fabricating an
# Opta identifier.  Once admitted, the ID persists in the calculator checkpoint
# and every later batch resolves it from that saved state.
PROVIDER_CLUB_ONBOARDING = {
    "elversberg": ("fotmob:8232", "SV Elversberg"),
}

PLAYER_WEIGHTS = {
    "FW": [380, 180, 100, 80, 50, 0, 60, 50],
    "AM_W": [250, 250, 180, 100, 50, 0, 50, 40],
    "CM": [100, 180, 220, 220, 120, 0, 40, 50],
    "DM": [50, 100, 180, 220, 250, 0, 30, 70],
    "FB_WB": [80, 180, 180, 120, 250, 0, 50, 60],
    "CB": [40, 40, 100, 150, 450, 0, 40, 80],
    "GK": [0, 30, 70, 100, 80, 570, 50, 50],
    "UNKNOWN": [150, 150, 150, 150, 200, 0, 50, 70],
}
PLAYER_DENOMS = {"FW": 900, "AM_W": 920, "CM": 930, "DM": 900,
                 "FB_WB": 920, "CB": 900, "GK": 950, "UNKNOWN": 920}
PLAYER_GAINS = {"FW": 28_550, "AM_W": 39_215, "CM": 41_150,
                "DM": 36_002, "FB_WB": 40_309, "CB": 43_777,
                "GK": 55_172, "UNKNOWN": 37_739}
CLUB_WEIGHTS = [250_000, 0, 0, 100_000, 180_000, 70_000, 55_000, 55_000]

PLAYER_TERMS = {
    "goal_outcome": [(0, .70)], "shot_on_target_non_goal": [(0, .30)],
    "official_assist": [(1, .60)], "key_pass_non_assist": [(1, .40)],
    "progressive_pass_net": [(2, .65)], "progressive_carry_net": [(2, .35)],
    "ordinary_pass_security": [(3, .45)], "retention_net": [(3, .25)],
    "allocated_recovery": [(3, .20), (4, .20)], "turnover_avoidance": [(3, .10)],
    "tackle_and_interception": [(4, .40)], "block_and_clearance": [(4, .30)],
    "own_goal_avoidance": [(4, .10)], "save": [(5, .60)],
    "cross_claimed": [(5, .15)], "concession_avoidance": [(5, .25)],
    "delivery_net": [(6, .40)], "penalty_won": [(6, .35)],
    "penalty_miss_avoidance": [(6, .25)], "dismissal_avoidance": [(7, .45)],
    "penalty_concession_avoidance": [(7, .25)], "yellow_avoidance": [(7, .20)],
    "foul_avoidance": [(7, .10)],
}
CLUB_TERMS = {
    "goal_outcome": [(0, .55)], "shot_on_target_non_goal": [(0, .20)],
    "creation_actions": [(0, .25)], "ordinary_pass_security": [(3, .40)],
    "retention_net": [(3, .20)], "allocated_recovery": [(3, .20), (4, .20)],
    "progression_net": [(3, .15)], "turnover_avoidance": [(3, .05)],
    "tackle_and_interception": [(4, .40)], "block_and_clearance": [(4, .30)],
    "own_goal_avoidance": [(4, .10)], "save": [(5, .60)],
    "cross_claimed": [(5, .15)], "concession_avoidance": [(5, .25)],
    "delivery_net": [(6, .40)], "penalty_won": [(6, .35)],
    "penalty_miss_avoidance": [(6, .25)], "dismissal_avoidance": [(7, .45)],
    "penalty_concession_avoidance": [(7, .25)], "yellow_avoidance": [(7, .20)],
    "foul_avoidance": [(7, .10)],
}

PLAYER_INTERACTIONS = [
    (0, 4, -.07), (0, 5, -.05), (1, 4, -.08), (1, 3, -.03),
    (2, 3, -.06), (2, 4, -.03), (3, 3, -.04), (3, 0, -.02),
    (4, 0, .08), (4, 1, .03), (5, 0, .08), (5, 1, .04),
    (6, 6, -.05), (6, 7, .03),
]
CLUB_INTERACTIONS = [
    (0, 4, -.07), (0, 5, -.05), (4, 0, .08), (5, 0, .08),
    (3, 3, -.04), (3, 0, -.02), (6, 6, -.05), (6, 7, .03),
]

ALL_PLAYER_METRICS = list(PLAYER_TERMS)
ALL_CLUB_METRICS = list(CLUB_TERMS)
EXTENDED_ONLY = {"progressive_pass_net", "progressive_carry_net", "delivery_net", "progression_net"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Apply one manifest-bound RC3.1 football price update.",
    )
    parser.add_argument(
        "--base-forward-index",
        type=Path,
        required=True,
        help="Current detailed index state produced by the previous update.",
    )
    parser.add_argument(
        "--base-movement-events",
        type=Path,
        required=True,
        help="Cumulative movement ledger produced by the previous update.",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="Root of the restored sealed historical calibration archive.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing the new FotMob match JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="New or empty directory in which to write the candidate and audit artifacts.",
    )
    parser.add_argument(
        "--batch-manifest",
        type=Path,
        required=True,
        help="Update manifest declaring the exact time window and expected match IDs.",
    )
    parser.add_argument(
        "--parameters",
        type=Path,
        default=REPO_ROOT / "config/native-policy-v2.json",
        help="RC3.1.1 parameter package whose hash is bound into the receipt.",
    )
    return parser.parse_args()


def load_batch_manifest(path: Path) -> dict:
    manifest = load_json(path)
    expected_keys = {"schema", "from", "asOf", "provider", "expectedMatchIds"}
    if set(manifest) != expected_keys:
        raise ValueError("batch manifest contains unexpected or missing fields")
    if manifest["schema"] != "blackbook.index.update-batch.v1":
        raise ValueError("unsupported batch manifest schema")
    if manifest["provider"] != "fotmob":
        raise ValueError("this adapter accepts provider='fotmob'")
    start, end = dt(manifest["from"]), dt(manifest["asOf"])
    if (start.tzinfo is None or end.tzinfo is None
            or start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0)
            or start >= end):
        raise ValueError("batch manifest must define an increasing UTC window")
    midnight = (0, 0, 0, 0)
    if ((start.hour, start.minute, start.second, start.microsecond) != midnight
            or (end.hour, end.minute, end.second, end.microsecond) != midnight):
        raise ValueError("batch manifest cuts must be at 00:00 UTC")
    raw_ids = manifest["expectedMatchIds"]
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("batch manifest expectedMatchIds must be a non-empty array")
    normalized = [value if str(value).startswith("fotmob:") else f"fotmob:{value}" for value in raw_ids]
    if any(not re.fullmatch(r"fotmob:[0-9]+", value) for value in normalized):
        raise ValueError("batch manifest contains an invalid FotMob match ID")
    if len(normalized) != len(set(normalized)):
        raise ValueError("batch manifest contains duplicate match IDs")
    return {
        **manifest,
        "from": start.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "asOf": end.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "expectedMatchIds": normalized,
    }


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, value) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        f.write("\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(value: str | None) -> str:
    value = (value or "").lower().translate(str.maketrans({
        "ø": "o", "đ": "d", "ß": "ss", "ı": "i", "ł": "l",
        "æ": "ae", "ð": "d", "þ": "th", "œ": "oe",
    }))
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.replace("&", " and ")
    return " ".join(re.findall(r"[a-z0-9]+", value))


def stripped_club(value: str) -> str:
    tokens = norm(value).split()
    noise = {"fc", "afc", "cf", "ac", "sc", "club", "fk", "sk", "calcio", "football", "futbol"}
    return " ".join(t for t in tokens if t not in noise)


def name_similarity(a: str, b: str) -> float:
    aa, bb = norm(a), norm(b)
    if not aa or not bb:
        return 0.0
    direct = SequenceMatcher(None, aa, bb).ratio()
    token = SequenceMatcher(None, " ".join(sorted(aa.split())), " ".join(sorted(bb.split()))).ratio()
    sa, sb = stripped_club(aa), stripped_club(bb)
    stripped = SequenceMatcher(None, sa, sb).ratio() if sa and sb else 0.0
    containment = min(len(sa), len(sb)) / max(len(sa), len(sb)) if sa in sb or sb in sa else 0.0
    return max(direct, token, stripped, containment)


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def weighted_median(values):
    values = sorted(values, key=lambda x: x[0])
    total = sum(w for _, w in values)
    acc = 0.0
    for i, (v, w) in enumerate(values):
        acc += w
        if acc * 2 > total:
            return v
        if abs(acc * 2 - total) < 1e-9:
            return (v + values[min(i + 1, len(values) - 1)][0]) / 2
    return values[-1][0]


def robust_baseline(values, minimum=30.0):
    if not values or sum(w for _, w in values) < minimum:
        return None
    center = weighted_median(values)
    mad = weighted_median([(abs(v - center), w) for v, w in values])
    scale = mad * 1.4826
    if scale <= 0:
        expanded = []
        total = sum(w for _, w in values)
        variance = sum(w * (v - center) ** 2 for v, w in values) / max(total, 1)
        scale = math.sqrt(variance)
    if scale <= 0:
        scale = PPM
    return center, scale, sum(w for _, w in values)


def flatten_stats(player: dict) -> dict:
    out = {}
    for group in player.get("stats") or []:
        for item in (group.get("stats") or {}).values():
            key = item.get("key")
            stat = item.get("stat") or {}
            if key:
                out[key] = {"value": stat.get("value", 0) or 0,
                            "total": stat.get("total")}
    return out


def sval(stats, key, default=0.0):
    return float((stats.get(key) or {}).get("value", default) or default)


def sfrac(stats, key):
    item = stats.get(key) or {}
    value = float(item.get("value", 0) or 0)
    total = item.get("total")
    return value, float(total if total is not None else value)


def player_metrics(player: dict, meta: dict) -> tuple[dict, int]:
    s = flatten_stats(player)
    minutes = int(round(sval(s, "minutes_played", 0)))
    goals = sval(s, "goals")
    assists = sval(s, "assists")
    sot = sval(s, "ShotsOnTarget")
    chances = sval(s, "chances_created")
    passes, pass_total = sfrac(s, "accurate_passes")
    dribbles, dribble_total = sfrac(s, "dribbles_succeeded")
    crosses, cross_total = sfrac(s, "accurate_crosses")
    progressive_pass = sval(s, "line_breaking_passes") + sval(s, "passes_into_final_third")
    yellow = int(meta.get("yellow", 0))
    red = int(meta.get("red", 0))
    metrics = {
        "goal_outcome": goals,
        "shot_on_target_non_goal": max(sot - goals, 0),
        "official_assist": assists,
        "key_pass_non_assist": max(chances - assists, 0),
        # Provider bridge: line-breaking + final-third passes are the available
        # progressive-pass proxy; the same definition is used for its baseline.
        "progressive_pass_net": progressive_pass,
        "progressive_carry_net": dribbles - max(dribble_total - dribbles, 0),
        "ordinary_pass_security": passes - max(pass_total - passes, 0),
        "retention_net": dribbles - max(dribble_total - dribbles, 0),
        "allocated_recovery": .5 * sval(s, "recoveries"),
        "turnover_avoidance": -sval(s, "dispossessed"),
        "tackle_and_interception": sval(s, "matchstats.headers.tackles") + sval(s, "interceptions"),
        "block_and_clearance": sval(s, "shot_blocks") + sval(s, "clearances"),
        "own_goal_avoidance": -sval(s, "owngoal"),
        "save": sval(s, "saves"),
        "cross_claimed": sval(s, "keeper_high_claim"),
        "concession_avoidance": -sval(s, "goals_conceded"),
        "delivery_net": crosses - max(cross_total - crosses, 0),
        "penalty_won": sval(s, "penalties_won"),
        "penalty_miss_avoidance": -sval(s, "missed_penalty"),
        "dismissal_avoidance": -red,
        "penalty_concession_avoidance": -sval(s, "conceded_penalties"),
        "yellow_avoidance": -yellow,
        "foul_avoidance": -sval(s, "fouls"),
    }
    return {k: int(round(v * PPM)) for k, v in metrics.items()}, minutes


def lineup_meta(match: dict):
    output = {}
    lineup = (match.get("content") or {}).get("lineup") or {}
    for side_key in ("homeTeam", "awayTeam"):
        side = lineup.get(side_key) or {}
        for group in ("starters", "subs"):
            for p in side.get(group) or []:
                events = ((p.get("performance") or {}).get("events") or [])
                types = [norm(e.get("type")) for e in events]
                output[str(p.get("id"))] = {
                    "shirt": str(p.get("shirtNumber") or ""),
                    "usual": p.get("usualPlayingPositionId"),
                    "position_id": p.get("positionId"),
                    "layout": p.get("horizontalLayout") or p.get("verticalLayout") or {},
                    "yellow": sum("yellow" in t and "second" not in t for t in types),
                    "red": sum("red" in t or "second yellow" in t for t in types),
                }
    return output


def team_stat(match: dict, key: str):
    groups = (((match.get("content") or {}).get("stats") or {}).get("Periods") or {}).get("All", {}).get("stats") or []
    for group in groups:
        for item in group.get("stats") or []:
            if item.get("key") == key:
                vals = item.get("stats") or [0, 0]
                return float(vals[0] or 0), float(vals[1] or 0)
    return 0.0, 0.0


def role_from_sources(current_role, opta_row, meta, is_goalkeeper=False):
    if current_role and current_role != "UNKNOWN":
        return current_role
    if is_goalkeeper:
        return "GK"
    if opta_row:
        pos = norm(opta_row.get("position"))
        side = norm(opta_row.get("position_side"))
        if "goalkeeper" in pos:
            return "GK"
        if "defender" in pos:
            return "CB" if side in ("", "centre", "center") else "FB_WB"
        if "forward" in pos:
            return "FW" if side in ("", "centre", "center") else "AM_W"
        if "midfielder" in pos:
            return "CM"
    usual = meta.get("usual")
    if usual == 0:
        return "GK"
    if usual == 1:
        layout = meta.get("layout") or {}
        y = layout.get("y", .5)
        return "FB_WB" if y < .30 or y > .70 else "CB"
    if usual == 2:
        return "CM"
    if usual == 3:
        return "FW"
    return "UNKNOWN"


def player_name_score(fotmob_name, candidate, shirt, minutes):
    full = candidate.get("full_name") or candidate.get("player_name") or ""
    abbreviated = candidate.get("player_name") or ""
    score = 70 * max(name_similarity(fotmob_name, full), name_similarity(fotmob_name, abbreviated))
    fn = norm(fotmob_name).split()
    cn = norm(candidate.get("last_name") or full).split()
    if fn and cn and (fn[-1] == cn[-1] or fn[-1] in cn or cn[-1] in fn):
        score += 22
    public_tokens = norm(full).split()
    if (fn and public_tokens and len(public_tokens[0]) == 1
            and fn[0][0] == public_tokens[0][0] and fn[-1] == public_tokens[-1]):
        score += 12
    cshirt = candidate.get("shirt_number")
    if shirt and cshirt is not None and str(int(float(cshirt))) == str(shirt):
        score += 24
    cminutes = candidate.get("minutes_played")
    if cminutes is not None:
        diff = abs(float(cminutes) - minutes)
        score += 18 if diff <= 1 else 9 if diff <= 5 else 0
    return score


def map_players_for_team(fplayers, candidates, player_info, meta):
    pairs = []
    for fp in fplayers:
        fstats = flatten_stats(fp)
        minutes = int(round(sval(fstats, "minutes_played", 0)))
        fm = meta.get(str(fp.get("id")), {})
        for c in candidates:
            pid = c.get("player_id")
            info = player_info.get(pid, {})
            candidate = dict(c)
            candidate.update(info)
            score = player_name_score(fp.get("name", ""), candidate, fm.get("shirt"), minutes)
            pairs.append((score, str(fp.get("id")), pid, c))
    assigned_fb, assigned_opta, output = set(), set(), {}
    for score, fid, pid, row in sorted(pairs, reverse=True, key=lambda x: x[0]):
        if score < 55 or fid in assigned_fb or pid in assigned_opta:
            continue
        assigned_fb.add(fid)
        assigned_opta.add(pid)
        output[fid] = (pid, row, score)
    return output


def strict_global_player(name, player_info, surname_index, current_by_id):
    """Return one globally unambiguous player ID, or None.

    This is only a transfer/new-roster fallback.  It requires an exact public
    full-name field or matching first and last names with a clear score margin;
    common-name ties are deliberately held.
    """
    tokens = norm(name).split()
    if len(tokens) < 2:
        return None
    pool = {}
    for token in tokens[-2:]:
        for pid in surname_index.get(token, []):
            pool[pid] = player_info[pid]
    ranked = []
    for pid, info in pool.items():
        full = info.get("full_name") or info.get("player_name") or ""
        first_tokens = norm(info.get("first_name") or full).split()
        last_tokens = norm(info.get("last_name") or full).split()
        initial_match = bool(first_tokens and tokens and first_tokens[0][0] == tokens[0][0])
        abbreviated_first = bool(first_tokens) and len(first_tokens[0]) == 1
        first_match = bool(first_tokens) and (
            tokens[0] == first_tokens[0] or
            (min(len(tokens[0]), len(first_tokens[0])) >= 4 and
             (tokens[0].startswith(first_tokens[0]) or first_tokens[0].startswith(tokens[0])))
        )
        last_match = bool(last_tokens) and tokens[-1] in last_tokens
        unique_initial_surname = abbreviated_first and initial_match and last_match
        exact_public = norm(info.get("player_name")) == norm(name)
        similarity = max(name_similarity(name, full), name_similarity(name, info.get("player_name") or ""))
        if not exact_public and not (first_match and last_match and similarity >= .72) and not unique_initial_surname:
            continue
        score = similarity + (.12 if exact_public else 0) + (.08 if unique_initial_surname else 0)
        score += .03 if "player:" + pid in current_by_id else 0
        ranked.append((score, exact_public, pid))
    ranked.sort(reverse=True)
    if not ranked:
        return None
    exact = [r for r in ranked if r[1]]
    if len(exact) == 1:
        return exact[0][2]
    if len(ranked) == 1 or ranked[0][0] - ranked[1][0] >= .035:
        return ranked[0][2]
    return None


def resolve_catalog_club(name, catalog_clubs):
    if norm(name) in CLUB_ID_OVERRIDES:
        team_id, registered = CLUB_ID_OVERRIDES[norm(name)]
        return 1.0, team_id, registered
    if norm(name) in PROVIDER_CLUB_ONBOARDING:
        team_id, registered = PROVIDER_CLUB_ONBOARDING[norm(name)]
        return 1.0, team_id, registered
    target = CLUB_ALIASES.get(norm(name), norm(name))
    ranked = sorted(
        (
            name_similarity(target, registered),
            team_id,
            registered,
        )
        for team_id, registered in catalog_clubs
    )
    best = ranked[-1] if ranked else None
    if not best or best[0] < .58:
        raise RuntimeError(f"Unable to resolve club {name!r}; best={best}")
    return best


def build_identity_assets(catalog, canonical_facts, prior_events, current_by_id):
    """Build latest sealed club rosters and global exact-name fallbacks.

    Historical lineup facts establish the last known Opta club assignment.
    The cumulative accepted movement ledger then advances those assignments
    without requiring licensed source payloads to be committed.
    """
    player_info = {}
    full_index = defaultdict(list)
    surname_index = defaultdict(list)
    catalog_clubs = []
    for entity in catalog["entities"]:
        entity_id = entity["entity_id"]
        if entity["kind"] == "CLUB":
            catalog_clubs.append((entity_id.split(":", 1)[1], entity["display_name"]))
            continue
        pid = entity_id.split(":", 1)[1]
        display_name = entity["display_name"]
        tokens = display_name.split()
        info = {
            "player_id": pid,
            "player_name": display_name,
            "full_name": display_name,
            "first_name": tokens[0] if tokens else "",
            "last_name": tokens[-1] if tokens else "",
        }
        player_info[pid] = info
        full_index[norm(display_name)].append(pid)
        for token in set(norm(info["last_name"] or display_name).split()):
            if len(token) >= 3:
                surname_index[token].append(pid)

    assignments = {}

    def assign(player_id, club_id, effective_at, position=""):
        pid = player_id.split(":", 1)[-1]
        cid = club_id.split(":", 1)[-1]
        if pid not in player_info:
            return
        at = dt(effective_at) if isinstance(effective_at, str) else effective_at
        previous = assignments.get(pid)
        if previous is None or at >= previous[0]:
            assignments[pid] = (at, cid, position or "")

    with canonical_facts.open(encoding="utf-8") as source:
        for line in source:
            if '"fact_type":"LINEUP_CONFIRMATION"' not in line:
                continue
            fact = json.loads(line)
            if fact.get("fact_status") != "ACTIVE":
                continue
            data = ((fact.get("payload") or {}).get("data") or {})
            club_id = data.get("club_id")
            effective_at = data.get("effective_at") or fact.get("effective_at")
            if not club_id or not effective_at:
                continue
            for entry in data.get("entries") or []:
                if entry.get("player_id"):
                    assign(entry["player_id"], club_id, effective_at, entry.get("position"))

    prior_by_match = defaultdict(list)
    for event in prior_events:
        prior_by_match[event["match_id"]].append(event)
    for events in prior_by_match.values():
        clubs = {event["entity_id"] for event in events if event.get("kind") == "CLUB"}
        if len(clubs) != 2:
            continue
        for event in events:
            if event.get("kind") != "PLAYER" or event.get("opponent_id") not in clubs:
                continue
            own = next(club for club in clubs if club != event["opponent_id"])
            assign(event["entity_id"], own, event["kickoff"], event.get("role"))

    rosters = defaultdict(dict)
    for pid, (_, club_id, position) in assignments.items():
        info = player_info[pid]
        rosters[club_id][pid] = {
            **info,
            "team_id": club_id,
            "position": position,
            "position_side": "",
            "shirt_number": None,
            "minutes_played": None,
        }

    # The current forward universe is the preferred global fallback surface.
    current_ids = {entity_id.split(":", 1)[1] for entity_id in current_by_id if entity_id.startswith("player:")}
    for key in list(full_index):
        full_index[key].sort(key=lambda pid: pid not in current_ids)
    return catalog_clubs, player_info, full_index, surname_index, rosters


def build_snapshot_baselines(rows):
    pools = defaultdict(list)
    for row in rows:
        cs = row.get("component_state") or {}
        metrics = cs.get("metrics") or {}
        active = cs.get("active_seconds") or 0
        if active <= 0:
            continue
        kind = "PLAYER" if row["entity_id"].startswith("player:") else "CLUB"
        role = cs.get("role") or "UNKNOWN"
        comp = cs.get("competition_id") or "*"
        exposure = min(active / SECONDS_90, 1.0)
        for metric, units in metrics.items():
            rate = units * SECONDS_90 / active
            for key in ((kind, role, comp, metric), (kind, role, "*", metric), (kind, "*", "*", metric)):
                pools[key].append((rate, exposure))
    return pools


def add_window_baselines(pools, cells):
    for cell in cells:
        active = cell["active_seconds"]
        exposure = min(active / SECONDS_90, 1.0)
        for metric, units in cell["metrics"].items():
            rate = units * SECONDS_90 / active
            for key in ((cell["kind"], cell["role"], cell["competition_id"], metric),
                        (cell["kind"], cell["role"], "*", metric),
                        (cell["kind"], "*", "*", metric)):
                pools[key].append((rate, exposure))


def baseline_for(snapshot_pools, window_pools, kind, role, comp, metric):
    candidates = ((kind, role, comp, metric), (kind, role, "*", metric), (kind, "*", "*", metric))
    # Extended-only metrics do not exist in the frozen BASIC replay; use the
    # small observation window, while all shared metrics remain source-frozen.
    primary = window_pools if metric in EXTENDED_ONLY else snapshot_pools
    secondary = snapshot_pools if primary is window_pools else window_pools
    for pools, minimum in ((primary, 30.0), (secondary, 30.0)):
        for key in candidates:
            base = robust_baseline(pools.get(key), minimum)
            if base:
                return base, ("WINDOW_FALLBACK" if pools is window_pools else "SNAPSHOT_CELL")
    raise RuntimeError(f"No baseline for {kind}/{role}/{comp}/{metric}")


def normalize_cell(cell, snapshot_pools, window_pools):
    terms = PLAYER_TERMS if cell["kind"] == "PLAYER" else CLUB_TERMS
    observed = [0.0] * 8
    sources = set()
    for metric, units in cell["metrics"].items():
        base, source = baseline_for(snapshot_pools, window_pools, cell["kind"], cell["role"], cell["competition_id"], metric)
        center, scale, _ = base
        rate = units * SECONDS_90 / cell["active_seconds"]
        z = (rate - center) / scale * PPM
        smooth = 2_500_000 * math.tanh(z / 2_500_000)
        for idx, weight in terms[metric]:
            observed[idx] += smooth * weight
        sources.add(source)
    return [int(round(v)) for v in observed], sorted(sources)


def player_reference_weights(role):
    role = role if role in PLAYER_WEIGHTS else "UNKNOWN"
    raw, denom = PLAYER_WEIGHTS[role], PLAYER_DENOMS[role]
    out = [int(round(v / denom * PPM)) for v in raw]
    out[-1] += PPM - sum(out)
    return out


def renormalize(weights, observed_components, target):
    source = sum(weights[i] for i in observed_components)
    if source <= 0:
        return [0] * 8
    out = [0] * 8
    assigned = 0
    for i in observed_components[:-1]:
        out[i] = int(round(weights[i] * target / source))
        assigned += out[i]
    out[observed_components[-1]] = target - assigned
    return out


def interaction_adjustment(opponent, kind):
    adjustment = [0.0] * 8
    interactions = PLAYER_INTERACTIONS if kind == "PLAYER" else CLUB_INTERACTIONS
    for subject, opp, loading in interactions:
        adjustment[subject] += opponent[opp] * loading
    return adjustment


def decay_slow(slow, last, kickoff, kind):
    if not last:
        return list(slow)
    elapsed = max((kickoff - last).total_seconds() / 86400, 0)
    half_life = 720 if kind == "PLAYER" else 900
    factor = 2 ** (-elapsed / half_life)
    return [int(round(v * factor)) for v in slow]


def logistic(x):
    if x > 20:
        return 1.0
    if x < -20:
        return 0.0
    return 1 / (1 + math.exp(-x))


def ordered_logistic(home_minus_away):
    fixture = home_minus_away + 395_293
    home = logistic((fixture - 592_136) / PPM)
    away = logistic((-fixture - 592_136) / PPM)
    return home, max(0.0, 1 - home - away), away


def radial(performance, result, cap):
    l1 = abs(performance) + abs(result)
    if l1 <= cap:
        return performance, result, performance + result
    p = performance * cap / l1
    r = result * cap / l1
    return p, r, p + r


def rolling_delta(acc, raw, cap):
    return cap * math.tanh((acc + raw) / cap) - cap * math.tanh(acc / cap)


def state_from_forward_row(row, prior_events):
    reliability = int(row.get("personal_reliability_ppm") or 0)
    effective = 20 * reliability / max(PPM - reliability, 1)
    rolling_events = []
    for event in prior_events:
        raw = int(event.get("performance_log_return_ppm") or 0)
        raw += int(event.get("result_log_return_ppm") or 0)
        rolling_events.append((dt(event["kickoff"]), raw))
    price = int(row["reference_micros"])
    return {
        "entity_id": row["entity_id"],
        "kind": row.get("kind") or ("PLAYER" if row["entity_id"].startswith("player:") else "CLUB"),
        "name": row.get("display_name") or row["entity_id"],
        "role": row.get("role") or "UNKNOWN",
        "price": price,
        "start_price": int(row.get("snapshot_reference_micros") or price),
        "batch_start_price": price,
        "slow": list(row.get("slow_level_per90") or [0] * 8),
        "density": int(row.get("density_ppm") or 0),
        "reliability": reliability,
        "effective": effective,
        "last": dt(row.get("effective_at") or SNAPSHOT_CUT),
        "rolling_events": rolling_events,
        "base_matches": int(row.get("matches_applied") or 0),
        "events": [],
    }


def ensure_state(states, entity_id, kind, name, role="UNKNOWN"):
    if entity_id not in states:
        states[entity_id] = {
            "entity_id": entity_id, "kind": kind, "name": name, "role": role,
            "price": 1_000_000_000, "start_price": 1_000_000_000,
            "batch_start_price": 1_000_000_000,
            "slow": [0] * 8, "density": 0, "reliability": 0, "effective": 0.0,
            "last": dt(SNAPSHOT_CUT), "rolling_events": [], "base_matches": 0, "events": [],
        }
    if name and (states[entity_id]["name"].startswith(("player:", "club:")) or kind == "PLAYER"):
        states[entity_id]["name"] = name
    if kind == "PLAYER" and states[entity_id]["role"] == "UNKNOWN" and role != "UNKNOWN":
        states[entity_id]["role"] = role
    return states[entity_id]


def main():
    global HISTORICAL_INDEX, CATALOG, CANONICAL_FACTS, SOURCE_LOCK
    global BASE_FORWARD_INDEX, BASE_MOVEMENT_EVENTS, PARAMS, INPUT, OUTPUT
    global SNAPSHOT_CUT, AS_OF, EXPECTED_MATCH_IDS

    args = parse_args()
    batch_manifest_path = args.batch_manifest.resolve()
    batch_manifest = load_batch_manifest(batch_manifest_path)
    archive = args.archive_root.resolve()
    materialized = archive / "derived/materialized-calibrated-v2-final"
    HISTORICAL_INDEX = materialized / "current-index.json"
    CATALOG = archive / "derived/entity-catalog.json"
    CANONICAL_FACTS = archive / "derived/canonical-facts.ndjson"
    SOURCE_LOCK = archive / "derived/source-lock.json"
    BASE_FORWARD_INDEX = args.base_forward_index.resolve()
    BASE_MOVEMENT_EVENTS = args.base_movement_events.resolve()
    PARAMS = args.parameters.resolve()
    INPUT = args.input_dir.resolve()
    OUTPUT = args.output_dir.resolve()
    SNAPSHOT_CUT = batch_manifest["from"]
    AS_OF = batch_manifest["asOf"]
    EXPECTED_MATCH_IDS = set(batch_manifest["expectedMatchIds"])

    required = [
        HISTORICAL_INDEX,
        CATALOG,
        CANONICAL_FACTS,
        SOURCE_LOCK,
        BASE_FORWARD_INDEX,
        BASE_MOVEMENT_EVENTS,
        PARAMS,
        batch_manifest_path,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required input files: " + ", ".join(missing))
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError(f"Output directory must be empty: {OUTPUT}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    historical = load_json(HISTORICAL_INDEX)
    forward = load_json(BASE_FORWARD_INDEX)
    prior_events = load_json(BASE_MOVEMENT_EVENTS)
    catalog = load_json(CATALOG)
    parameters = load_json(PARAMS)
    if parameters.get("schema") != "blackbook.index.rc3.1.native-policy.v2":
        raise RuntimeError("unsupported RC3.1 parameter package")
    if forward.get("schema") != "blackbook.index.forward-extended.v1":
        raise RuntimeError("unsupported base forward index schema")
    if not isinstance(prior_events, list):
        raise RuntimeError("base movement ledger must be an array")
    if forward.get("as_of") != SNAPSHOT_CUT:
        raise RuntimeError(
            f"Base forward index is {forward.get('as_of')!r}; expected exact manifest cut {SNAPSHOT_CUT!r}"
        )
    current_rows = forward["rows"]
    current_by_id = {r["entity_id"]: r for r in current_rows}
    if len(current_by_id) != len(current_rows):
        raise RuntimeError("base forward index contains duplicate entities")
    prior_by_entity = defaultdict(list)
    prior_identities = set()
    for event in prior_events:
        if dt(event["kickoff"]) >= dt(SNAPSHOT_CUT):
            raise RuntimeError("base movement ledger reaches or exceeds the batch cut")
        identity = (event.get("match_id"), event.get("entity_id"))
        if identity in prior_identities:
            raise RuntimeError(f"base movement ledger contains duplicate event {identity}")
        prior_identities.add(identity)
        prior_by_entity[event["entity_id"]].append(event)
    for entity_id, events in prior_by_entity.items():
        if entity_id not in current_by_id:
            raise RuntimeError(f"base movement ledger references unknown entity {entity_id}")
        latest = max(events, key=lambda event: (event["kickoff"], event["match_id"]))
        if int(latest["next_reference_micros"]) != int(current_by_id[entity_id]["reference_micros"]):
            raise RuntimeError(f"base movement ledger does not close at current state for {entity_id}")
    states = {
        r["entity_id"]: state_from_forward_row(r, prior_by_entity.get(r["entity_id"], []))
        for r in current_rows
    }
    catalog_clubs, player_info, full_index, surname_index, rosters = build_identity_assets(
        catalog, CANONICAL_FACTS, prior_events, current_by_id
    )
    # The saved checkpoint may already contain clubs admitted after the sealed
    # historical catalog cut. Prefer their stable IDs in all later batches.
    known_clubs = {team_id: registered for team_id, registered in catalog_clubs}
    for row in current_rows:
        if row.get("kind") == "CLUB":
            known_clubs.setdefault(
                row["entity_id"].split(":", 1)[1],
                row["display_name"],
            )
    catalog_clubs = sorted(known_clubs.items())

    match_files = sorted(INPUT.glob("*.json"))
    matches = []
    for path in match_files:
        m = load_json(path)
        g = m.get("general") or {}
        if not g.get("finished") or g.get("leagueName") not in COMPETITION_IDS:
            continue
        kickoff = dt(g["matchTimeUTCDate"])
        if not (dt(SNAPSHOT_CUT) <= kickoff < dt(AS_OF)):
            continue
        matches.append({"path": path, "raw": m, "kickoff": kickoff,
                        "competition_id": COMPETITION_IDS[g["leagueName"]]})
    matches.sort(key=lambda x: (x["kickoff"], int(x["raw"]["general"]["matchId"])))
    discovered_match_ids = {
        "fotmob:" + str(item["raw"]["general"]["matchId"]) for item in matches
    }
    if len(discovered_match_ids) != len(matches):
        raise RuntimeError("duplicate FotMob match payload in input directory")
    if discovered_match_ids != EXPECTED_MATCH_IDS:
        missing_ids = sorted(EXPECTED_MATCH_IDS - discovered_match_ids)
        unexpected_ids = sorted(discovered_match_ids - EXPECTED_MATCH_IDS)
        raise RuntimeError(
            f"Batch manifest mismatch; missing={missing_ids}, unexpected={unexpected_ids}"
        )

    for item in matches:
        m = item["raw"]
        teams = m["header"]["teams"]
        home = resolve_catalog_club(teams[0]["name"], catalog_clubs)
        away = resolve_catalog_club(teams[1]["name"], catalog_clubs)
        item["home_id"], item["away_id"] = "club:" + home[1], "club:" + away[1]
        item["home_registered_name"], item["away_registered_name"] = home[2], away[2]
        item["club_mapping"] = (
            "PROVIDER_ID_ONBOARDING"
            if home[1].startswith("fotmob:") or away[1].startswith("fotmob:")
            else "SEALED_CATALOG"
        )
        item["club_mapping_scores"] = [round(home[0], 4), round(away[0], 4)]

    cells = []
    audits = []
    latest_player_name = {}
    unmatched_rows = []
    for item in matches:
        m = item["raw"]
        g, teams = m["general"], m["header"]["teams"]
        meta = lineup_meta(m)
        pstats_obj = (m.get("content") or {}).get("playerStats") or {}
        fplayers = list(pstats_obj.values())
        by_fteam = defaultdict(list)
        for p in fplayers:
            by_fteam[str(p.get("teamId"))].append(p)
        match_player_map = {}
        mapped_scores = {}
        for side, entity_id in ((0, item["home_id"]), (1, item["away_id"])):
            fotmob_team_id = str(g["homeTeam" if side == 0 else "awayTeam"]["id"])
            opta_team_id = entity_id.split(":", 1)[1]
            fps = by_fteam.get(fotmob_team_id, [])
            candidates = list(rosters.get(opta_team_id, {}).values())
            # Add globally unique exact full-name identities for new transfers.
            # Ambiguous names are held; there is no provider-ID fabrication.
            existing = {r["player_id"] for r in candidates}
            for fp in fps:
                ids = full_index.get(norm(fp.get("name")), [])
                strict_id = ids[0] if len(ids) == 1 else strict_global_player(
                    fp.get("name", ""), player_info, surname_index, current_by_id)
                if strict_id and strict_id not in existing:
                    info = player_info[strict_id]
                    candidates.append({"player_id": strict_id, "player_name": info["player_name"],
                                       "team_id": opta_team_id, "position": "", "position_side": "",
                                       "shirt_number": None, "minutes_played": None})
                    existing.add(strict_id)
            mapped = map_players_for_team(fps, candidates, player_info, meta)
            for fid, value in mapped.items():
                match_player_map[fid] = value
                mapped_scores[fid] = value[2]

        club_player_metrics = {item["home_id"]: defaultdict(int), item["away_id"]: defaultdict(int)}
        mapped_players = 0
        active_players = 0
        for p in fplayers:
            fid = str(p.get("id"))
            fm = meta.get(fid, {})
            metrics, minutes = player_metrics(p, fm)
            if minutes <= 0:
                continue
            active_players += 1
            club_id = item["home_id"] if int(p.get("teamId")) == int(g["homeTeam"]["id"]) else item["away_id"]
            for key, value in metrics.items():
                club_player_metrics[club_id][key] += value
            mapping = match_player_map.get(fid)
            if not mapping:
                unmatched_rows.append({"fotmob_match_id": g["matchId"], "kickoff": g["matchTimeUTCDate"],
                                       "club_id": club_id, "player_name": p.get("name"),
                                       "fotmob_player_id": fid, "minutes": minutes})
                continue
            pid, opta_row, score = mapping
            entity_id = "player:" + pid
            current_role = (current_by_id.get(entity_id) or {}).get("role")
            role = role_from_sources(current_role, opta_row, fm, p.get("isGoalkeeper", False))
            cells.append({
                "kind": "PLAYER", "entity_id": entity_id, "name": p.get("name"), "role": role,
                "club_id": club_id, "opponent_id": item["away_id"] if club_id == item["home_id"] else item["home_id"],
                "competition_id": item["competition_id"], "active_seconds": min(minutes * 60, 7_200),
                "metrics": metrics, "kickoff": item["kickoff"], "match_id": "fotmob:" + str(g["matchId"]),
                "profile": "EXTENDED", "side": None, "result": None,
            })
            latest_player_name[entity_id] = p.get("name")
            rosters[club_id.split(":", 1)[1]][pid] = {
                **player_info[pid], "team_id": club_id.split(":", 1)[1],
                "position": opta_row.get("position", ""), "position_side": "",
                "shirt_number": fm.get("shirt") or None, "minutes_played": minutes,
            }
            mapped_players += 1

        hs, aws = int(teams[0]["score"]), int(teams[1]["score"])
        shots = team_stat(m, "ShotsOnTarget")
        full_extended = bool(fplayers)
        for side, club_id, opp_id, goals, conceded in (
            ("HOME", item["home_id"], item["away_id"], hs, aws),
            ("AWAY", item["away_id"], item["home_id"], aws, hs),
        ):
            idx = 0 if side == "HOME" else 1
            if full_extended:
                pm = club_player_metrics[club_id]
                metrics = {
                    "goal_outcome": goals * PPM,
                    "shot_on_target_non_goal": int(max(shots[idx] - goals, 0) * PPM),
                    "creation_actions": pm["official_assist"] + pm["key_pass_non_assist"],
                    "ordinary_pass_security": pm["ordinary_pass_security"],
                    "retention_net": pm["retention_net"], "allocated_recovery": pm["allocated_recovery"],
                    "progression_net": pm["progressive_pass_net"] + pm["progressive_carry_net"],
                    "turnover_avoidance": pm["turnover_avoidance"],
                    "tackle_and_interception": pm["tackle_and_interception"],
                    "block_and_clearance": pm["block_and_clearance"],
                    "own_goal_avoidance": pm["own_goal_avoidance"], "save": pm["save"],
                    "cross_claimed": pm["cross_claimed"], "concession_avoidance": -conceded * PPM,
                    "delivery_net": pm["delivery_net"], "penalty_won": pm["penalty_won"],
                    "penalty_miss_avoidance": pm["penalty_miss_avoidance"],
                    "dismissal_avoidance": pm["dismissal_avoidance"],
                    "penalty_concession_avoidance": pm["penalty_concession_avoidance"],
                    "yellow_avoidance": pm["yellow_avoidance"], "foul_avoidance": pm["foul_avoidance"],
                }
                profile = "EXTENDED"
            else:
                metrics = {"goal_outcome": goals * PPM,
                           "shot_on_target_non_goal": int(max(shots[idx] - goals, 0) * PPM)}
                profile = "BASIC_PARTIAL"
            result = "WIN" if goals > conceded else "LOSS" if goals < conceded else "DRAW"
            cells.append({
                "kind": "CLUB", "entity_id": club_id,
                "name": item["home_registered_name"] if side == "HOME" else item["away_registered_name"],
                "role": "UNKNOWN",
                "opponent_id": opp_id, "competition_id": item["competition_id"], "active_seconds": SECONDS_90,
                "metrics": metrics, "kickoff": item["kickoff"], "match_id": "fotmob:" + str(g["matchId"]),
                "profile": profile, "side": side, "result": result,
            })
        audits.append({
            "fotmob_match_id": str(g["matchId"]), "kickoff": g["matchTimeUTCDate"],
            "competition": g["leagueName"], "competition_id": item["competition_id"],
            "home": teams[0]["name"], "away": teams[1]["name"], "score": f"{hs}-{aws}",
            "home_entity_id": item["home_id"], "away_entity_id": item["away_id"],
            "club_mapping": item["club_mapping"],
            "club_mapping_scores": item["club_mapping_scores"],
            "profile": "EXTENDED" if full_extended else "BASIC_PARTIAL",
            "players_in_stats_payload": len(fplayers), "players_with_stats": active_players,
            "players_mapped": mapped_players, "players_unmapped": active_players - mapped_players,
        })

    snapshot_pools = build_snapshot_baselines(historical["rows"])
    window_pools = defaultdict(list)
    add_window_baselines(window_pools, cells)
    baseline_usage = Counter()
    for cell in cells:
        cell["observed"], sources = normalize_cell(cell, snapshot_pools, window_pools)
        cell["baseline_sources"] = sources
        baseline_usage.update(sources)

    # Result strength is initialized from the already-published club price;
    # only rating differences matter.  It then updates online match by match.
    result_ratings = {eid: math.log(max(s["price"], 1) / 1_000_000_000) * PPM
                      for eid, s in states.items() if s["kind"] == "CLUB"}
    match_groups = defaultdict(list)
    for cell in cells:
        match_groups[(cell["kickoff"], cell["match_id"])].append(cell)

    event_rows = []
    for (kickoff, match_id), group in sorted(match_groups.items()):
        club_cells = [c for c in group if c["kind"] == "CLUB"]
        home_cell = next(c for c in club_cells if c["side"] == "HOME")
        away_cell = next(c for c in club_cells if c["side"] == "AWAY")
        for c in club_cells:
            ensure_state(states, c["entity_id"], "CLUB", c["name"])
        home_rating = result_ratings.get(home_cell["entity_id"], 0.0)
        away_rating = result_ratings.get(away_cell["entity_id"], 0.0)
        hp, dp, ap = ordered_logistic(home_rating - away_rating)
        expected_utils = {
            home_cell["entity_id"]: hp + dp / 3,
            away_cell["entity_id"]: ap + dp / 3,
        }

        for cell in sorted(group, key=lambda c: (c["kind"] != "CLUB", c["entity_id"])):
            state = ensure_state(states, cell["entity_id"], cell["kind"], cell["name"], cell["role"])
            state["slow"] = decay_slow(state["slow"], state["last"], kickoff, cell["kind"])
            opp = ensure_state(states, cell["opponent_id"], "CLUB", cell["opponent_id"])
            opp_slow = decay_slow(opp["slow"], opp["last"], kickoff, "CLUB")
            personal_weight = state["reliability"] / PPM * .5
            adjustment = interaction_adjustment(opp_slow, cell["kind"])
            expected = [state["slow"][i] * personal_weight + adjustment[i] for i in range(8)]
            observed_components = sorted({idx for metric in cell["metrics"]
                                          for idx, _ in (PLAYER_TERMS if cell["kind"] == "PLAYER" else CLUB_TERMS)[metric]})
            base_weights = player_reference_weights(cell["role"]) if cell["kind"] == "PLAYER" else CLUB_WEIGHTS
            target = PPM if cell["kind"] == "PLAYER" else sum(CLUB_WEIGHTS)
            weights = renormalize(base_weights, observed_components, target)
            observed_quality = sum(cell["observed"][i] * weights[i] for i in range(8)) / PPM
            residual_quality = sum((cell["observed"][i] - expected[i]) * weights[i] for i in range(8)) / PPM
            quality = .75 * observed_quality + .25 * residual_quality
            response = math.tanh(quality / 1_500_000)
            density_multiplier = .95 + .10 * (1 - state["density"] / PPM)
            exposure = min(cell["active_seconds"] / SECONDS_90, 1.0)
            gain = PLAYER_GAINS.get(cell["role"], PLAYER_GAINS["UNKNOWN"]) if cell["kind"] == "PLAYER" else 50_185
            performance = gain * exposure * response * density_multiplier
            result_delta = 0.0
            expected_utility = None
            if cell["kind"] == "CLUB":
                expected_utility = expected_utils[cell["entity_id"]]
                actual = 1.0 if cell["result"] == "WIN" else 1 / 3 if cell["result"] == "DRAW" else 0.0
                result_delta = (actual - expected_utility) * 55_000
            match_cap = 80_000 if cell["kind"] == "PLAYER" else 60_000
            performance, result_delta, raw = radial(performance, result_delta, match_cap)
            roll_cap = 120_000 if cell["kind"] == "PLAYER" else 100_000
            rolling_cutoff = kickoff - timedelta(days=7)
            state["rolling_events"] = [
                (at, value) for at, value in state["rolling_events"] if at >= rolling_cutoff
            ]
            rolling_acc = sum(value for _, value in state["rolling_events"])
            published = rolling_delta(rolling_acc, raw, roll_cap)
            previous = state["price"]
            next_price = int(round(previous * math.exp(published / PPM)))
            if cell["kind"] == "CLUB":
                next_price = max(next_price, 500_000_000)
            state["price"] = next_price
            state["rolling_events"].append((kickoff, raw))
            alpha = exposure / 4
            for i in observed_components:
                state["slow"][i] = int(round(state["slow"][i] + alpha * (cell["observed"][i] - state["slow"][i])))
            state["effective"] += exposure
            state["reliability"] = int(round(state["effective"] / (state["effective"] + 20) * PPM))
            state["density"] = int(round((1 - math.exp(-state["effective"] / 30)) * PPM))
            state["last"] = kickoff
            event = {
                "match_id": match_id, "kickoff": kickoff.isoformat().replace("+00:00", "Z"),
                "profile": cell["profile"], "entity_id": cell["entity_id"], "kind": cell["kind"],
                "role": cell["role"], "opponent_id": cell["opponent_id"],
                "performance_quality_ppm": int(round(quality)),
                "performance_log_return_ppm": int(round(performance)),
                "result_log_return_ppm": int(round(result_delta)),
                "published_log_return_ppm": int(round(published)),
                "previous_reference_micros": previous, "next_reference_micros": next_price,
                "expected_result_utility_ppm": None if expected_utility is None else int(round(expected_utility * PPM)),
                "baseline_sources": cell["baseline_sources"],
            }
            state["events"].append(event)
            event_rows.append(event)

        # Online result rating update uses the frozen pre-match probabilities.
        actual_home = 1.0 if home_cell["result"] == "WIN" else .5 if home_cell["result"] == "DRAW" else 0.0
        innovation = (actual_home - (hp + dp / 2)) * 157_742
        result_ratings[home_cell["entity_id"]] = home_rating + innovation
        result_ratings[away_cell["entity_id"]] = away_rating - innovation

    updated_rows = []
    change_rows = []
    for eid, s in sorted(states.items()):
        change_ppm = int(round(math.log(s["price"] / s["start_price"]) * PPM)) if s["price"] != s["start_price"] else 0
        batch_change_ppm = int(round(math.log(s["price"] / s["batch_start_price"]) * PPM)) if s["price"] != s["batch_start_price"] else 0
        row = {
            "entity_id": eid, "kind": s["kind"], "display_name": latest_player_name.get(eid, s["name"]),
            "role": s["role"], "snapshot_reference_micros": s["start_price"],
            "reference_micros": s["price"], "reference": round(s["price"] / PPM, 6),
            "change_log_return_ppm": change_ppm,
            "change_pct": round((s["price"] / s["start_price"] - 1) * 100, 6),
            "matches_applied": s["base_matches"] + len(s["events"]),
            "batch_previous_reference_micros": s["batch_start_price"],
            "batch_change_log_return_ppm": batch_change_ppm,
            "batch_change_pct": round((s["price"] / s["batch_start_price"] - 1) * 100, 6),
            "batch_matches_applied": len(s["events"]),
            "effective_at": s["last"].isoformat().replace("+00:00", "Z"),
            "density_ppm": s["density"], "personal_reliability_ppm": s["reliability"],
            "slow_level_per90": s["slow"],
        }
        updated_rows.append(row)
        if s["events"]:
            change_rows.append(row)

    dump_json(OUTPUT / "updated-index.json", {
        "schema": "blackbook.index.forward-extended.v1", "as_of": AS_OF,
        "snapshot_cut": forward["snapshot_cut"], "batch_cut": SNAPSHOT_CUT,
        "base_replay_run_id": forward["base_replay_run_id"],
        "methodology": "RC3.1_EXTENDED_FORWARD_BRIDGE", "rows": updated_rows,
    })
    dump_json(OUTPUT / "match-audit.json", audits)
    cumulative_events = sorted(
        [*prior_events, *event_rows],
        key=lambda event: (event["kickoff"], event["match_id"], event["kind"], event["entity_id"]),
    )
    dump_json(OUTPUT / "movement-events.json", cumulative_events)
    dump_json(OUTPUT / "batch-movement-events.json", event_rows)

    fields = ["entity_id", "display_name", "role", "batch_previous_reference_micros", "reference_micros",
              "reference", "batch_change_log_return_ppm", "batch_change_pct",
              "batch_matches_applied", "effective_at"]
    for kind, filename in (("CLUB", "club-changes.csv"), ("PLAYER", "player-changes.csv")):
        with (OUTPUT / filename).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for row in sorted((r for r in change_rows if r["kind"] == kind),
                              key=lambda r: r["batch_change_pct"], reverse=True):
                w.writerow({k: row[k] for k in fields})
    with (OUTPUT / "unmapped-players.csv").open("w", newline="", encoding="utf-8") as f:
        fields_unmapped = ["fotmob_match_id", "kickoff", "club_id", "player_name", "fotmob_player_id", "minutes"]
        w = csv.DictWriter(f, fieldnames=fields_unmapped)
        w.writeheader(); w.writerows(unmatched_rows)

    clubs = sorted((r for r in change_rows if r["kind"] == "CLUB"), key=lambda r: r["batch_change_pct"], reverse=True)
    players = sorted((r for r in change_rows if r["kind"] == "PLAYER"), key=lambda r: r["batch_change_pct"], reverse=True)
    def md_table(rows):
        lines = ["| Entity | Old | New | Change | Matches |", "|---|---:|---:|---:|---:|"]
        for r in rows:
            lines.append(f"| {r['display_name']} | {r['batch_previous_reference_micros']/PPM:.3f} | {r['reference_micros']/PPM:.3f} | {r['batch_change_pct']:+.2f}% | {r['batch_matches_applied']} |")
        return "\n".join(lines)
    full_count = sum(a["profile"] == "EXTENDED" for a in audits)
    basic_count = sum(a["profile"] == "BASIC_PARTIAL" for a in audits)
    mapped_count = sum(a["players_mapped"] for a in audits)
    stats_count = sum(a["players_with_stats"] for a in audits)
    summary = f"""# Football index forward update — {AS_OF}

This incremental calculation starts from the published state at {SNAPSHOT_CUT} and applies only completed, in-scope competitive matches declared by the batch manifest through {AS_OF}. Earlier accepted state and movements remain cumulative. Friendlies are excluded by the frozen competition allow-list.

- Matches applied: **{len(audits)}** ({full_count} Extended; {basic_count} BASIC-partial where player-level Extended facts were unavailable)
- Extended player appearances resolved: **{mapped_count}/{stats_count}** ({mapped_count/max(stats_count,1):.1%})
- Clubs repriced: **{sum(r['kind']=='CLUB' for r in change_rows)}**
- Players repriced: **{sum(r['kind']=='PLAYER' for r in change_rows)}**
- Unmapped player appearances held (never identity-guessed): **{len(unmatched_rows)}**

## Biggest club rises

{md_table(clubs[:10])}

## Biggest club falls

{md_table(list(reversed(clubs[-10:])))}

## Biggest player rises

{md_table(players[:15])}

## Biggest player falls

{md_table(list(reversed(players[-15:])))}

## Method note

The update carries the saved reference, density, reliability, slow component state and seven-day cap ledger forward; applies RC3.1 Extended component/reference weights, calibrated response gains and contextual result probabilities; and does not replay or retune the sealed historical corpus. Existing frozen component cells supply robust baselines. Newly observed progression/delivery fields use a robust current-batch window fallback. The progressive-pass proxy is line-breaking passes plus passes into the final third because the source does not expose RC3.1 event flags directly. Player identities come from the sealed catalog and latest verified lineup assignments, with unresolved appearances held. The result model is initialized from relative saved club prices because the historical replay did not publish its separate latent result-rating state. This remains an auditable forward bridge into the canonical publication step.
"""
    (OUTPUT / "summary.md").write_text(summary, encoding="utf-8")

    receipt = {
        "schema": "blackbook.index.forward-update-receipt.v1", "snapshot_cut": SNAPSHOT_CUT,
        "as_of": AS_OF, "friendlies_included": False,
        "competition_allow_list": sorted(COMPETITION_IDS),
        "counts": {"matches": len(audits), "extended_matches": full_count,
                   "basic_partial_matches": basic_count, "player_appearances_with_stats": stats_count,
                   "player_appearances_mapped": mapped_count, "player_appearances_held": len(unmatched_rows),
                   "clubs_repriced": sum(r["kind"] == "CLUB" for r in change_rows),
                   "players_repriced": sum(r["kind"] == "PLAYER" for r in change_rows)},
        "baseline_usage": dict(baseline_usage),
        "inputs": {"historical_index_sha256": sha256(HISTORICAL_INDEX),
                   "batch_manifest_sha256": sha256(batch_manifest_path),
                   "base_forward_index_sha256": sha256(BASE_FORWARD_INDEX),
                   "base_movement_events_sha256": sha256(BASE_MOVEMENT_EVENTS),
                   "canonical_facts_sha256": sha256(CANONICAL_FACTS),
                   "source_lock_sha256": sha256(SOURCE_LOCK),
                   "rc3_1_parameters_sha256": sha256(PARAMS),
                   "match_files": {p.name: sha256(p) for p in match_files}},
        "limitations": [
            "Extended progression/delivery baselines use the current-batch window fallback.",
            "Progressive pass uses line-breaking plus final-third passes as the available provider proxy.",
            "The separate unpublished result-rating state is initialized from relative saved club prices at the batch cut.",
            "Player identity uses the sealed catalog plus latest verified lineup assignment.",
            "Unresolved player identities are held and never merged by guess.",
        ],
    }
    dump_json(OUTPUT / "receipt.json", receipt)

    manifest = {}
    for path in sorted(OUTPUT.iterdir()):
        if path.is_file() and path.name != "manifest.sha256":
            manifest[path.name] = sha256(path)
    with (OUTPUT / "manifest.sha256").open("w", encoding="utf-8") as f:
        for name, digest in manifest.items():
            f.write(f"{digest}  {name}\n")

    print(json.dumps({
        "matches": len(audits), "extended": full_count, "basic_partial": basic_count,
        "mapped_players": mapped_count, "player_stats": stats_count, "held_players": len(unmatched_rows),
        "clubs_repriced": sum(r["kind"] == "CLUB" for r in change_rows),
        "players_repriced": sum(r["kind"] == "PLAYER" for r in change_rows),
        "sealed_catalog_matches": sum(a["club_mapping"] == "SEALED_CATALOG" for a in audits),
        "top_clubs": [(r["display_name"], r["reference"], r["batch_change_pct"]) for r in clubs[:5]],
        "bottom_clubs": [(r["display_name"], r["reference"], r["batch_change_pct"]) for r in clubs[-5:]],
        "top_players": [(r["display_name"], r["reference"], r["batch_change_pct"]) for r in players[:8]],
        "bottom_players": [(r["display_name"], r["reference"], r["batch_change_pct"]) for r in players[-8:]],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
