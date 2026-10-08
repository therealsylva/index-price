#!/usr/bin/env python3
"""Compute one admin-verified match without changing any repository pointer.

The caller persists the returned candidate, publishes its market contracts, and
commits the checkpoint only after all publication receipts are complete.
"""
import argparse
import contextlib
import io
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import compute
from publish import band, load_band_policy, load_previous_publication
from state_io import load_checkpoint


def calculate(request, archive_root, root, basis=None):
    match = request["match"]
    raw = match["fotmob"]
    general = raw.get("general") or {}
    if str(general.get("matchId")) != match["match_id"] or general.get("finished") is not True:
        raise ValueError("Expected a verified completed FotMob match")
    if general.get("leagueName") not in compute.COMPETITION_IDS:
        raise ValueError("Competition is outside the frozen scope (friendlies excluded)")
    if len((raw.get("header") or {}).get("teams") or []) != 2 or not (raw.get("content") or {}).get("playerStats"):
        raise ValueError("Completed score and player statistics are required")
    saved = request.get("checkpoint")
    if saved is None:
        forward, movements = load_checkpoint(root / "state/current.json")
        _, _, snapshots, _ = load_previous_publication(root / "football/current.json")
    else:
        forward, movements, snapshots = saved["forward"], saved["movements"], saved["snapshots"]
    previous_by_id = {row["entityId"]: row for row in snapshots}
    publication_time = max(datetime.now(timezone.utc), compute.dt(forward["as_of"]) + timedelta(microseconds=1))
    with tempfile.TemporaryDirectory(prefix="blackbook-match-") as temporary:
        directory = Path(temporary)
        inputs = directory / "matches"
        inputs.mkdir()
        compute.dump_json(inputs / f"{match['match_id']}.json", raw)
        compute.dump_json(directory / "forward.json", forward)
        compute.dump_json(directory / "movements.json", movements)
        compute.dump_json(directory / "batch.json", {
            "schema": "blackbook.index.update-batch.v1", "provider": "fotmob",
            "from": forward["as_of"], "asOf": publication_time.isoformat().replace("+00:00", "Z"),
            "expectedMatchIds": [match["match_id"]],
        })
        argv = sys.argv
        try:
            sys.argv = ["compute.py", "--manual-match", *( ["--basis", str(basis)] if basis else ["--archive-root", str(archive_root)] ),
                "--base-forward-index", str(directory / "forward.json"), "--base-movement-events", str(directory / "movements.json"),
                "--input-dir", str(inputs), "--output-dir", str(directory / "candidate"),
                "--batch-manifest", str(directory / "batch.json"), "--parameters", str(root / "config/native-policy-v2.json")]
            with contextlib.redirect_stdout(io.StringIO()):
                compute.main()
        finally:
            sys.argv = argv
        candidate = directory / "candidate"
        updated = json.loads((candidate / "updated-index.json").read_text())
        events = json.loads((candidate / "batch-movement-events.json").read_text())
        ledger = json.loads((candidate / "movement-events.json").read_text())
        receipt = json.loads((candidate / "receipt.json").read_text())
        audits = json.loads((candidate / "match-audit.json").read_text())
    changed = {event["entity_id"]: event for event in events}
    policy = load_band_policy(root / "config/publication-v3.json")
    rows = []
    next_snapshots = dict(previous_by_id)
    for row in updated["rows"]:
        entity_id = row["entity_id"]
        event = changed.get(entity_id)
        if event:
            lower, upper = band(row["reference_micros"], row["density_ppm"], event["profile"], row["kind"], event["published_log_return_ppm"], policy)
            projected = {"entityId": entity_id, "referenceMicros": row["reference_micros"], "lowerMicros": lower, "upperMicros": upper, "densityPpm": row["density_ppm"]}
            next_snapshots[entity_id] = projected
            rows.append({**projected, "changed": True})
        elif entity_id in match["entity_ids"]:
            if entity_id not in previous_by_id:
                raise ValueError(f"Scheduled entity has no saved normal band: {entity_id}")
            rows.append({**previous_by_id[entity_id], "changed": False})
    affected = set(match["entity_ids"]) | set(changed)
    base_references = {row["entity_id"]: str(row["reference_micros"]) for row in forward["rows"] if row["entity_id"] in affected}
    return {"rows": rows, "receipt": receipt, "audit": audits, "baseReferences": base_references,
        "checkpoint": {"forward": updated, "movements": ledger, "snapshots": list(next_snapshots.values())}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path)
    parser.add_argument("--basis", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = calculate(json.load(sys.stdin), args.archive_root.resolve() if args.archive_root else None, args.root.resolve(), args.basis.resolve() if args.basis else None)
    json.dump(result, sys.stdout, separators=(",", ":"))


if __name__ == "__main__":
    main()
