"""Locked Nov 1, 2026: (a) ads and breaks are never trait evidence; (b) one live instance = one copy of a character."""

import json
import tempfile
import unittest
from pathlib import Path

from charmeta.live_instance import LiveInstanceError, copies_in_shot, live_instance_conflicts
from charmeta.observations import (
    ObservationValidationError,
    append_observation,
    append_observations,
    load_observations,
)
from charmeta.promote import promote
from charmeta.stills_stub import ingest_stills_meta_to_log
from charmeta.store import build_companion_from_bible, save_companion
from lineage.eligibility import (
    ad_or_break_clip_ids,
    build_trait_promotion_aired_index,
    is_ad_or_break_row,
    is_break_row,
    is_commercial_or_ad_row,
    is_show_master_row,
)
from tests.test_support import BIBLE_FIXTURE, CAST_IDS, FIXTURES

SHOW = [{"clip_id": f"test-aired-{n}", "global_no": 300 + n, "aired": True} for n in (1, 2, 3)]
BREAKS = [
    {"clip_id": "bi-cameo-1", "global_no": 311, "aired": True, "kind": "break"},
    {"clip_id": "bi-cameo-2", "global_no": 312, "aired": True, "kind": "station_break"},
    {"clip_id": "bi-cameo-3", "global_no": 313, "aired": True, "kind": "bumper"},
]
SLOT_BREAKS = [{"clip_id": f"bi-slot-{n}", "global_no": 320 + n, "aired": True} for n in (1, 2, 3)]
SLOTS = [
    {"slot_id": f"ch04-q2{n}", "occupant_global_no": 320 + n, "status": "AIRED", "kind": "break"}
    for n in (1, 2, 3)
] + [{"slot_id": "ch04-q31", "occupant_global_no": 301, "status": "AIRED", "kind": "segment"}]


def _obs(clip_id, text="brass tag"):
    return {
        "clip_id": clip_id,
        "character": "mira_smirin",
        "field": "traits.tangible",
        "extracted_text": text,
        "method": "aired_event",
    }


def _jsonl(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


class TestAdsAndBreaksAreNotTraitEvidence(unittest.TestCase):
    def test_break_kinds_are_not_show_masters(self) -> None:
        for row in BREAKS + [{"clip_id": "bi-x", "slot_kind": "ident"}, {"clip_id": "ch4-bumper-01"}]:
            self.assertTrue(is_break_row(row), row)
            self.assertTrue(is_ad_or_break_row(row), row)
            self.assertFalse(is_show_master_row(row), row)

    def test_underscored_ad_kinds_match(self) -> None:
        for kind in ("house_ad", "sales_ad", "commercial_break"):
            self.assertTrue(is_commercial_or_ad_row({"clip_id": "bi-x", "kind": kind}), kind)

    def test_show_clips_with_break_words_still_count(self) -> None:
        for clip_id in ("bi-prison-break-01", "ch4-bi-breakfast", "bi-identity-02"):
            self.assertTrue(is_show_master_row({"clip_id": clip_id}), clip_id)

    def test_aired_breaks_do_not_count_for_promotion(self) -> None:
        index = build_trait_promotion_aired_index(SHOW + BREAKS)
        self.assertTrue(all(index[r["clip_id"]] for r in SHOW))
        self.assertFalse(any(index[r["clip_id"]] for r in BREAKS))

    def test_slot_kind_marks_ad_and_break_items(self) -> None:
        slots = SLOTS + [{"occupant_global_no": 302, "kind": "ad"}]
        got = ad_or_break_clip_ids(SHOW + SLOT_BREAKS, slots)
        self.assertEqual(got, {"bi-slot-1", "bi-slot-2", "bi-slot-3", "test-aired-2"})

    def test_single_row_writer_still_rejects_break_clip_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ObservationValidationError):
                append_observation(Path(tmp) / "obs.jsonl", _obs("ch4-break-03"))

    def test_batch_writer_skips_ad_and_break_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lineage = _jsonl(root / "lineage.jsonl", SHOW + BREAKS + SLOT_BREAKS)
            slots = _jsonl(root / "slots.jsonl", SLOTS)
            path = root / "obs.jsonl"
            rows = [_obs(c) for c in ("test-aired-1", "ch4-ad-armored-showroom-cruiser", "bi-cameo-1",
                                      "bi-slot-2", "ch4-ident-07", "test-aired-2")]
            written, skipped = append_observations(path, rows, lineage_path=lineage, slots_path=slots)
            self.assertEqual([r["clip_id"] for r in written], ["test-aired-1", "test-aired-2"])
            self.assertEqual(len(skipped), 4)
            self.assertEqual([r["clip_id"] for r in load_observations(path)], ["test-aired-1", "test-aired-2"])

    def test_stills_from_an_ad_write_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "obs.jsonl"
            written = ingest_stills_meta_to_log(
                observations_path=path,
                stills_meta_path=FIXTURES / "stills-meta-sample.json",
                clip_id="ch4-ad-armored-showroom-cruiser",
                character="mira_smirin",
            )
            self.assertEqual(written, [])
            self.assertEqual(load_observations(path), [])

    def test_stills_dry_run_skips_ad_and_break_like_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "obs.jsonl"
            lineage = _jsonl(root / "lineage.jsonl", SHOW[:1])
            slots = _jsonl(root / "slots.jsonl", SLOTS)
            dry = ingest_stills_meta_to_log(
                observations_path=path,
                stills_meta_path=FIXTURES / "stills-meta-sample.json",
                clip_id="ch4-ad-armored-showroom-cruiser",
                character="mira_smirin",
                apply=False,
                lineage_path=lineage,
                slots_path=slots,
            )
            self.assertEqual(dry, [])
            self.assertEqual(load_observations(path), [])

    def test_break_observations_already_logged_never_promote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            companion_path = root / "companion.yaml"
            save_companion(companion_path, build_companion_from_bible(BIBLE_FIXTURE, CAST_IDS))
            lineage = _jsonl(root / "lineage.jsonl", SHOW[:1] + SLOT_BREAKS)
            slots = _jsonl(root / "slots.jsonl", SLOTS)
            obs = _jsonl(root / "obs.jsonl", [_obs(r["clip_id"], "silver cuff") for r in SLOT_BREAKS])
            before = companion_path.read_text(encoding="utf-8")
            unaware = promote(companion_path=companion_path, observations_path=obs, lineage_path=lineage)
            self.assertEqual(len(unaware.proposals), 1)
            report = promote(companion_path=companion_path, observations_path=obs, lineage_path=lineage,
                             slots_path=slots, apply=True)
            self.assertEqual(report.proposals, [])
            self.assertEqual(companion_path.read_text(encoding="utf-8"), before)


