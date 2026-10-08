#!/usr/bin/env python3
"""Project immutable identity and baseline inputs; never recompute a price."""
import argparse
import hashlib
import json
from pathlib import Path
from compute import build_identity_assets, load_json, dump_json, sha256

def prepare(archive, destination):
    # Verify the source files actually used, including the large facts journal.
    checks = {}
    for line in (archive / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        checks[name.removeprefix("./")] = digest
    paths = {"historical_index_sha256": "derived/materialized-calibrated-v2-final/current-index.json",
        "canonical_facts_sha256": "derived/canonical-facts.ndjson", "source_lock_sha256": "derived/source-lock.json",
        "entity_catalog_sha256": "derived/entity-catalog.json"}
    hashes = {}
    for label, name in paths.items():
        digest = sha256(archive / name)
        if digest != checks[name]:
            raise ValueError(f"Sealed source checksum mismatch: {name}")
        hashes[label] = digest
    historical = load_json(archive / paths["historical_index_sha256"])
    catalog = load_json(archive / paths["entity_catalog_sha256"])
    _, _, _, _, rosters = build_identity_assets(catalog, archive / paths["canonical_facts_sha256"], [], {})
    basis = {"schema": "blackbook.index.live-calibration-basis.v1", "sourceHashes": hashes,
        "catalog": {"entities": [{k: e[k] for k in ("entity_id", "kind", "display_name")} for e in catalog["entities"]]},
        "historicalRows": [{"entity_id": r["entity_id"], "component_state": r.get("component_state")} for r in historical["rows"]],
        "rosters": rosters}
    dump_json(destination, basis)
    return {"sha256": sha256(destination), "sourceHashes": hashes}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.archive_root.resolve(), args.output.resolve())))
