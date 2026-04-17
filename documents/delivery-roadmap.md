# Delivery Roadmap

## Delivery Strategy

Build the project as a sequence of visible portfolio milestones. Each milestone should produce something that can be explained in a README, interview, or demo.

## Phase 1: Scope And Contracts

Goal: lock what the MVP is and what data/API contracts it needs.

Deliverables:

- Product brief
- MVP specification
- Technical architecture
- Data and evaluation plan
- Initial API contract
- Initial schema draft

Exit criteria:

- The first dataset scope is chosen.
- API response shape is stable enough to start backend work.
- The repository structure is scaffolded.

## Phase 2: Data Layer

Goal: create repeatable local data loading.

Deliverables:

- Listing seed data
- Knowledge source seed data
- Ingestion script
- Chunking script
- Embedding script
- PostgreSQL and pgvector setup

Exit criteria:

- A local database can be recreated from seed data.
- A sample query can retrieve relevant chunks.

## Phase 3: Retrieval

Goal: combine hard listing filters with semantic evidence retrieval.

Deliverables:

- Structured listing search
- Semantic retrieval over knowledge chunks
- Hybrid merge and ranking
- Retrieval debug output

Exit criteria:

- At least 10 realistic queries return plausible listing candidates and relevant evidence.

## Phase 4: Recommendation API

Goal: convert retrieval context into grounded, renderable recommendations.

Deliverables:

- Citation-aware prompt
- Pydantic response models
- JSON validation
- Risk flag logic
- Price commentary logic
- `/recommend` endpoint

Exit criteria:

- Top 3 recommendations render from stable JSON.
- Important claims reference evidence ids.

## Phase 5: Frontend

Goal: build a decision workbench, not a chat UI.

Deliverables:

- Search page
- Recommendation result page
- Detail page
- Comparison page
- Evidence and risk flag components

Exit criteria:

- A user can complete a realistic end-to-end decision flow from query to comparison.

## Phase 6: Evaluation And Observability

Goal: show production-minded AI engineering.

Deliverables:

- 20 eval cases
- Eval runner
- Eval report
- Request logging
- Retrieval/generation cost tracking
- Failure examples and fixes

Exit criteria:

- Evaluation results are documented and tied to concrete improvements.

## Phase 7: Public Portfolio Packaging

Goal: make the project understandable to HR and technical interviewers.

Deliverables:

- Polished GitHub README
- Architecture diagram
- Screenshots
- 2-3 minute demo video script and recording
- LinkedIn post
- Resume bullets

Exit criteria:

- The project can be reviewed without private context.
- The demo clearly shows retrieval, citations, risk flags, evaluation, and deployment.

