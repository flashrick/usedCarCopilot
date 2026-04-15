# PLANS.md

## Goal

Build an AI Used Car Decision Copilot that demonstrates real AI engineering ability through RAG, hybrid retrieval, structured filtering, citation-grounded generation, evaluation, and a deployable API/UI experience.

## Current Stage

Stage: project kickoff and documentation.

The repository is documentation-only. The core product direction, MVP scope, architecture direction, data plan, and execution roadmap have been extracted from the original planning notes.

## Milestones

- Completed: choose portfolio project direction.
- Completed: create startup documentation package.
- Pending: scaffold repository structure for frontend, backend, data, scripts, and shared packages.
- Pending: define initial schema and demo dataset format.
- Pending: build ingestion and embedding pipeline.
- Pending: build retrieval API and debug output.
- Pending: build recommendation API with citation-aware JSON output.
- Pending: build decision-workbench UI.
- Pending: add evaluation workflow and reporting.
- Pending: add deployment, screenshots, demo video, and public README polish.

## Accepted Decisions

- The project is a decision support system, not a generic chatbot.
- The MVP should be narrow before it is broad.
- Initial data scope should focus on Toyota, Mazda, and Honda.
- The technical direction is FastAPI, Next.js, PostgreSQL, and pgvector.
- The system must combine structured listing filters with unstructured semantic retrieval.
- Recommendation claims must be grounded with evidence citations.
- Evaluation is part of the MVP, not a later optional polish step.

## Open Questions

- Which city or market should the first demo dataset represent?
- Should the project use OpenAI, Anthropic, or a provider-abstracted LLM interface for the first build?
- Should the first dataset be hand-built, scraped from public sources, or mixed?
- What deployment target should be chosen for the API: Render, Railway, Fly.io, or Azure App Service?
- Should the public README and demo be written mainly in English, Chinese, or bilingual format?

## Blockers

- No code scaffold exists yet.
- No dataset or schema file exists yet.
- No API contract exists yet.
- No environment variable contract exists yet.

## Next Skill

Recommended next skill: `repo-architect`, followed by `backend-implementer`, `frontend-implementer`, and `test-engineer` once the scaffold and API contracts are clear.

## Next Actions

1. Create repository structure for `apps/web`, `apps/api`, `packages`, `data`, `scripts`, and `documents`.
2. Define the first database schema for listings, knowledge documents, chunks, embeddings, and eval cases.
3. Create `.env.example` with LLM, database, and app settings.
4. Build a small seed dataset before writing retrieval logic.
5. Implement ingestion before recommendation generation.

## Acceptance Gates

- Before implementation: product scope, schema, and API contracts are documented.
- Before frontend work: recommendation response JSON shape is stable enough for UI wiring.
- Before public release: README, architecture diagram, screenshots, demo script, eval report, and deployment links exist.
- Before LinkedIn posting: the app can run end to end and show citations, risk flags, and comparison output.

## Change Log

- Initial plan created from `documents/README.md`, `documents/used-car-rag-build-guide.md`, and `documents/linkedin-hr-pack.md`.

