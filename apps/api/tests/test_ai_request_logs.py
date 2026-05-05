from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from app.ai_request_logs import (
    ai_request_log_path,
    append_ai_request_log,
    build_ai_request_log_entry,
    resolve_client_ip,
)
from app.models.schemas import RecommendRequest


class AIRequestLogTests(unittest.TestCase):
    def test_ai_request_log_path_includes_date_in_filename(self) -> None:
        now = datetime(2026, 5, 5, 21, 30, tzinfo=timezone.utc)

        path = ai_request_log_path(now)

        self.assertEqual(path.name, "ai-requests-2026-05-05.log")

    def test_resolve_client_ip_prefers_forwarded_headers(self) -> None:
        headers = {
            "x-forwarded-for": "203.0.113.9, 10.0.0.8",
            "x-real-ip": "198.51.100.4",
        }

        resolved = resolve_client_ip(headers, "127.0.0.1")

        self.assertEqual(resolved, "203.0.113.9")

    def test_append_ai_request_log_writes_jsonl_entry(self) -> None:
        now = datetime(2026, 5, 5, 21, 30, tzinfo=timezone.utc)
        entry = {"timestamp": now.isoformat(), "status_code": 200}

        with tempfile.TemporaryDirectory() as temp_dir:
            fake_repo_root = Path(temp_dir)
            with patch("app.ai_request_logs.repo_root", return_value=fake_repo_root):
                path = append_ai_request_log(entry, now)

            written = path.read_text(encoding="utf-8").strip()
            self.assertEqual(json.loads(written), entry)

    def test_build_ai_request_log_entry_includes_key_request_metadata(self) -> None:
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/recommend",
            "headers": [
                (b"user-agent", b"pytest"),
                (b"x-forwarded-for", b"203.0.113.10"),
            ],
            "client": ("127.0.0.1", 50000),
            "scheme": "http",
            "server": ("testserver", 80),
            "query_string": b"",
        }
        request = Request(scope)
        payload = RecommendRequest(query="Need AI advice", selected_profile_ids=["camry-1", "rav4-1"])
        response = {
            "debug": {"recommendation_provider": "deepseek"},
            "recommended_profiles": [{"profile_id": "camry-1"}],
        }

        entry = build_ai_request_log_entry(
            request,
            payload,
            response=response,
            status_code=200,
            error=None,
            now=datetime(2026, 5, 5, 21, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(entry["client_ip"], "203.0.113.10")
        self.assertEqual(entry["method"], "POST")
        self.assertEqual(entry["path"], "/recommend")
        self.assertEqual(entry["request"]["selected_profile_ids"], ["camry-1", "rav4-1"])
        self.assertEqual(entry["response"]["debug"]["recommendation_provider"], "deepseek")
