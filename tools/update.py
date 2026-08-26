#!/usr/bin/env python3
"""Run one complete, verified index-price update.

This command stages the provider computation and public projection, verifies the
staged publication, and only then advances the repository checkpoint and public
pointer. Raw provider payloads remain outside the repository.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from compute import load_batch_manifest
from state_io import load_checkpoint, materialize_checkpoint, write_checkpoint


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_FILES = (
    "batch-movement-events.json",
    "club-changes.csv",
    "manifest.sha256",
    "match-audit.json",
    "player-changes.csv",
    "receipt.json",
    "summary.md",
    "unmapped-players.csv",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute, project, verify, and stage one football price update.",
    )
    parser.add_argument(
        "--matches",
        type=Path,
        required=True,
        help="Directory containing the new FotMob match JSON files.",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="Restored sealed historical calibration archive root.",
    )
    parser.add_argument(
        "--batch",
        type=Path,
        required=True,
        help="Batch manifest declaring the exact window and match IDs.",
    )
    parser.add_argument(
        "--state-pointer",
        type=Path,
        default=REPO_ROOT / "state/current.json",
    )
    parser.add_argument(
        "--previous-pointer",
        type=Path,
        default=REPO_ROOT / "football/current.json",
    )
    parser.add_argument(
        "--parameters",
        type=Path,
        default=REPO_ROOT / "config/native-policy-v2.json",
    )
    parser.add_argument(
        "--band-policy",
        type=Path,
        default=REPO_ROOT / "config/publication-v3.json",
    )
    parser.add_argument("--snapshot-shard-size", type=int, default=1_000)
    parser.add_argument("--movement-shard-size", type=int, default=1_000)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and verify without changing repository files.",
    )
    return parser.parse_args()


def run(command: list[str]) -> None:
    print("+ " + shlex.join(command), flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def require_file(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"{label} is not a file: {resolved}")
    return resolved


def require_directory(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"{label} is not a directory: {resolved}")
    return resolved


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    shutil.copy2(source, temporary)
    os.replace(temporary, destination)


def commit_update(
    staged_publication: Path,
    staged_pointer: Path,
    staged_state: Path,
    staged_state_pointer: Path,
    candidate: Path,
    batch_path: Path,
    publication: str,
) -> None:
    final_publication = REPO_ROOT / "football" / publication
    final_state = REPO_ROOT / "state" / publication
    final_audit = REPO_ROOT / "updates" / publication
    if final_publication.exists():
        raise RuntimeError(f"immutable publication already exists: {final_publication}")
    if final_audit.exists():
        raise RuntimeError(f"update audit already exists: {final_audit}")
    if final_state.exists():
        raise RuntimeError(f"immutable calculator state already exists: {final_state}")

    current_state_pointer = REPO_ROOT / "state/current.json"
    current_pointer = REPO_ROOT / "football/current.json"

    with tempfile.TemporaryDirectory(prefix="index-price-backup-") as backup_name:
        backup = Path(backup_name)
        shutil.copy2(current_state_pointer, backup / "state-current.json")
        shutil.copy2(current_pointer, backup / "current.json")
        try:
            shutil.copytree(staged_publication, final_publication)
            shutil.copytree(staged_state, final_state)
            final_audit.mkdir(parents=True)
            shutil.copy2(batch_path, final_audit / "batch.json")
            for name in AUDIT_FILES:
                source = candidate / name
                if source.is_file():
                    shutil.copy2(source, final_audit / name)

            atomic_copy(staged_state_pointer, current_state_pointer)
            atomic_copy(staged_pointer, current_pointer)
        except Exception:
            atomic_copy(backup / "state-current.json", current_state_pointer)
            atomic_copy(backup / "current.json", current_pointer)
            if final_audit.exists():
                shutil.rmtree(final_audit)
            if final_publication.exists():
                shutil.rmtree(final_publication)
            if final_state.exists():
                shutil.rmtree(final_state)
            raise


def main() -> None:
    args = parse_args()
    matches = require_directory(args.matches, "match input")
    archive_root = require_directory(args.archive_root, "archive root")
    batch_path = require_file(args.batch, "batch manifest")
    state_pointer = require_file(args.state_pointer, "calculator state pointer")
    previous_pointer = require_file(args.previous_pointer, "previous pointer")
    parameters = require_file(args.parameters, "parameter package")
    band_policy = require_file(args.band_policy, "band policy")
    if not args.dry_run:
        canonical_inputs = {
            "calculator state pointer": REPO_ROOT / "state/current.json",
            "previous pointer": REPO_ROOT / "football/current.json",
        }
        supplied_inputs = {
            "calculator state pointer": state_pointer,
            "previous pointer": previous_pointer,
        }
        for label, canonical in canonical_inputs.items():
            if supplied_inputs[label] != canonical.resolve():
                raise RuntimeError(f"custom {label} is allowed only with --dry-run")
    batch = load_batch_manifest(batch_path)
    publication = batch["asOf"][:10]

    final_publication = REPO_ROOT / "football" / publication
    final_state = REPO_ROOT / "state" / publication
    final_audit = REPO_ROOT / "updates" / publication
    if final_publication.exists() or final_state.exists() or final_audit.exists():
        raise RuntimeError(f"refusing to overwrite immutable update {publication}")

    with tempfile.TemporaryDirectory(prefix="index-price-update-") as work_name:
        work = Path(work_name)
        base = work / "base"
        candidate = work / "candidate"
        verify_root = work / "verified-root"
        staged_publication = verify_root / "football" / publication
        staged_pointer = verify_root / "football/current.json"
        staged_state = verify_root / "state" / publication
        staged_state_pointer = verify_root / "state/current.json"

        base.mkdir()
        base_checkpoint = materialize_checkpoint(
            state_pointer,
            base / "current-index.json",
            base / "movement-events.json",
        )
        previous = json.loads(previous_pointer.read_text(encoding="utf-8"))
        if (base_checkpoint["as_of"] != batch["from"]
                or previous.get("asOf") != batch["from"]):
            raise RuntimeError(
                "calculator state, public pointer, and batch 'from' cut must match exactly"
            )

        run([
            sys.executable,
            str(REPO_ROOT / "tools/compute.py"),
            "--base-forward-index", str(base / "current-index.json"),
            "--base-movement-events", str(base / "movement-events.json"),
            "--archive-root", str(archive_root),
            "--input-dir", str(matches),
            "--output-dir", str(candidate),
            "--batch-manifest", str(batch_path),
            "--parameters", str(parameters),
        ])
        run([
            sys.executable,
            str(REPO_ROOT / "tools/publish.py"),
            "--forward-index", str(candidate / "updated-index.json"),
            "--movement-events", str(candidate / "movement-events.json"),
            "--source-manifest", str(candidate / "manifest.sha256"),
            "--previous-pointer", str(previous_pointer),
            "--band-policy", str(band_policy),
            "--output-dir", str(staged_publication),
            "--pointer-output", str(staged_pointer),
            "--snapshot-shard-size", str(args.snapshot_shard_size),
            "--movement-shard-size", str(args.movement_shard_size),
        ])
        write_checkpoint(
            candidate / "updated-index.json",
            candidate / "movement-events.json",
            staged_state,
            staged_state_pointer,
            args.snapshot_shard_size,
            args.movement_shard_size,
        )
        staged_forward, staged_movements = load_checkpoint(staged_state_pointer)
        if (staged_forward["as_of"] != batch["asOf"]
                or not staged_forward["rows"] or not isinstance(staged_movements, list)):
            raise RuntimeError("staged calculator checkpoint verification failed")
        run([
            "node",
            str(REPO_ROOT / "tools/verify.mjs"),
            "--root", str(verify_root),
        ])

        pointer = json.loads(staged_pointer.read_text(encoding="utf-8"))
        if pointer["publication"] != publication:
            raise RuntimeError("batch and staged publication dates differ")
        if args.dry_run:
            print(json.dumps({
                "status": "VERIFIED_DRY_RUN",
                "publication": publication,
                "asOf": pointer["asOf"],
            }, indent=2))
            return

        commit_update(
            staged_publication,
            staged_pointer,
            staged_state,
            staged_state_pointer,
            candidate,
            batch_path,
            publication,
        )
        print(json.dumps({
            "status": "PUBLISHED",
            "publication": publication,
            "asOf": pointer["asOf"],
        }, indent=2))


if __name__ == "__main__":
    main()
