import json
from datetime import datetime
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import spend


TRACKER = """# xAI monthly spend
Notes: $999.00 of $50 is not spend.
## October 2026
- October payments now $100 + $136 = $236.00 of $150 (157%).
- October payments still $236.00 of $150.
## November 2026
- 2026-11-02 6:55 PM CT (trundle): November payments $0.00 spent of $50 cap (0%).
## December 2026
- $999.00 of $50
"""


class SpendMonthTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.tracker = Path(temp.name) / "xai-month.md"
        self.ledger = Path(temp.name) / "ledger.jsonl"
        self.tracker.write_text(TRACKER)
        for name, path in (("SHARED_MONTH", self.tracker), ("LEDGER_PATH", self.ledger)):
            patcher = patch.object(spend, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.now = datetime(2026, 11, 2, 18, 55, tzinfo=spend.CT)

    def test_november_ignores_october_and_later_months(self):
        shared = spend.shared_month_payments(self.now)
        self.assertEqual(shared.spent, 0.0)
        self.assertEqual(shared.cap, 50.0)
        spend.check_can_spend(now=self.now)

    def test_october_still_blocks(self):
        now = datetime(2026, 10, 29, tzinfo=spend.CT)
        self.assertEqual(spend.shared_month_payments(now), spend.SharedMonth(236.0, 150.0))
        with self.assertRaises(spend.SpendLimitError):
            spend.check_can_spend(now=now)

    def test_estimate_would_exceed_cap(self):
        self.tracker.write_text("## November 2026\n- $45.00 of $50\n")
        with self.assertRaises(spend.SpendLimitError):
            spend.check_can_spend(10, now=self.now)

    def test_cap_cannot_raise_hard_stop(self):
        self.tracker.write_text("## November 2026\n- $10.00 of $500\n")
        spend.check_can_spend(40, now=self.now)
        with self.assertRaises(spend.SpendLimitError):
            spend.check_can_spend(40.01, now=self.now)

    def test_lower_cap_is_enforced(self):
        self.tracker.write_text("## November 2026\n- $10.00 of $20.50\n")
        spend.check_can_spend(10.50, now=self.now)
        with self.assertRaisesRegex(spend.SpendLimitError, r"\$20\.50"):
            spend.check_can_spend(10.51, now=self.now)

    def test_comma_amounts(self):
        self.tracker.write_text("## November 2026\n- $1,234.50 of $2,000\n")
        self.assertEqual(spend.shared_month_payments(self.now), spend.SharedMonth(1234.50, 2000.0))

    def test_last_match_and_case_insensitive_header(self):
        self.tracker.write_text(
            "Notes $999 of $50\n  ## nOvEmBeR 2026  \n"
            "- $5 of $50\n- $10 of $50; still $12.50 spent of $40\n"
            "## December 2026\n- $999 of $50\n"
        )
        self.assertEqual(spend.shared_month_payments(self.now), spend.SharedMonth(12.50, 40.0))

    def assert_fail_closed(self):
        with self.assertRaises(spend.SpendLimitError) as caught:
            spend.check_can_spend(now=self.now)
        message = str(caught.exception)
        self.assertIn("fail closed", message)
        self.assertIn("November 2026", message)
        self.assertIn(str(self.tracker), message)

    def test_missing_tracker_fails_closed(self):
        self.tracker.unlink()
        self.assert_fail_closed()

    def test_missing_month_fails_closed(self):
        self.tracker.write_text("## October 2026\n- $0 of $50\n")
        self.assert_fail_closed()

    def test_unparseable_month_fails_closed(self):
        self.tracker.write_text("Notes $0 of $50\n## November 2026\n- No total yet.\n")
        self.assert_fail_closed()

    def test_unreadable_tracker_fails_closed(self):
        self.tracker.unlink()
        self.tracker.mkdir()
        self.assert_fail_closed()

    def test_invalid_encoding_fails_closed(self):
        self.tracker.write_bytes(b"\xff")
        self.assert_fail_closed()

    def test_local_ledger_higher_than_shared(self):
        rows = [
            {"ts_ct": "2026-10-29T12:00:00-05:00", "cost_usd": 200},
            {"ts_ct": "2026-11-01T12:00:00-06:00", "cost_usd": 30},
            {"ts_ct": "2026-11-02T12:00:00-06:00", "cost_usd": 15},
        ]
        self.ledger.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
        total, note = spend.month_total_for_gate(self.now)
        self.assertEqual(total, 45.0)
        self.assertIn("local_ledger=$45.0000", note)
        with self.assertRaises(spend.SpendLimitError):
            spend.check_can_spend(10, now=self.now)

    def test_default_clock_and_explicit_path(self):
        with patch.object(spend, "_now_ct", return_value=self.now):
            self.assertEqual(spend.shared_month_payments(), spend.SharedMonth(0.0, 50.0))
            self.assertEqual(spend.month_total_for_gate()[0], 0.0)
            spend.check_can_spend()
        alternate = self.tracker.with_name("alternate.md")
        alternate.write_text("## November 2026\n- $2 of $25\n")
        self.assertEqual(spend.shared_month_payments(self.now, alternate), spend.SharedMonth(2.0, 25.0))


if __name__ == "__main__":
    unittest.main()
