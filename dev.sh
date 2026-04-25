#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
WEB_PORT="${WEB_PORT:-3000}"
WEB_HOST="${WEB_HOST:-0.0.0.0}"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
POSTGRES_WAIT_SECONDS="${POSTGRES_WAIT_SECONDS:-60}"

api_pid=""
web_pid=""

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

cleanup() {
  if [[ -n "$api_pid" ]] && kill -0 "$api_pid" >/dev/null 2>&1; then
    kill "$api_pid" >/dev/null 2>&1 || true
  fi

  if [[ -n "$web_pid" ]] && kill -0 "$web_pid" >/dev/null 2>&1; then
    kill "$web_pid" >/dev/null 2>&1 || true
  fi
}

load_env() {
  if [[ -f "$ROOT_DIR/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT_DIR/.env"
    set +a
  fi
}

ensure_python_env() {
  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Python virtualenv not found at $PYTHON_BIN" >&2
    echo "Create it first with: python3 -m venv .venv && .venv/bin/pip install -e apps/api" >&2
    exit 1
  fi

  if ! "$PYTHON_BIN" -c "import fastapi, psycopg, sqlalchemy, uvicorn" >/dev/null 2>&1; then
    echo "Installing API dependencies into ${PYTHON_BIN%/python}" >&2
    (cd "$ROOT_DIR" && "$PYTHON_BIN" -m pip install -e apps/api)
  fi
}

ensure_web_deps() {
  if [[ ! -d "$ROOT_DIR/apps/web/node_modules" ]]; then
    echo "Installing web dependencies" >&2
    (cd "$ROOT_DIR/apps/web" && npm install)
  fi
}

wait_for_postgres() {
  local deadline
  deadline=$((SECONDS + POSTGRES_WAIT_SECONDS))

  while (( SECONDS < deadline )); do
    if (cd "$ROOT_DIR" && docker compose exec -T postgres pg_isready -U used_car -d used_car_copilot >/dev/null 2>&1); then
      return 0
    fi
    sleep 2
  done

  echo "PostgreSQL did not become ready within ${POSTGRES_WAIT_SECONDS}s" >&2
  exit 1
}

bootstrap_backend() {
  echo "Applying migrations"
  (cd "$ROOT_DIR" && "$PYTHON_BIN" apps/api/scripts/migrate.py)

  echo "Ingesting seed data"
  (cd "$ROOT_DIR" && "$PYTHON_BIN" apps/api/scripts/ingest_seed.py)

  echo "Building local embeddings"
  (cd "$ROOT_DIR" && "$PYTHON_BIN" apps/api/scripts/build_embeddings.py)
}

start_api() {
  (
    cd "$ROOT_DIR"
    exec "$PYTHON_BIN" -m uvicorn app.main:app --app-dir apps/api --reload --host "$API_HOST" --port "$API_PORT"
  ) &
  api_pid=$!
}

start_web() {
  (
    cd "$ROOT_DIR/apps/web"
    exec npm run dev -- --hostname "$WEB_HOST" --port "$WEB_PORT"
  ) &
  web_pid=$!
}

main() {
  trap cleanup EXIT INT TERM

  require_command docker
  require_command npm
  load_env
  ensure_python_env
  ensure_web_deps

  echo "Starting PostgreSQL"
  (cd "$ROOT_DIR" && docker compose up -d postgres >/dev/null)
  wait_for_postgres
  bootstrap_backend

  echo "Starting API on http://127.0.0.1:${API_PORT}"
  start_api

  echo "Starting web on http://127.0.0.1:${WEB_PORT}"
  start_web

  echo "Development services are running. Press Ctrl-C to stop API and web."

  wait -n "$api_pid" "$web_pid"
}

main "$@"
