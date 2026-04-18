# PLANS.md

## Goal

Build an AI Used Car Decision Copilot that demonstrates real AI engineering ability through RAG, hybrid retrieval, structured filtering, citation-grounded generation, evaluation, and a deployable API/UI experience.

## Current Stage

Stage: Hybrid retrieval backend scaffold verified.

The repository now has planning documents, seed data, and the first FastAPI/PostgreSQL backend scaffold. The schema includes pgvector support and tables for listings, knowledge sources, document chunks, chunk embeddings, eval cases, ingestion runs, and request logs. Runtime database access uses SQLAlchemy ORM sessions and mapped records. Seed ingestion, local deterministic chunk embedding generation, and pgvector semantic retrieval have been run successfully against a local pgvector Postgres container.

## Milestones

- Completed: choose portfolio project direction.
- Completed: create startup documentation package.
- Completed: create first raw Turners listing export.
- Completed: create canonical `data/seed/` layout for listings, knowledge sources, and eval cases.
- Completed: add data preparation and validation scripts.
- Completed: validate current seed data with no coverage warnings.
- Completed: scaffold repository structure for frontend placeholder, backend, shared packages, data, and scripts.
- Completed: define initial PostgreSQL and pgvector schema from the seed data contract.
- Completed: add manual Honda Civic seed listing rows to close the listing coverage gap.
- Completed: add local deterministic embedding generation for `document_chunks` and store vectors in `chunk_embeddings`.
- In progress: build ingestion and embedding pipeline. Seed ingestion and local embedding generation are implemented and verified; external provider integration is pending.
- In progress: build retrieval API and debug output. Structured retrieval and pgvector semantic chunk retrieval are implemented and service-verified.
- Pending: build recommendation API with citation-aware JSON output.
- Pending: build decision-workbench UI.
- Pending: add evaluation workflow and reporting.
- Pending: add deployment, screenshots, demo video, and public README polish.

## Accepted Decisions

- The project is a decision support system, not a generic chatbot.
- The MVP should be narrow before it is broad.
- Initial data scope should focus on Toyota, Mazda, and Honda.
- The first market is Auckland, New Zealand.
- The first listing source is Turners data normalized into `data/seed/listings.jsonl`.
- Canonical seed data lives in `data/seed/`; raw listing export lives in `data/raw/`.
- The technical direction is FastAPI, Next.js, PostgreSQL, and pgvector.
- The first backend uses FastAPI with psycopg and PostgreSQL, not SQLite.
- Runtime database access uses SQLAlchemy ORM; raw SQL is reserved for migration files and minimal probes.
- The first retrieval endpoint started as non-LLM and non-embedding so the database contract could be validated before vector search and generation.
- The first embedding provider is a deterministic local hash embedding model so vector retrieval can be developed without external API keys. It is a development scaffold, not the final production embedding provider.
- The system must combine structured listing filters with unstructured semantic retrieval.
- Recommendation claims must be grounded with evidence citations.
- Evaluation is part of the MVP, not a later optional polish step.

## Open Questions

- Should the project use OpenAI, Anthropic, or a provider-abstracted LLM interface for the first build?
- What deployment target should be chosen for the API: Render, Railway, Fly.io, or Azure App Service?
- Should the public README and demo be written mainly in English, Chinese, or bilingual format?

## Blockers

- No current implementation blocker for local hybrid retrieval.
- External embedding and LLM provider choice remains open before production-quality recommendation generation.

## Next Skill

Recommended next skill: `test-engineer` for the first retrieval eval runner, followed by `backend-implementer` for recommendation JSON generation.

## Next Actions

1. Add a first eval runner against `/retrieve`.
2. Score whether retrieved chunks cover expected models and risk themes from `data/seed/eval_cases.json`.
3. Add recommendation API with citation-aware JSON output.
4. Choose or abstract the external embedding/LLM provider.
5. Start frontend scaffolding once the retrieval and recommendation response contracts stabilize.

## Acceptance Gates

- Before implementation: product scope, schema, and API contracts are documented.
- Before frontend work: recommendation response JSON shape is stable enough for UI wiring.
- Before public release: README, architecture diagram, screenshots, demo script, eval report, and deployment links exist.
- Before LinkedIn posting: the app can run end to end and show citations, risk flags, and comparison output.

## Change Log

- Initial plan created from `documents/README.md`, `documents/used-car-rag-build-guide.md`, and `documents/linkedin-hr-pack.md`.
- Added canonical seed data layout, data preparation script, validation script, and updated project state after data validation.
- Added manual Honda Civic seed listing rows and cleared the listing coverage warning.
- Added Postgres/pgvector backend scaffold, initial schema, seed ingestion command, and first structured retrieval API.
- Verified Docker pgvector startup, migration, seed ingestion, `/health`, and `/retrieve` against local Postgres.
- Replaced runtime psycopg query calls with SQLAlchemy ORM models, sessions, ingestion, and retrieval queries.
- Added local chunk embedding generation, content-hash based skip behavior, pgvector semantic chunk retrieval, and `/retrieve` chunk debug output.
