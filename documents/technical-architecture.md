# Technical Architecture

## Architecture Summary

The system combines a web frontend, FastAPI backend, PostgreSQL with pgvector, ingestion scripts, retrieval modules, and an LLM generation layer.

The key architectural principle is separation between:

- Structured listing search
- Unstructured knowledge retrieval
- Ranking and risk scoring
- Citation-grounded generation
- Evaluation and observability

## Planned Repository Layout

```text
usedCarCopilot/
  apps/
    web/
    api/
  packages/
    prompts/
    retrieval/
    evaluation/
  data/
    raw/
    processed/
  scripts/
    ingest_listings.py
    build_embeddings.py
    run_eval.py
  documents/
  README.md
  PLANS.md
  AGENTS.md
```

## Main Runtime Flow

1. User submits buying need from the web UI.
2. API parses the query into structured constraints and softer preferences.
3. API applies structured filters against listings.
4. Retrieval layer searches embedded knowledge chunks with semantic search.
5. Ranking layer merges listing candidates and retrieved evidence.
6. Generation layer produces JSON recommendations with citations.
7. UI renders recommendations, risks, price commentary, evidence, and comparison output.
8. Logs capture query, filters, retrieved chunks, generation cost, and errors.

## Backend Modules

### API

Owns HTTP routes, request validation, response models, and error handling.

Expected routes:

- `/parse-query`
- `/retrieve`
- `/recommend`
- `/compare`
- `/health`

### Ingestion

Owns loading raw listing and knowledge data into normalized tables.

Responsibilities:

- Validate source files
- Normalize listing fields
- Chunk knowledge documents
- Store source metadata
- Support repeatable local seed runs

### Embedding

Owns embedding document chunks and writing vectors to pgvector.

Responsibilities:

- Batch embedding calls
- Deduplicate chunks
- Record embedding model version
- Avoid re-embedding unchanged content when possible

### Retrieval

Owns structured filtering, semantic retrieval, hybrid retrieval, and debug metadata.

Responsibilities:

- Apply hard filters first
- Retrieve top-k knowledge chunks
- Merge listing and document evidence
- Return enough debug data for evaluation

### Ranking

Owns deterministic scoring before LLM generation.

Signals:

- Budget fit
- Mileage fit
- Year fit
- Brand preference
- Usage fit
- Reliability evidence
- Maintenance risk evidence
- Evidence coverage

### Generation

Owns prompt construction and JSON response validation.

Requirements:

- Never produce unsupported major claims.
- Attach evidence ids to recommendation reasons and risks.
- Return stable JSON for UI rendering.
- Fail gracefully when evidence is weak.

### Evaluation

Owns eval case execution and reporting.

Checks:

- Retrieval relevance
- Citation quality
- Groundedness
- Recommendation usefulness
- Regression over a small fixed query set

## Data Storage

PostgreSQL should store both structured records and retrieval metadata.

Core tables:

- `listings`
- `knowledge_sources`
- `document_chunks`
- `chunk_embeddings`
- `eval_cases`
- `eval_runs`
- `request_logs`

## Observability

Minimum useful logging:

- query text
- parsed filters
- listing candidate count
- retrieved chunk ids
- generation model
- token usage or cost estimate
- latency by stage
- validation errors

## Architecture Risks

- Weak data quality can make the recommendation look shallow.
- LLM output without strict schema validation can break the UI.
- Citations can become decorative unless claims are explicitly tied to evidence ids.
- A broad initial data scope can delay the end-to-end demo.

## Early Mitigations

- Keep the first dataset small and hand-checkable.
- Use Pydantic models for all API responses.
- Keep retrieval debug output visible during development.
- Treat eval cases as part of the product, not as a final polish step.

