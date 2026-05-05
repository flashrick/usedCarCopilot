from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.reporting.service import price_band_label, summarize_ai_request_logs


class AdminReportsTests(unittest.TestCase):
    def test_price_band_label_uses_stable_admin_report_buckets(self) -> None:
        self.assertEqual(price_band_label(14999), "Under 15k")
        self.assertEqual(price_band_label(15000), "15k-25k")
        self.assertEqual(price_band_label(25000), "25k-40k")
        self.assertEqual(price_band_label(40000), "40k+")
        self.assertEqual(price_band_label(None), "Unpriced")

    def test_summarize_ai_request_logs_counts_provider_success_and_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "ai-requests-2026-05-06.log"
            rows = [
                {
                    "timestamp": "2026-05-06T09:00:00+12:00",
                    "event": "ai_recommendation_request",
                    "status_code": 200,
                    "request": {"query": "family SUV", "selected_profile_ids": ["rav4", "crv"]},
                    "response": {"debug": {"recommendation_provider": "openai"}},
                },
                {
                    "timestamp": "2026-05-06T09:05:00+12:00",
                    "event": "ai_recommendation_request",
                    "status_code": 500,
                    "request": {"query": "commuter car", "selected_profile_ids": ["camry"]},
                    "error": {"message": "provider failed"},
                },
            ]
            log_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

            summary = summarize_ai_request_logs(Path(temp_dir))

        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["success_rate"], 50.0)
        self.assertEqual(summary["providers"][0]["label"], "openai")
        self.assertEqual(summary["recent"][0]["status"], "error")
