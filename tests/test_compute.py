import json
import tempfile
import unittest
from pathlib import Path

from tools.compute import COMPETITION_IDS, load_batch_manifest, resolve_catalog_club, baseline_for, map_players_for_team


class CompetitionCoverageTests(unittest.TestCase):
    def test_uefa_main_competitions_share_qualification_identity(self):
        for name, suffix in (("Champions League", "champions-league"),
                             ("Europa League", "europa-league"),
                             ("Conference League", "conference-league")):
            with self.subTest(competition=name):
                expected = "football:uefa:" + suffix
                self.assertEqual(COMPETITION_IDS[name], expected)
                self.assertEqual(COMPETITION_IDS[name + " Qualification"], expected)

    def test_unrelated_competitions_remain_excluded(self):
        for name in ("Club Friendlies", "FA Cup", "World Cup", "Championship"):
            self.assertNotIn(name, COMPETITION_IDS)


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

    def test_manual_intake_allows_intraday_without_relaxing_utc_or_identity_checks(self):
        value = self.valid_manifest()
        value["asOf"] = "2026-08-27T12:00:00Z"
        directory, path = self.write_manifest(value)
        self.addCleanup(directory.cleanup)
        actual = load_batch_manifest(path, allow_intraday=True)
        self.assertEqual(actual["asOf"], "2026-08-27T12:00:00.000000Z")

    def test_rejects_unknown_fields(self):
        value = self.valid_manifest()
        value["note"] = "not committed input"
        directory, path = self.write_manifest(value)
        self.addCleanup(directory.cleanup)
        with self.assertRaisesRegex(ValueError, "unexpected or missing"):
            load_batch_manifest(path)


class ManualComparisonTests(unittest.TestCase):
    def test_single_match_uses_prior_population_and_never_self_calibrates(self):
        key = ('PLAYER', '*', '*', 'progressive_pass_net')
        prior = {key: (100.0, 20.0, 31.0)}
        current = {key: [(999999, 100)]}
        base, source = baseline_for({}, current, 'PLAYER', 'AM_W', 'football:fra:ligue-1', 'progressive_pass_net', prior)
        self.assertEqual(base, prior[key])
        self.assertEqual(source, 'VERIFIED_PRIOR_MATCH_WINDOW')
        with self.assertRaisesRegex(RuntimeError, 'No verified prior baseline'):
            baseline_for({}, current, 'PLAYER', 'AM_W', 'football:fra:ligue-1', 'progressive_pass_net', {})

    def test_shared_metrics_prefer_sealed_snapshot(self):
        key = ('CLUB', '*', '*', 'goal_outcome')
        base, source = baseline_for({key: [(50, 31)]}, {}, 'CLUB', 'UNKNOWN', 'football:fra:ligue-1', 'goal_outcome', {key: (999, 1, 31)})
        self.assertEqual(base[0], 50)
        self.assertEqual(source, 'SNAPSHOT_CELL')

class ClubIdentityTests(unittest.TestCase):
    def test_sporting_cp_never_resolves_to_pisa(self):
        clubs = [("pisa", "Pisa Sporting Club"),
                 ("sporting", "Sporting Clube de Portugal")]
        self.assertEqual(resolve_catalog_club("Sporting CP", clubs),
                         (1.0, "sporting", "Sporting Clube de Portugal"))

    def test_alias_prevents_plausible_wrong_fuzzy_match(self):
        clubs = [
            ("braga", "Riga FC"),
            ("correct", "Sporting Braga"),
        ]
        score, entity_id, registered = resolve_catalog_club("Braga", clubs)
        self.assertEqual((score, entity_id, registered), (1.0, "correct", "Sporting Braga"))

    def test_provider_club_debut_uses_stable_provider_identity(self):
        score, entity_id, registered = resolve_catalog_club("Elversberg", [])
        self.assertEqual(
            (score, entity_id, registered),
            (1.0, "fotmob:8232", "SV Elversberg"),
        )


class PlayerIdentityTests(unittest.TestCase):
    def test_tied_surnames_are_held_in_both_candidate_orders(self):
        player = {"id": 1180547, "name": "Souleymane Touré", "stats": []}
        candidates = [{"player_id": "a", "player_name": "I. Touré", "last_name": "Touré"},
                      {"player_id": "b", "player_name": "Z. Touré", "last_name": "Touré"}]
        for order in (candidates, list(reversed(candidates))):
            self.assertEqual(map_players_for_team([player], order, {}, {}), {})

    def test_unique_full_name_is_still_resolved(self):
        player = {"id": 1, "name": "Lamine Yamal", "stats": []}
        candidates = [{"player_id": "lamine", "player_name": "Lamine Yamal"},
                      {"player_id": "other", "player_name": "Other Player"}]
        mapped = map_players_for_team([player], candidates, {}, {})
        self.assertEqual(mapped["1"][0], "lamine")


if __name__ == "__main__":
    unittest.main()
