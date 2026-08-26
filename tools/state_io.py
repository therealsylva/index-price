#!/usr/bin/env python3
"""Pack, verify, and materialize immutable calculator checkpoints."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
POINTER_SCHEMA = "blackbook.index.calculator-state-pointer.v1"
MANIFEST_SCHEMA = "blackbook.index.calculator-state-manifest.v1"
SHARD_SCHEMA = "blackbook.index.calculator-state-shard.v1"


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


def chunks(values: list[dict], size: int):
    if size < 1:
        raise ValueError("shard size must be positive")
    for offset in range(0, len(values), size):
        yield values[offset:offset + size]


def safe_relative(root: Path, relative_path: str) -> Path:
    if not isinstance(relative_path, str) or Path(relative_path).is_absolute():
        raise ValueError("unsafe calculator state path")
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError("unsafe calculator state path") from error
    return candidate


def write_checkpoint(
    forward_index_path: Path,
    movement_events_path: Path,
    output_dir: Path,
    pointer_output: Path,
    index_shard_size: int = 1_000,
    movement_shard_size: int = 1_000,
) -> dict:
    forward = load_json(forward_index_path)
    movements = load_json(movement_events_path)
    if forward.get("schema") != "blackbook.index.forward-extended.v1":
        raise ValueError("unsupported forward checkpoint schema")
    if not isinstance(forward.get("rows"), list) or not isinstance(movements, list):
        raise ValueError("invalid calculator checkpoint payload")
    entities = [row.get("entity_id") for row in forward["rows"]]
    if len(entities) != len(set(entities)):
        raise ValueError("duplicate entity in calculator checkpoint")

    output = output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"checkpoint output directory must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    metadata = {key: value for key, value in forward.items() if key != "rows"}
    as_of = metadata["as_of"]
    publication = as_of[:10]
    files = []

    sorted_rows = sorted(forward["rows"], key=lambda row: row["entity_id"])
    for index, rows in enumerate(chunks(sorted_rows, index_shard_size)):
        name = f"index-{index:03d}.json"
        digest = write_json(output / name, {
            "kind": "INDEX",
            "rows": rows,
            "schema": SHARD_SCHEMA,
        })
        files.append({"kind": "INDEX", "name": name, "rows": len(rows), "sha256": digest})

    sorted_movements = sorted(movements, key=lambda row: (
        row["kickoff"], row["match_id"], row["kind"], row["entity_id"],
    ))
    for index, rows in enumerate(chunks(sorted_movements, movement_shard_size)):
        name = f"movements-{index:03d}.json"
        digest = write_json(output / name, {
            "kind": "MOVEMENTS",
            "rows": rows,
            "schema": SHARD_SCHEMA,
        })
        files.append({"kind": "MOVEMENTS", "name": name, "rows": len(rows), "sha256": digest})

    manifest = {
        "asOf": as_of,
        "files": files,
        "indexMetadata": metadata,
        "indexRows": len(sorted_rows),
        "movementRows": len(sorted_movements),
        "schema": MANIFEST_SCHEMA,
    }
    manifest_digest = write_json(output / "manifest.json", manifest)
    pointer = {
        "asOf": as_of,
        "manifest": f"state/{publication}/manifest.json",
        "manifestSha256": manifest_digest,
        "publication": publication,
        "schema": POINTER_SCHEMA,
    }
    write_json(pointer_output.resolve(), pointer)
    return {
        "as_of": as_of,
        "publication": publication,
        "index_rows": len(sorted_rows),
        "movement_rows": len(sorted_movements),
        "files": len(files),
    }


def load_checkpoint(pointer_path: Path) -> tuple[dict, list[dict]]:
    pointer_path = pointer_path.resolve()
    root = pointer_path.parent.parent.resolve()
    pointer = load_json(pointer_path)
    exact_keys(pointer, {
        "asOf", "manifest", "manifestSha256", "publication", "schema",
    }, "calculator state pointer")
    if pointer["schema"] != POINTER_SCHEMA:
        raise ValueError("unsupported calculator state pointer")
    publication = pointer["publication"]
    if (not isinstance(publication, str)
            or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", publication)
            or not isinstance(pointer["asOf"], str)
            or pointer["asOf"][:10] != publication
            or pointer["manifest"] != f"state/{publication}/manifest.json"):
        raise ValueError("invalid calculator state pointer target")
    manifest_path = safe_relative(root, pointer["manifest"])
    if digest_file(manifest_path) != pointer["manifestSha256"]:
        raise ValueError("calculator state manifest hash mismatch")
    manifest = load_json(manifest_path)
    exact_keys(manifest, {
        "asOf", "files", "indexMetadata", "indexRows", "movementRows", "schema",
    }, "calculator state manifest")
    if manifest["schema"] != MANIFEST_SCHEMA or manifest["asOf"] != pointer["asOf"]:
        raise ValueError("invalid calculator state manifest")
    if manifest["indexMetadata"].get("as_of") != manifest["asOf"]:
        raise ValueError("calculator state metadata as-of mismatch")

    index_rows = []
    movement_rows = []
    manifest_dir = manifest_path.parent
    declared_names = set()
    for declaration in manifest["files"]:
        exact_keys(declaration, {"kind", "name", "rows", "sha256"}, "state shard declaration")
        name = declaration["name"]
        if (not isinstance(name, str) or Path(name).name != name
                or name in declared_names or declaration["kind"] not in {"INDEX", "MOVEMENTS"}):
            raise ValueError("invalid calculator state shard declaration")
        if not isinstance(declaration["rows"], int) or declaration["rows"] < 1:
            raise ValueError("invalid calculator state shard row count")
        declared_names.add(name)
        path = manifest_dir / name
        if digest_file(path) != declaration["sha256"]:
            raise ValueError(f"calculator state shard hash mismatch: {name}")
        shard = load_json(path)
        exact_keys(shard, {"kind", "rows", "schema"}, "calculator state shard")
        if (shard["schema"] != SHARD_SCHEMA or shard["kind"] != declaration["kind"]
                or not isinstance(shard["rows"], list)
                or len(shard["rows"]) != declaration["rows"]):
            raise ValueError(f"invalid calculator state shard: {name}")
        target = index_rows if shard["kind"] == "INDEX" else movement_rows
        target.extend(shard["rows"])

    if len(index_rows) != manifest["indexRows"] or len(movement_rows) != manifest["movementRows"]:
        raise ValueError("calculator state row count mismatch")
    entities = [row.get("entity_id") for row in index_rows]
    if len(entities) != len(set(entities)):
        raise ValueError("duplicate entity in calculator state")
    forward = {**manifest["indexMetadata"], "rows": index_rows}
    return forward, movement_rows


def materialize_checkpoint(
    pointer_path: Path,
    forward_output: Path,
    movement_output: Path,
) -> dict:
    forward, movements = load_checkpoint(pointer_path)
    write_json(forward_output.resolve(), forward)
    write_json(movement_output.resolve(), movements)
    return {
        "as_of": forward["as_of"],
        "index_rows": len(forward["rows"]),
        "movement_rows": len(movements),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    pack = commands.add_parser("pack")
    pack.add_argument("--forward-index", type=Path, required=True)
    pack.add_argument("--movement-events", type=Path, required=True)
    pack.add_argument("--output-dir", type=Path, required=True)
    pack.add_argument("--pointer-output", type=Path, required=True)
    pack.add_argument("--index-shard-size", type=int, default=1_000)
    pack.add_argument("--movement-shard-size", type=int, default=1_000)

    materialize = commands.add_parser("materialize")
    materialize.add_argument("--pointer", type=Path, default=REPO_ROOT / "state/current.json")
    materialize.add_argument("--forward-output", type=Path, required=True)
    materialize.add_argument("--movement-output", type=Path, required=True)

    verify = commands.add_parser("verify")
    verify.add_argument("--pointer", type=Path, default=REPO_ROOT / "state/current.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "pack":
        result = write_checkpoint(
            args.forward_index,
            args.movement_events,
            args.output_dir,
            args.pointer_output,
            args.index_shard_size,
            args.movement_shard_size,
        )
    elif args.command == "materialize":
        result = materialize_checkpoint(
            args.pointer,
            args.forward_output,
            args.movement_output,
        )
    else:
        forward, movements = load_checkpoint(args.pointer)
        result = {
            "as_of": forward["as_of"],
            "index_rows": len(forward["rows"]),
            "movement_rows": len(movements),
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
