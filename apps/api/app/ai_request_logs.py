from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from fastapi import Request

from app.models.schemas import RecommendRequest


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def ai_request_log_path(now: datetime | None = None) -> Path:
    current = now or datetime.now().astimezone()
    return repo_root() / "logs" / f"ai-requests-{current.date().isoformat()}.log"


def resolve_client_ip(headers: Mapping[str, str], client_host: str | None) -> str:
    forwarded_for = headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    real_ip = headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip

    return client_host or "unknown"


def append_ai_request_log(entry: dict[str, Any], now: datetime | None = None) -> Path:
    path = ai_request_log_path(now)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def build_ai_request_log_entry(
    http_request: Request | None,
    payload: RecommendRequest,
    *,
    response: dict[str, Any] | None = None,
    status_code: int,
    error: Exception | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = now or datetime.now().astimezone()
    headers = dict(http_request.headers.items()) if http_request is not None else {}
    client_host = http_request.client.host if http_request is not None and http_request.client is not None else None

    entry: dict[str, Any] = {
        "timestamp": current.isoformat(),
        "event": "ai_recommendation_request",
        "method": http_request.method if http_request is not None else "UNKNOWN",
        "path": str(http_request.url.path) if http_request is not None else "/recommend",
        "client_ip": resolve_client_ip(headers, client_host),
        "user_agent": headers.get("user-agent"),
        "status_code": status_code,
        "request": payload.model_dump(mode="json"),
    }

    if response is not None:
        entry["response"] = response

    if error is not None:
        entry["error"] = {
            "type": type(error).__name__,
            "message": str(error),
        }

    return entry


def log_ai_recommendation_request(
    http_request: Request | None,
    payload: RecommendRequest,
    *,
    response: dict[str, Any] | None = None,
    status_code: int,
    error: Exception | None = None,
) -> Path:
    entry = build_ai_request_log_entry(
        http_request,
        payload,
        response=response,
        status_code=status_code,
        error=error,
    )
    return append_ai_request_log(entry)
