#!/usr/bin/env python3
"""Shared helpers for seed sync build/diff scripts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED_DIR = ROOT / "data" / "seed"
DEFAULT_SNAPSHOT_DIR = DEFAULT_SEED_DIR / "snapshots"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}: expected each JSONL line to be an object")
        rows.append(value)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def normalize_market(value: str) -> str:
    market = value.strip().upper()
    if market not in {"US", "CN"}:
        raise SystemExit(f"Unsupported market: {value}")
    return market


def diff_by_id(previous_rows: list[dict[str, Any]], current_rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    previous_ids = {str(row[key]) for row in previous_rows}
    return [row for row in current_rows if str(row[key]) not in previous_ids]


def build_sync_parser(*, description: str, default_source: Path) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("mode", choices=["build", "diff"])
    parser.add_argument("--market", default="all", choices=["us", "cn", "all"], help="Target market for output generation.")
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--source", type=Path, default=default_source)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--report", type=Path, default=None, help="Optional diff report path.")
    return parser
