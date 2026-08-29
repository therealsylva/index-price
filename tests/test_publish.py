import json
import shutil
import subprocess
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

from tools.publish import (
    MANIFEST_SCHEMA,
    POINTER_SCHEMA,
    PUBLICATION_SCHEMA,
    band,
    canonical_bytes,
    digest_bytes,
    digest_file,
    load_band_policy,
    publish,
    write_json,
)
from tools.state_io import load_checkpoint


ROOT = Path(__file__).resolve().parents[1]


def load_public_rows(publication: Path, prefix: str):
    rows = []
    for path in sorted(publication.glob(f"{prefix}-*.json")):
        rows.extend(json.loads(path.read_text(encoding="utf-8"))["rows"])
    return rows


class CurrentPublicationRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_band_policy(ROOT / "config/publication-v3.json")
        cls.public_pointer = json.loads((ROOT / "football/current.json").read_text(encoding="utf-8"))
        cls.public_manifest_path = ROOT / cls.public_pointer["manifest"]
        cls.public_manifest = json.loads(cls.public_manifest_path.read_text(encoding="utf-8"))
        cls.state_pointer = json.loads((ROOT / "state/current.json").read_text(encoding="utf-8"))
        cls.state_manifest_path = ROOT / cls.state_pointer["manifest"]
        cls.state_manifest = json.loads(cls.state_manifest_path.read_text(encoding="utf-8"))
        cls.state, cls.events = load_checkpoint(ROOT / "state/current.json")
        cls.publication = cls.public_manifest_path.parent
        cls.snapshots = load_public_rows(cls.publication, "snapshot")
        cls.movements = load_public_rows(cls.publication, "movements")

    def test_checkpoint_matches_every_public_reference(self):
        public = {row["entityId"]: row for row in self.snapshots}
        self.assertEqual(len(public), len(self.state["rows"]))
        for row in self.state["rows"]:
            actual = public[row["entity_id"]]
            self.assertEqual(actual["referenceMicros"], row["reference_micros"])
            self.assertEqual(actual["densityPpm"], row["density_ppm"])
            self.assertEqual(actual["lastSportingEventAt"], row["effective_at"])

    def test_band_code_reproduces_every_changed_entity(self):
        events_by_entity = defaultdict(list)
        for event in sorted(self.events, key=lambda row: (row["kickoff"], row["match_id"], row["entity_id"])):
            events_by_entity[event["entity_id"]].append(event)
        public = {row["entityId"]: row for row in self.snapshots}
        changed = 0
        for row in self.state["rows"]:
            events = events_by_entity.get(row["entity_id"])
            if not events:
                continue
            latest = events[-1]
            expected = band(
                row["reference_micros"],
                row["density_ppm"],
                latest["profile"],
                row["kind"],
                latest["published_log_return_ppm"],
                self.policy,
            )
            actual = public[row["entity_id"]]
            self.assertEqual(expected, (actual["lowerMicros"], actual["upperMicros"]))
            changed += 1
        self.assertEqual(changed, self.public_manifest["changedEntities"])

    def test_detailed_ledger_projects_to_every_public_movement(self):
        detailed = sorted((
            row["entity_id"], row["kickoff"], row["previous_reference_micros"],
            row["next_reference_micros"], row["published_log_return_ppm"],
        ) for row in self.events)
        public = sorted((
            row["entityId"], row["asOf"], row["previousReferenceMicros"],
            row["newReferenceMicros"], row["logReturnPpm"],
        ) for row in self.movements)
        self.assertEqual(public, detailed)

    def test_active_pointers_commit_to_matching_publication_and_state(self):
        self.assertEqual(
            digest_file(self.public_manifest_path),
            self.public_pointer["manifestSha256"],
        )
        self.assertEqual(
            digest_file(self.state_manifest_path),
            self.state_pointer["manifestSha256"],
        )
        self.assertEqual(self.public_pointer["asOf"], self.state_pointer["asOf"])
        self.assertEqual(self.state_manifest["indexRows"], len(self.state["rows"]))
        self.assertEqual(self.state_manifest["movementRows"], len(self.events))


