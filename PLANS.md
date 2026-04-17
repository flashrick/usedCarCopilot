# PLANS.md

## Goal

Build an AI Used Car Decision Copilot that demonstrates real AI engineering ability through RAG, hybrid retrieval, structured filtering, citation-grounded generation, evaluation, and a deployable API/UI experience.

## Current Stage

Stage: PostgreSQL backend scaffold verified.

The repository now has planning documents, seed data, and the first FastAPI/PostgreSQL backend scaffold. The schema includes pgvector support and tables for listings, knowledge sources, document chunks, chunk embeddings, eval cases, ingestion runs, and request logs. Seed ingestion and a non-LLM retrieval endpoint have been run successfully against a local pgvector Postgres container.

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
- In progress: build ingestion and embedding pipeline. Seed ingestion is implemented and verified; embedding generation is pending.
- In progress: build retrieval API and debug output. Structured retrieval is implemented and HTTP-verified; vector retrieval is pending.
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
- The first retrieval endpoint is non-LLM and non-embedding so the database contract can be validated before vector search and generation.
- The system must combine structured listing filters with unstructured semantic retrieval.
- Recommendation claims must be grounded with evidence citations.
- Evaluation is part of the MVP, not a later optional polish step.

## Open Questions

- Should the project use OpenAI, Anthropic, or a provider-abstracted LLM interface for the first build?
- What deployment target should be chosen for the API: Render, Railway, Fly.io, or Azure App Service?
- Should the public README and demo be written mainly in English, Chinese, or bilingual format?

## Blockers

- Embedding generation is not implemented yet.

## Next Skill

Recommended next skill: `repo-architect`, followed by `backend-implementer`, `frontend-implementer`, and `test-engineer` once the scaffold and API contracts are clear.

## Next Actions

1. Add embedding generation for `document_chunks`.
2. Store embeddings in `chunk_embeddings`.
3. Add pgvector semantic retrieval alongside the existing structured retrieval.
4. Add a first eval runner against `/retrieve`.
5. Start frontend scaffolding once the retrieval response contract stabilizes.

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
