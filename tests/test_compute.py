import json
import tempfile
import unittest
from pathlib import Path

from tools.compute import load_batch_manifest


class BatchManifestTests(unittest.TestCase):
    def write_manifest(self, value):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name) / "batch.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return directory, path

    def valid_manifest(self):
        return {
            "schema": "blackbook.index.update-batch.v1",
            "from": "2026-08-26T00:00:00Z",
            "asOf": "2026-08-27T00:00:00+00:00",
            "provider": "fotmob",
            "expectedMatchIds": ["123", "fotmob:456"],
        }

    def test_normalizes_timestamps_and_match_ids(self):
        directory, path = self.write_manifest(self.valid_manifest())
        self.addCleanup(directory.cleanup)
        actual = load_batch_manifest(path)
        self.assertEqual(actual["from"], "2026-08-26T00:00:00.000000Z")
        self.assertEqual(actual["asOf"], "2026-08-27T00:00:00.000000Z")
        self.assertEqual(actual["expectedMatchIds"], ["fotmob:123", "fotmob:456"])

    def test_rejects_non_utc_window(self):
        value = self.valid_manifest()
        value["asOf"] = "2026-08-27T01:00:00+01:00"
        directory, path = self.write_manifest(value)
        self.addCleanup(directory.cleanup)
        with self.assertRaisesRegex(ValueError, "UTC window"):
            load_batch_manifest(path)

    def test_rejects_duplicate_normalized_ids(self):
        value = self.valid_manifest()
        value["expectedMatchIds"] = ["123", "fotmob:123"]
        directory, path = self.write_manifest(value)
        self.addCleanup(directory.cleanup)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_batch_manifest(path)

    def test_rejects_intraday_cuts(self):
        value = self.valid_manifest()
        value["asOf"] = "2026-08-27T12:00:00Z"
        directory, path = self.write_manifest(value)
        self.addCleanup(directory.cleanup)
        with self.assertRaisesRegex(ValueError, "00:00 UTC"):
            load_batch_manifest(path)

    def test_rejects_unknown_fields(self):
        value = self.valid_manifest()
        value["note"] = "not committed input"
        directory, path = self.write_manifest(value)
        self.addCleanup(directory.cleanup)
        with self.assertRaisesRegex(ValueError, "unexpected or missing"):
            load_batch_manifest(path)


if __name__ == "__main__":
    unittest.main()
