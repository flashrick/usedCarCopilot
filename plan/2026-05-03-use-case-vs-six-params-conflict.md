# Task Plan: Use Case and Preferences vs Six Structured Parameters

## User Prompt

`Use case and preferences 和 6个参数如果有冲突怎么办`

## Preflight Check

- Repository root confirmed: `/home/rick/workspace/usedCarCopilot`
- Required local CLI available:
  - `rg 15.1.0`
  - `git 2.43.0`
- Writable planning directory:
  - `plan/` did not exist initially
  - created successfully in repo root
- Required repo context located:
  - frontend input composition in `apps/web/app/page.tsx`
  - retrieval filter inference in `apps/api/app/retrieval/service.py`
  - recommendation query summary in `apps/api/app/recommendation/service.py`
- External runtime services:
  - not required for this task because the user asked for behavior clarification, not execution or implementation
- Plugins / MCP / network:
  - not required for answering this question from local code
- Permissions:
  - workspace write available and sufficient

## Relevant Inputs Found

The current frontend sends:

- Free-text field: `Use case and preferences`
- Six structured parameters:
  - `budget`
  - `location`
  - `bodyType`
  - `brand`
  - `fuel`
  - `mileage`

## Code Evidence

### Frontend behavior

File: `apps/web/app/page.tsx`

- `buildPrompt()` appends the six structured values into the natural-language `query`
- `runSearch()` also sends the same values as structured payload fields

This means the backend receives the same information twice:

1. inside `query`
2. inside explicit filter fields

Key references:

- state definition: lines 55-61
- prompt merge: lines 86-105
- payload send: lines 112-123

### Backend retrieval behavior

File: `apps/api/app/retrieval/service.py`

Current precedence by field:

- `brand`
  - `request.brand` wins if provided
  - query is only used when `request.brand` is missing
  - evidence: lines 102-108
- `body_type`
  - `request.body_type` wins if provided
  - query inference only runs when `request.body_type` is missing
  - evidence: lines 110-122
- `max_price`
  - `request.max_price` wins if provided
  - query parsing only runs when `request.max_price` is missing
  - evidence: lines 124-131
- `max_mileage`
  - `request.max_mileage` wins if provided
  - query parsing only runs when `request.max_mileage` is missing
  - evidence: lines 133-140
- `fuel_type`
  - `request.fuel_type` wins if provided
  - query inference only runs when `request.fuel_type` is missing
  - evidence: lines 142-144 and 280-297
- `location`
  - only comes from `request.location`
  - there is no query-based location inference in the current retrieval path
  - evidence: line 158

### Important exceptions

File: `apps/api/app/retrieval/service.py`

- `infer_context_filters()` can still add soft preference flags from free text
- if query contains `hybrid`, it unconditionally sets `filters["fuel_type"] = "hybrid"`
- this is merged after the explicit `fuel_type` assignment through `**context_filters`
- evidence: lines 146-162 and 275-276

This creates one real conflict case:

- user selects `fuel = petrol`
- free text says `I want a hybrid`
- final `fuel_type` becomes `hybrid`

So the current system is mostly `structured filters first`, except that query-derived context can still override at least one structured field.

There is a second contradiction path:

- query negation can set `exclude_body_type`
- structured input can still set `body_type` to the same value
- this can produce self-conflicting filters such as `body_type=suv` and `exclude_body_type=suv`

So the current system can both:

- override an explicit structured field in the fuel case
- carry contradictory include/exclude constraints in the body type case

### Recommendation summary behavior

File: `apps/api/app/recommendation/service.py`

- query summary shown to the user is rebuilt from resolved `filters`
- it does not preserve contradictory raw inputs separately
- evidence: lines 991-1015

This means once the backend resolves a conflict, the response only reflects the resolved version.

## Conclusion

## Current Actual Rule

In the current codebase, the practical rule is:

- structured six parameters are intended to be hard constraints or explicit preferences
- free text is intended to fill gaps and infer softer intent
- but the implementation is not fully consistent, because query-derived context can still override explicit fuel selection

## Recommended Product Rule

If `Use case and preferences` conflicts with the six structured parameters:

1. The six structured parameters should take priority as hard user-confirmed inputs.
2. `Use case and preferences` should only supplement missing fields or add soft ranking hints.
3. Free text must not overwrite explicit structured fields.
4. If a contradiction is detected, surface it in UI or logs as a clarification warning instead of silently choosing the free-text side.

Recommended warning copy example:

`You selected petrol in filters, but your description mentions hybrid. Filters were treated as the final constraint.`

## Practical Answer To The User Question

If they conflict, the correct product behavior should be:

- trust the 6 structured parameters first
- treat `Use case and preferences` as supplementary intent
- do not let natural language overwrite explicit filter choices

But in the current implementation, there is at least one exception:

- `fuel` can be overridden by the text if the text mentions `hybrid`
- body-type filters can become internally contradictory if the text negates the same body type selected in structured filters

## Suggested Follow-up Implementation

If you want, the next change should be:

1. make all six structured fields authoritative
2. restrict `infer_context_filters()` to soft tags only
3. add explicit contradiction detection and a user-visible warning
4. add tests for each conflict type

## Suggested Commit Message

`docs(plan): record precedence rule for free-text query vs structured car filters`
