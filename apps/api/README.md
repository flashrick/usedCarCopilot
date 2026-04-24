# API README

FastAPI backend for AI Used Car Decision Copilot.

Runtime database access uses SQLAlchemy ORM with the psycopg v3 PostgreSQL driver. Raw SQL is reserved for migration files under `apps/api/migrations/`.

## Prerequisites

- Python 3.11+
- Docker Compose
- PostgreSQL with pgvector, provided by the root `docker-compose.yml`
- Default database URL: `postgresql+psycopg://used_car:used_car@127.0.0.1:5432/used_car_copilot`

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

Generate local development embeddings for knowledge chunks:

```bash
python3 apps/api/scripts/build_embeddings.py
```

Run the API:

```bash
uvicorn app.main:app --app-dir apps/api --reload
```

Run the retrieval eval set against the running API:

```bash
python3 apps/api/scripts/run_retrieval_eval.py --markdown-output documents/eval-report.md
```

Run the recommendation eval set against the running API:

```bash
python3 apps/api/scripts/run_recommendation_eval.py --markdown-output documents/recommendation-eval-report.md
```

Run focused backend regression tests:

```bash
cd apps/api
../../.venv/bin/python -m unittest discover -s tests -v
```

## Endpoints

- `GET /health`
- `GET /listings`
- `GET /knowledge`
- `POST /retrieve`
- `POST /recommend`

`POST /retrieve` uses structured listing filters plus pgvector semantic retrieval over embedded knowledge chunks. The current embedding backend is `local-hash-embedding-v1`, a deterministic local provider intended for repeatable development before an external embedding provider is chosen.

The retrieval eval runner calls `POST /retrieve` for the 20 seed eval cases, then reports model recall, risk-theme recall, filter recall, semantic chunk coverage, and weakest cases.

`POST /recommend` reuses retrieval context, ranks candidate listings with deterministic structured signals, selects a model-diverse top list, and returns match scores, reasons, risk flags, price commentary, next steps, and evidence ids. The recommendation eval runner calls `POST /recommend` for the same 20 eval cases, then reports model recall, risk-theme recall, citation score, and weakest cases.