class PublisherIntegrationTests(unittest.TestCase):
    def make_previous(self, root: Path):
        publication = root / "football/2026-08-26"
        publication.mkdir(parents=True)
        material = {
            "asOf": "2026-08-26T00:00:00.000000Z",
            "bandAsOf": "2026-08-26T00:00:00.000000Z",
            "bandHorizonEnd": "2026-08-29T00:00:00.000000Z",
            "densityPpm": 600_000,
            "displayName": "Example FC",
            "entityId": "club:example",
            "kind": "CLUB",
            "lastSportingEventAt": "2026-08-25T12:00:00Z",
            "lowerMicros": 950_000_000,
            "referenceMicros": 1_000_000_000,
            "status": "AVAILABLE",
            "upperMicros": 1_050_000_000,
            "version": 7,
        }
        snapshot = {**material, "priceHash": digest_bytes(canonical_bytes(material))}
        shard_digest = write_json(publication / "snapshot-000.json", {
            "kind": "SNAPSHOT",
            "rows": [snapshot],
            "schema": PUBLICATION_SCHEMA,
        })
        manifest = {
            "asOf": material["asOf"],
            "automaticReferenceMovement": False,
            "bandHorizonEnd": material["bandHorizonEnd"],
            "bandHorizonHours": 72,
            "bandPolicyVersion": "blackbook-football-band-v3",
            "changedEntities": 0,
            "files": [{"kind": "SNAPSHOT", "name": "snapshot-000.json", "rows": 1, "sha256": shard_digest}],
            "friendliesIncluded": False,
            "methodologyVersion": "RC3.1",
            "movementRows": 0,
            "schema": MANIFEST_SCHEMA,
            "snapshotId": "football-rc31-current-2026-08-26",
            "snapshotRows": 1,
            "source": {"canonicalManifestSha256": "0" * 64},
            "status": "CANONICAL_PRICE_PUBLICATION",
        }
        manifest_digest = write_json(publication / "manifest.json", manifest)
        pointer = {
            "asOf": material["asOf"],
            "manifest": "football/2026-08-26/manifest.json",
            "manifestSha256": manifest_digest,
            "publication": "2026-08-26",
            "schema": POINTER_SCHEMA,
        }
        write_json(root / "football/current.json", pointer)

    def make_candidate(self, root: Path):
        candidate = root / "candidate"
        candidate.mkdir()
        kickoff = "2026-08-26T12:00:00Z"
        forward = {
            "as_of": "2026-08-27T00:00:00.000000Z",
            "base_replay_run_id": "test",
            "batch_cut": "2026-08-26T00:00:00.000000Z",
            "methodology": "RC3.1_EXTENDED_FORWARD_BRIDGE",
            "rows": [{
                "density_ppm": 610_000,
                "display_name": "Example FC",
                "effective_at": kickoff,
                "entity_id": "club:example",
                "kind": "CLUB",
                "reference_micros": 1_010_000_000,
            }],
            "schema": "blackbook.index.forward-extended.v1",
            "snapshot_cut": "2026-08-17T00:00:00.000000Z",
        }
        events = [{
            "baseline_sources": ["TEST"],
            "entity_id": "club:example",
            "kickoff": kickoff,
            "kind": "CLUB",
            "match_id": "fotmob:1",
            "next_reference_micros": 1_010_000_000,
            "opponent_id": "club:other",
            "performance_log_return_ppm": 9_950,
            "profile": "EXTENDED",
            "published_log_return_ppm": 9_950,
            "result_log_return_ppm": 0,
            "role": "UNKNOWN",
            "previous_reference_micros": 1_000_000_000,
        }]
        write_json(candidate / "updated-index.json", forward)
        write_json(candidate / "movement-events.json", events)
        (candidate / "manifest.sha256").write_text("test source manifest\n", encoding="utf-8")
        return candidate

    def publish_once(self, previous: Path, candidate: Path, target: Path):
        output = target / "football/2026-08-27"
        pointer = target / "football/current.json"
        result = publish(SimpleNamespace(
            forward_index=candidate / "updated-index.json",
            movement_events=candidate / "movement-events.json",
            source_manifest=candidate / "manifest.sha256",
            previous_pointer=previous / "football/current.json",
            band_policy=ROOT / "config/publication-v3.json",
            output_dir=output,
            pointer_output=pointer,
            snapshot_shard_size=1_000,
            movement_shard_size=1_000,
        ))
        return output, pointer, result

    def test_publisher_is_deterministic_and_verifiable(self):
        with tempfile.TemporaryDirectory() as name:
            temp = Path(name)
            previous = temp / "previous"
            first = temp / "first"
            second = temp / "second"
            self.make_previous(previous)
            candidate = self.make_candidate(temp)
            first_output, first_pointer, result = self.publish_once(previous, candidate, first)
            second_output, second_pointer, _ = self.publish_once(previous, candidate, second)

            self.assertEqual(result["new_movements"], 1)
            self.assertEqual(first_pointer.read_bytes(), second_pointer.read_bytes())
            first_files = sorted(path.name for path in first_output.iterdir())
            self.assertEqual(first_files, sorted(path.name for path in second_output.iterdir()))
            for name in first_files:
                self.assertEqual((first_output / name).read_bytes(), (second_output / name).read_bytes())

            movement = load_public_rows(first_output, "movements")[0]
            snapshot = load_public_rows(first_output, "snapshot")[0]
            self.assertEqual(movement["version"], 8)
            self.assertEqual(snapshot["version"], 8)
            self.assertEqual(snapshot["referenceMicros"], movement["newReferenceMicros"])

            node = shutil.which("node")
            if node:
                subprocess.run(
                    [node, str(ROOT / "tools/verify.mjs"), "--root", str(first)],
                    check=True,
                    capture_output=True,
                    text=True,
                )

    def test_publisher_onboards_new_entity_from_1000(self):
        with tempfile.TemporaryDirectory() as name:
            temp = Path(name)
            previous = temp / "previous"
            self.make_previous(previous)
            candidate = self.make_candidate(temp)

            forward_path = candidate / "updated-index.json"
            forward = json.loads(forward_path.read_text(encoding="utf-8"))
            forward["rows"].append({
                "density_ppm": 500_000,
                "display_name": "SV Elversberg",
                "effective_at": "2026-08-26T12:00:00Z",
                "entity_id": "club:fotmob:8232",
                "kind": "CLUB",
                "reference_micros": 990_000_000,
            })
            write_json(forward_path, forward)

            events_path = candidate / "movement-events.json"
            events = json.loads(events_path.read_text(encoding="utf-8"))
            events.append({
                "baseline_sources": [],
                "entity_id": "club:fotmob:8232",
                "kickoff": "2026-08-26T12:00:00Z",
                "kind": "CLUB",
                "match_id": "fotmob:2",
                "next_reference_micros": 990_000_000,
                "opponent_id": "club:example",
                "performance_log_return_ppm": -10_050,
                "profile": "BASIC_PARTIAL",
                "published_log_return_ppm": -10_050,
                "result_log_return_ppm": 0,
                "role": "UNKNOWN",
                "previous_reference_micros": 1_000_000_000,
            })
            write_json(events_path, events)

            output, _, result = self.publish_once(
                previous,
                candidate,
                temp / "published",
            )
            snapshots = {row["entityId"]: row for row in load_public_rows(output, "snapshot")}
            movements = {
                row["entityId"]: row for row in load_public_rows(output, "movements")
            }

            self.assertEqual(result["snapshot_rows"], 2)
            self.assertEqual(result["new_movements"], 2)
            self.assertEqual(snapshots["club:fotmob:8232"]["version"], 1)
            self.assertEqual(snapshots["club:fotmob:8232"]["referenceMicros"], 990_000_000)
            self.assertEqual(movements["club:fotmob:8232"]["previousReferenceMicros"], 1_000_000_000)
            self.assertEqual(movements["club:fotmob:8232"]["version"], 1)

    def test_publisher_rejects_new_entity_with_nonstandard_start(self):
        with tempfile.TemporaryDirectory() as name:
            temp = Path(name)
            previous = temp / "previous"
            self.make_previous(previous)
            candidate = self.make_candidate(temp)

            forward_path = candidate / "updated-index.json"
            forward = json.loads(forward_path.read_text(encoding="utf-8"))
            forward["rows"].append({
                "density_ppm": 500_000,
                "display_name": "New Club",
                "effective_at": "2026-08-26T12:00:00Z",
                "entity_id": "club:provider:new",
                "kind": "CLUB",
                "reference_micros": 990_000_000,
            })
            write_json(forward_path, forward)

            events_path = candidate / "movement-events.json"
            events = json.loads(events_path.read_text(encoding="utf-8"))
            events.append({
                "baseline_sources": [],
                "entity_id": "club:provider:new",
                "kickoff": "2026-08-26T12:00:00Z",
                "kind": "CLUB",
                "match_id": "fotmob:2",
                "next_reference_micros": 990_000_000,
                "opponent_id": "club:example",
                "performance_log_return_ppm": -10_050,
                "profile": "BASIC_PARTIAL",
                "published_log_return_ppm": -10_050,
                "result_log_return_ppm": 0,
                "role": "UNKNOWN",
                "previous_reference_micros": 900_000_000,
            })
            write_json(events_path, events)

            with self.assertRaisesRegex(ValueError, "does not debut from 1,000"):
                self.publish_once(previous, candidate, temp / "published")


if __name__ == "__main__":
    unittest.main()
