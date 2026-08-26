#!/usr/bin/env python3
"""Project a computed RC3.1 state into the public price-only feed.

The publisher is intentionally separate from the provider adapter. It accepts
the detailed candidate state and cumulative sporting movement ledger, checks
their chain against the current public publication, and emits immutable public
shards plus a replacement pointer. No provider payload or model component is
copied into the public feed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PPM = 1_000_000
PUBLICATION_SCHEMA = "blackbook.index.price-publication.v1"
MANIFEST_SCHEMA = "blackbook.index.price-manifest.v1"
POINTER_SCHEMA = "blackbook.index.price-pointer.v1"
POLICY_SCHEMA = "blackbook.index.publication-band-policy.v1"
TRANSCENDENTAL_SCALE = 1_000_000_000_000
LN_2_SCALED = 693_147_180_560


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish a computed state as deterministic price-only shards.",
    )
    parser.add_argument("--forward-index", type=Path, required=True)
    parser.add_argument("--movement-events", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument(
        "--previous-pointer",
        type=Path,
        default=REPO_ROOT / "football/current.json",
    )
    parser.add_argument(
        "--band-policy",
        type=Path,
        default=REPO_ROOT / "config/publication-v3.json",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pointer-output", type=Path, required=True)
    parser.add_argument("--snapshot-shard-size", type=int, default=1_000)
    parser.add_argument("--movement-shard-size", type=int, default=1_000)
    return parser.parse_args()


def load_json(path: Path):
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def canonical_bytes(value) -> bytes:
    return (json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n").encode("utf-8")


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value) -> str:
    payload = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return digest_bytes(payload)


def exact_keys(value: dict, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} contains unexpected or missing fields")


def parse_utc(value: str, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"invalid {label}: {value!r}") from error
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be UTC")
    return parsed.astimezone(timezone.utc)


def canonical_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(
        timespec="microseconds",
    ).replace("+00:00", "Z")


def div_round_nearest_even(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("rounding denominator must be positive")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and quotient % 2):
        quotient += 1
    return sign * quotient


def fixed_exp(value: int) -> int:
    value = max(
        -20 * TRANSCENDENTAL_SCALE,
        min(20 * TRANSCENDENTAL_SCALE, value),
    )
    exponent = div_round_nearest_even(value, LN_2_SCALED)
    remainder = value - exponent * LN_2_SCALED
    total = term = TRANSCENDENTAL_SCALE
    for divisor in range(1, 29):
        term = div_round_nearest_even(
            term * remainder,
            TRANSCENDENTAL_SCALE * divisor,
        )
        total += term
    if exponent >= 0:
        return total * (1 << exponent)
    return div_round_nearest_even(total, 1 << -exponent)


def bounded_tanh_ppm(value_ppm: int, bound_ppm: int) -> int:
    ratio = div_round_nearest_even(
        value_ppm * TRANSCENDENTAL_SCALE,
        bound_ppm,
    )
    ratio = max(
        -10 * TRANSCENDENTAL_SCALE,
        min(10 * TRANSCENDENTAL_SCALE, ratio),
    )
    exponential = fixed_exp(2 * ratio)
    tanh_scaled = div_round_nearest_even(
        (exponential - TRANSCENDENTAL_SCALE) * TRANSCENDENTAL_SCALE,
        exponential + TRANSCENDENTAL_SCALE,
    )
    return div_round_nearest_even(
        tanh_scaled * bound_ppm,
        TRANSCENDENTAL_SCALE,
    )


def candidate_reference(reference: int, log_return_ppm: int) -> int:
    exponential = fixed_exp(
        log_return_ppm * (TRANSCENDENTAL_SCALE // PPM),
    )
    return max(1, div_round_nearest_even(
        reference * exponential,
        TRANSCENDENTAL_SCALE,
    ))


def load_band_policy(path: Path) -> dict:
    policy = load_json(path)
    exact_keys(policy, {
        "schema", "version", "horizonHours", "densityFloorPpm",
        "marketDiscoveryReservePpm", "densityReservePpm",
        "basicProfileReservePpm", "maximumBaseReservePpm",
        "maximumDirectionalSkewPpm", "signalScalePpm",
    }, "band policy")
    if policy["schema"] != POLICY_SCHEMA:
        raise ValueError("unsupported band policy schema")
    if set(policy["signalScalePpm"]) != {"CLUB", "PLAYER"}:
        raise ValueError("band policy must define CLUB and PLAYER signal scales")
    integer_fields = [
        "horizonHours", "densityFloorPpm", "marketDiscoveryReservePpm",
        "densityReservePpm", "basicProfileReservePpm",
        "maximumBaseReservePpm", "maximumDirectionalSkewPpm",
    ]
    if any(not isinstance(policy[field], int) or policy[field] <= 0 for field in integer_fields):
        raise ValueError("band policy contains an invalid integer parameter")
    if any(not isinstance(value, int) or value <= 0 for value in policy["signalScalePpm"].values()):
        raise ValueError("band policy contains an invalid signal scale")
    if policy["densityFloorPpm"] > PPM or policy["maximumDirectionalSkewPpm"] >= PPM:
        raise ValueError("band policy contains an out-of-range PPM value")
    return policy


def band(
    reference: int,
    density_ppm: int,
    profile: str,
    kind: str,
    signal_ppm: int,
    policy: dict,
) -> tuple[int, int]:
    if kind not in policy["signalScalePpm"]:
        raise ValueError(f"unsupported entity kind: {kind}")
    if not 0 <= density_ppm <= PPM:
        raise ValueError("invalid density")
    band_density_ppm = max(policy["densityFloorPpm"], density_ppm)
    density_reserve_ppm = div_round_nearest_even(
        policy["densityReservePpm"] * (PPM - band_density_ppm),
        PPM,
    )
    basic_reserve_ppm = (
        policy["basicProfileReservePpm"] if profile != "EXTENDED" else 0
    )
    base = min(
        policy["maximumBaseReservePpm"],
        policy["marketDiscoveryReservePpm"]
        + density_reserve_ppm
        + basic_reserve_ppm,
    )
    scale = policy["signalScalePpm"][kind]
    bounded_signal_ppm = bounded_tanh_ppm(signal_ppm, scale)
    normalized_signal_ppm = div_round_nearest_even(
        bounded_signal_ppm * PPM,
        scale,
    )
    skew_ppm = div_round_nearest_even(
        normalized_signal_ppm * policy["maximumDirectionalSkewPpm"],
        PPM,
    )
    downside = div_round_nearest_even(base * (PPM - skew_ppm), PPM)
    upside = 2 * base - downside
    lower = candidate_reference(reference, -downside)
    upper = candidate_reference(reference, upside)
    if not 0 < lower < reference < upper:
        raise ValueError("invalid price band")
    return lower, upper


def chunks(values: list[dict], size: int):
    if size < 1:
        raise ValueError("shard size must be positive")
    for offset in range(0, len(values), size):
        yield values[offset:offset + size]


def safe_relative(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or Path(relative_path).is_absolute():
        raise ValueError("unsafe publication path")
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError("unsafe publication path") from error
    return candidate


def load_previous_publication(pointer_path: Path) -> tuple[dict, dict, list[dict], list[dict]]:
    pointer_path = pointer_path.resolve()
    root = pointer_path.parent.parent.resolve()
    pointer = load_json(pointer_path)
    exact_keys(pointer, {"schema", "publication", "asOf", "manifest", "manifestSha256"}, "pointer")
    if pointer["schema"] != POINTER_SCHEMA:
        raise ValueError("unsupported previous pointer schema")
    manifest_path = safe_relative(root, pointer["manifest"])
    if digest_file(manifest_path) != pointer["manifestSha256"]:
        raise ValueError("previous manifest hash mismatch")
    manifest = load_json(manifest_path)
    if manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("asOf") != pointer["asOf"]:
        raise ValueError("invalid previous manifest")

    snapshot_rows: list[dict] = []
    movement_rows: list[dict] = []
    publication_dir = manifest_path.parent
    for declaration in manifest.get("files", []):
        name = declaration.get("name")
        if not isinstance(name, str) or Path(name).name != name:
            raise ValueError("unsafe previous shard name")
        shard_path = publication_dir / name
        if digest_file(shard_path) != declaration.get("sha256"):
            raise ValueError(f"previous shard hash mismatch: {name}")
        shard = load_json(shard_path)
        if (shard.get("schema") != PUBLICATION_SCHEMA
                or shard.get("kind") != declaration.get("kind")
                or len(shard.get("rows", [])) != declaration.get("rows")):
            raise ValueError(f"invalid previous shard: {name}")
        target = snapshot_rows if declaration["kind"] == "SNAPSHOT" else movement_rows
        target.extend(shard["rows"])
    if len(snapshot_rows) != manifest.get("snapshotRows") or len(movement_rows) != manifest.get("movementRows"):
        raise ValueError("previous publication count mismatch")
    return pointer, manifest, snapshot_rows, movement_rows


def publish(args: argparse.Namespace) -> dict:
    forward_path = args.forward_index.resolve()
    movements_path = args.movement_events.resolve()
    source_manifest = args.source_manifest.resolve()
    policy = load_band_policy(args.band_policy.resolve())
    required = [forward_path, movements_path, source_manifest, args.previous_pointer.resolve()]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing required input files: " + ", ".join(missing))

    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"output directory must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    pointer_output = args.pointer_output.resolve()

    previous_pointer, _, previous_snapshots, previous_movements = load_previous_publication(
        args.previous_pointer,
    )
    previous_as_of = parse_utc(previous_pointer["asOf"], "previous as-of")
    forward = load_json(forward_path)
    if forward.get("schema") != "blackbook.index.forward-extended.v1":
        raise ValueError("unsupported forward index schema")
    as_of_dt = parse_utc(forward.get("as_of"), "forward as-of")
    if as_of_dt <= previous_as_of:
        raise ValueError("forward as-of must be later than the current publication")
    as_of = canonical_utc(as_of_dt)
    publication = as_of[:10]
    horizon_end = canonical_utc(as_of_dt + timedelta(hours=policy["horizonHours"]))

    previous_by_id = {row["entityId"]: row for row in previous_snapshots}
    candidate_by_id = {row["entity_id"]: row for row in forward.get("rows", [])}
    if len(previous_by_id) != len(previous_snapshots) or len(candidate_by_id) != len(forward.get("rows", [])):
        raise ValueError("duplicate entity in previous or candidate state")
    if set(candidate_by_id) != set(previous_by_id):
        missing_ids = sorted(set(previous_by_id) - set(candidate_by_id))[:10]
        extra_ids = sorted(set(candidate_by_id) - set(previous_by_id))[:10]
        raise ValueError(f"entity universe changed; missing={missing_ids}, extra={extra_ids}")

    new_events_by_entity: dict[str, list[dict]] = defaultdict(list)
    cumulative_events = load_json(movements_path)
    if not isinstance(cumulative_events, list):
        raise ValueError("movement event ledger must be an array")
    historical_event_rows = []
    event_identities = set()
    for event in cumulative_events:
        kickoff = parse_utc(event.get("kickoff"), "movement kickoff")
        if kickoff >= as_of_dt:
            raise ValueError("movement event is not before the forward as-of")
        identity = (event.get("match_id"), event.get("entity_id"))
        if identity in event_identities:
            raise ValueError(f"duplicate detailed movement event: {identity}")
        event_identities.add(identity)
        if previous_as_of <= kickoff:
            entity_id = event.get("entity_id")
            if entity_id not in candidate_by_id:
                raise ValueError(f"movement references unknown entity: {entity_id}")
            new_events_by_entity[entity_id].append(event)
        else:
            historical_event_rows.append((
                event.get("entity_id"), event.get("kickoff"),
                int(event.get("previous_reference_micros")),
                int(event.get("next_reference_micros")),
                int(event.get("published_log_return_ppm")),
            ))
    historical_public_rows = [(
        row.get("entityId"), row.get("asOf"),
        int(row.get("previousReferenceMicros")),
        int(row.get("newReferenceMicros")),
        int(row.get("logReturnPpm")),
    ) for row in previous_movements]
    if sorted(historical_event_rows) != sorted(historical_public_rows):
        raise ValueError("detailed movement ledger does not reproduce the current public ledger")
    for events in new_events_by_entity.values():
        events.sort(key=lambda row: (row["kickoff"], row["match_id"], row["entity_id"]))

    snapshot_rows: list[dict] = []
    new_movement_rows: list[dict] = []
    for entity_id in sorted(candidate_by_id):
        row = candidate_by_id[entity_id]
        prior = previous_by_id[entity_id]
        events = new_events_by_entity.get(entity_id, [])
        if row["kind"] != prior["kind"]:
            raise ValueError(f"entity kind changed: {entity_id}")
        reference = int(row["reference_micros"])
        density = int(row["density_ppm"])
        version = int(prior["version"])

        if events:
            expected_reference = int(prior["referenceMicros"])
            for index, event in enumerate(events, start=1):
                if event.get("kind") != row["kind"] or event.get("entity_id") != entity_id:
                    raise ValueError(f"movement identity mismatch: {entity_id}")
                previous_reference = int(event["previous_reference_micros"])
                next_reference = int(event["next_reference_micros"])
                if previous_reference != expected_reference or next_reference < 1:
                    raise ValueError(f"broken movement chain: {entity_id}")
                event_material = {
                    "asOf": event["kickoff"],
                    "entityId": entity_id,
                    "logReturnPpm": int(event["published_log_return_ppm"]),
                    "newReferenceMicros": next_reference,
                    "previousReferenceMicros": previous_reference,
                    "version": version + index,
                }
                new_movement_rows.append({
                    **event_material,
                    "priceHash": digest_bytes(canonical_bytes(event_material)),
                })
                expected_reference = next_reference
            if expected_reference != reference:
                raise ValueError(f"candidate reference does not close movement chain: {entity_id}")
            latest = events[-1]
            candidate_event_at = parse_utc(
                row["effective_at"],
                "candidate sporting timestamp",
            )
            latest_event_at = parse_utc(
                latest["kickoff"],
                "latest movement kickoff",
            )
            if candidate_event_at != latest_event_at:
                raise ValueError(f"candidate sporting timestamp does not close movement chain: {entity_id}")
            lower, upper = band(
                reference,
                density,
                latest["profile"],
                row["kind"],
                int(latest["published_log_return_ppm"]),
                policy,
            )
            version += len(events)
            status = "PARTIAL_COVERAGE" if latest["profile"] == "BASIC_PARTIAL" else "AVAILABLE"
        else:
            if reference != int(prior["referenceMicros"]):
                raise ValueError(f"reference changed without movement: {entity_id}")
            if density != int(prior["densityPpm"]):
                raise ValueError(f"density changed without movement: {entity_id}")
            if row["effective_at"] != prior["lastSportingEventAt"]:
                raise ValueError(f"sporting timestamp changed without movement: {entity_id}")
            lower, upper = int(prior["lowerMicros"]), int(prior["upperMicros"])
            status = prior["status"]

        material = {
            "asOf": as_of,
            "bandAsOf": as_of,
            "bandHorizonEnd": horizon_end,
            "densityPpm": density,
            "displayName": row["display_name"],
            "entityId": entity_id,
            "kind": row["kind"],
            "lastSportingEventAt": row["effective_at"],
            "lowerMicros": lower,
            "referenceMicros": reference,
            "status": status,
            "upperMicros": upper,
            "version": version,
        }
        snapshot_rows.append({
            **material,
            "priceHash": digest_bytes(canonical_bytes(material)),
        })

    movement_rows = [*previous_movements, *new_movement_rows]
    movement_rows.sort(key=lambda row: (
        row["entityId"], row["version"], row["asOf"], row["priceHash"],
    ))
    movement_hashes = {row["priceHash"] for row in movement_rows}
    if len(movement_hashes) != len(movement_rows):
        raise ValueError("duplicate public movement commitment")

    files = []
    for index, shard_rows in enumerate(chunks(snapshot_rows, args.snapshot_shard_size)):
        name = f"snapshot-{index:03d}.json"
        digest = write_json(output / name, {
            "kind": "SNAPSHOT",
            "rows": shard_rows,
            "schema": PUBLICATION_SCHEMA,
        })
        files.append({"kind": "SNAPSHOT", "name": name, "rows": len(shard_rows), "sha256": digest})
    for index, shard_rows in enumerate(chunks(movement_rows, args.movement_shard_size)):
        name = f"movements-{index:03d}.json"
        digest = write_json(output / name, {
            "kind": "MOVEMENTS",
            "rows": shard_rows,
            "schema": PUBLICATION_SCHEMA,
        })
        files.append({"kind": "MOVEMENTS", "name": name, "rows": len(shard_rows), "sha256": digest})

    manifest = {
        "asOf": as_of,
        "automaticReferenceMovement": False,
        "bandHorizonEnd": horizon_end,
        "bandHorizonHours": policy["horizonHours"],
        "bandPolicyVersion": policy["version"],
        "changedEntities": len({row["entityId"] for row in movement_rows}),
        "files": files,
        "friendliesIncluded": False,
        "methodologyVersion": "RC3.1",
        "movementRows": len(movement_rows),
        "schema": MANIFEST_SCHEMA,
        "snapshotId": f"football-rc31-current-{publication}",
        "snapshotRows": len(snapshot_rows),
        "source": {"canonicalManifestSha256": digest_file(source_manifest)},
        "status": "CANONICAL_PRICE_PUBLICATION",
    }
    manifest_digest = write_json(output / "manifest.json", manifest)
    pointer = {
        "asOf": as_of,
        "manifest": f"football/{publication}/manifest.json",
        "manifestSha256": manifest_digest,
        "publication": publication,
        "schema": POINTER_SCHEMA,
    }
    write_json(pointer_output, pointer)
    return {
        "as_of": as_of,
        "publication": publication,
        "snapshot_rows": len(snapshot_rows),
        "movement_rows": len(movement_rows),
        "new_movements": len(new_movement_rows),
        "files": len(files),
    }


def main() -> None:
    result = publish(parse_args())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
