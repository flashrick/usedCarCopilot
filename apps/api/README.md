# API README

FastAPI backend for AI Used Car Decision Copilot.

## Prerequisites

- Python 3.11+
- Docker Compose
- PostgreSQL with pgvector, provided by the root `docker-compose.yml`
- Default database URL: `postgresql://used_car:used_car@127.0.0.1:5432/used_car_copilot`

## Setup

From the repository root:

```bash
docker compose up -d postgres
```

Install API dependencies from `apps/api`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e apps/api
```

Apply the schema:

```bash
python3 apps/api/scripts/migrate.py
```

Load seed data:

```bash
python3 apps/api/scripts/ingest_seed.py
```

Run the API:

```bash
uvicorn app.main:app --app-dir apps/api --reload
```

## Endpoints

- `GET /health`
- `GET /listings`
- `GET /knowledge`
- `POST /retrieve`

The first retrieval implementation is intentionally non-LLM and non-embedding. It uses structured filters and model-linked knowledge so the database contract can be validated before embeddings and generation are added.
