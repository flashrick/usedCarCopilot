# AI Used Car Decision Copilot

AI Used Car Decision Copilot is a portfolio-grade AI engineering project for used car decision support. It combines structured vehicle listings with unstructured reviews, buying guides, and maintenance knowledge to produce grounded recommendations, risk flags, and comparison reports.

This repository is in the early backend implementation stage. The first implementation target is a focused MVP that demonstrates RAG, hybrid retrieval, pgvector, citation-based generation, evaluation, and production-minded API/UI packaging.

## Problem

Buying a used car is a high-risk decision. Listings are incomplete, seller descriptions can be biased, and useful information is scattered across reviews, maintenance notes, and buying guides.

The goal is not to build a generic chatbot. The goal is to build a decision support system that helps a buyer understand:

- Which listings best match their budget and usage
- What trade-offs exist between similar cars
- Which risks are visible from mileage, age, description, and known model issues
- Why the system recommends a car, with evidence attached

## MVP Scope

The MVP should support one narrow data scope first:

- 1 market or city
- 3 brands, initially Toyota, Mazda, and Honda
- A small but high-quality listing and knowledge dataset
- Natural language search plus structured filtering
- Top 3 recommendations with citations and risk flags

## Planned Stack

- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: Python, FastAPI, Pydantic, Uvicorn
- Data: PostgreSQL with pgvector
- AI: embeddings, hybrid retrieval, reranking, citation-grounded LLM generation
- Evaluation: small hand-written eval set, retrieval metrics, citation quality checks, answer consistency checks
- Deployment: Vercel for frontend, Render/Railway/Fly.io/Azure App Service for API, Supabase for Postgres

## Key Capabilities

- Parse user buying needs into structured constraints
- Filter listings by price, year, mileage, brand, and usage fit
- Retrieve supporting knowledge from reviews, model notes, maintenance guidance, and buying guides
- Rank listings using structured signals plus semantic evidence
- Generate recommendation output in a stable JSON shape
- Attach citations to claims
- Score risk factors such as high mileage, maintenance cost, accident cues, and weak usage fit
- Log requests, retrieval results, cost, and failures for debugging

## Documentation

- [Project Brief](documents/product-brief.md)
- [MVP Specification](documents/mvp-spec.md)
- [Technical Architecture](documents/technical-architecture.md)
- [Data And Evaluation Plan](documents/data-and-evaluation-plan.md)
- [Delivery Roadmap](documents/delivery-roadmap.md)
- [Retrieval Eval Report](documents/eval-report.md)
- [Recommendation Eval Report](documents/recommendation-eval-report.md)
- [Original Portfolio Plan](documents/README.md)
- [Original Build Guide](documents/used-car-rag-build-guide.md)
- [LinkedIn And HR Pack](documents/linkedin-hr-pack.md)

## Current Status

The repository now contains planning documents, seed data, and a PostgreSQL-backed FastAPI scaffold with seed ingestion, local chunk embedding generation, pgvector semantic retrieval for `/retrieve`, and deterministic citation-aware recommendations for `/recommend`.

## Backend Quickstart

The API uses SQLAlchemy ORM for runtime database access with PostgreSQL and pgvector. Raw SQL is kept in migration files.

Start PostgreSQL with pgvector:

```bash
docker compose up -d postgres
```

Install API dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e apps/api
```

Apply the schema:

```bash
python3 apps/api/scripts/migrate.py
```

Ingest seed data:

```bash
python3 apps/api/scripts/ingest_seed.py
```

Generate local development embeddings for document chunks:

```bash
python3 apps/api/scripts/build_embeddings.py
```

Optional local provider settings:

```bash
EMBEDDING_PROVIDER=local_hash
EMBEDDING_MODEL=local-hash-embedding-v1
RECOMMENDATION_PROVIDER=deterministic
RECOMMENDATION_MODEL=deterministic_ranker_with_citations
```

Optional OpenAI-backed recommendation generation:

```bash
RECOMMENDATION_PROVIDER=openai
RECOMMENDATION_MODEL=gpt-5-mini
OPENAI_API_KEY=...
```

Alternative OpenAI-compatible AI providers:

```bash
RECOMMENDATION_PROVIDER=deepseek
RECOMMENDATION_MODEL=deepseek-chat
DEEPSEEK_API_KEY=...

RECOMMENDATION_PROVIDER=qwen
RECOMMENDATION_MODEL=qwen-plus
QWEN_API_KEY=...

RECOMMENDATION_PROVIDER=kimi
RECOMMENDATION_MODEL=kimi-k2.6
KIMI_API_KEY=...
```

If external AI generation is enabled but unavailable, `/recommend` falls back to the deterministic generator and reports the fallback reason in response debug metadata.

Run the API:

```bash
uvicorn app.main:app --app-dir apps/api --reload
```

Run the first retrieval eval set against the running API:

```bash
python3 apps/api/scripts/run_retrieval_eval.py --markdown-output documents/eval-report.md
```

Run the first recommendation eval set against the running API:

```bash
python3 apps/api/scripts/run_recommendation_eval.py --markdown-output documents/recommendation-eval-report.md
```

Run focused backend regression tests:

```bash
cd apps/api
../../.venv/bin/python -m unittest discover -s tests -v
```

First endpoints:

- `GET /health`
- `GET /listings`
- `GET /knowledge`
- `POST /retrieve`, returning structured listings, model-linked knowledge, semantic chunks, and retrieval debug metadata
- `POST /recommend`, returning top recommendations, match scores, risk flags, price commentary, next steps, and cited evidence

## Frontend Quickstart

The frontend lives in `apps/web` as a Next.js decision workbench.

```bash
cd apps/web
npm install
npm run dev
```

By default the browser uses Next.js `/api/*` proxy routes that forward to `http://127.0.0.1:8000`. Override the backend target with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```