class TestOneLiveInstance(unittest.TestCase):
    def test_many_different_characters_on_screen_is_fine(self) -> None:
        self.assertEqual(copies_in_shot(["mira_smirin", "osmund", "tim", "bill_dbears"]), [])
        crowd = [{"character": c, "start": 0, "end": 10, "channel": 4} for c in ("mira_smirin", "osmund", "tim")]
        self.assertEqual(live_instance_conflicts(crowd), [])

    def test_two_copies_in_one_shot_conflict(self) -> None:
        self.assertEqual(copies_in_shot(["osmund", "Mira_Smirin", "mira_smirin "]), ["mira_smirin"])

    def test_crossover_overlapping_home_channel_conflicts(self) -> None:
        got = live_instance_conflicts([
            {"character": "Marla", "channel": 12, "clip_id": "ch12-a", "start": "2026-11-01T20:00:00-05:00",
             "end": "2026-11-01T20:08:00-05:00"},
            {"character": "marla", "channel": 2, "clip_id": "ch2-x", "start": "2026-11-02T01:05:00Z",
             "end": "2026-11-02T01:10:00Z"},
        ])
        self.assertEqual(len(got), 1)
        self.assertEqual((got[0]["character"], got[0]["first"]["channel"], got[0]["second"]["channel"]),
                         ("marla", 12, 2))

    def test_back_to_back_and_later_crossover_are_fine(self) -> None:
        self.assertEqual(live_instance_conflicts([
            {"character": "marla", "channel": 12, "start": 0, "end": 480},
            {"character": "marla", "channel": 2, "start": 480, "end": 600},
            {"character": "marla", "channel": 12, "start": 900, "end": 1000},
        ]), [])

    def test_bad_windows_are_refused(self) -> None:
        for item in ({"character": "tim", "start": 5, "end": 5},
                     {"character": "tim", "start": "2026-11-01T20:00:00", "end": "2026-11-01T20:05:00"},
                     {"character": "", "start": 0, "end": 1}):
            with self.assertRaises(LiveInstanceError):
                live_instance_conflicts([item])


if __name__ == "__main__":
    unittest.main()
