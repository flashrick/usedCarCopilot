# MVP Specification

## MVP Objective

Build a narrow but complete end-to-end version of AI Used Car Decision Copilot. It should prove the full loop: user query, structured parsing, listing filtering, knowledge retrieval, recommendation generation, citation display, risk scoring, and basic evaluation.

## Initial Data Scope

- Brands: Toyota, Mazda, Honda
- Market: one city or region to be chosen
- Dataset size: small enough to hand-check, large enough to make ranking meaningful
- Minimum target: 30-60 listings, 50-100 knowledge snippets, 20 eval cases

## Required Pages

### Search Page

Purpose: collect a buyer's need in natural language.

Required inputs:

- Free-text buying need
- Optional budget
- Optional brand preference
- Optional usage type

Required output:

- Parsed requirement summary
- Link to recommendation results

### Recommendation Page

Purpose: show the top 3 listings or model options.

Each recommendation should include:

- Listing summary
- Match score
- Top reasons
- Risk flags
- Price commentary
- Evidence preview

### Detail Page

Purpose: explain one vehicle deeply.

Required sections:

- Listing facts
- Why it matches
- Risk analysis
- Evidence snippets
- Questions to ask the seller
- Suggested inspection checklist

### Comparison Page

Purpose: compare two or three vehicles side by side.

Required dimensions:

- Price
- Year
- Mileage
- Reliability signal
- Maintenance cost signal
- Usage fit
- Risks
- Evidence strength

## Backend API Requirements

### `POST /parse-query`

Input: natural language buying need.

Output:

- budget range
- brands
- usage type
- mileage tolerance
- location
- must-have constraints
- nice-to-have preferences

### `POST /retrieve`

Input: parsed query plus optional filters.

Output:

- filtered listing candidates
- retrieved document chunks
- retrieval debug metadata

### `POST /recommend`

Input: user query and retrieval context.

Output:

- `recommended_cars`
- `why_it_matches`
- `risk_flags`
- `price_commentary`
- `evidence`
- `next_steps`

### `POST /compare`

Input: selected listing ids.

Output:

- side-by-side comparison
- final recommendation
- evidence references

## Recommendation Output Contract

The recommendation response should be JSON-first so the UI can render stable cards and tables.

```json
{
  "query_summary": {
    "budget": "string",
    "usage": "string",
    "preferences": ["string"]
  },
  "recommended_cars": [
    {
      "listing_id": "string",
      "title": "string",
      "match_score": 0,
      "why_it_matches": ["string"],
      "risk_flags": [
        {
          "label": "string",
          "severity": "low|medium|high",
          "reason": "string",
          "evidence_ids": ["string"]
        }
      ],
      "price_commentary": "string",
      "evidence_ids": ["string"],
      "next_steps": ["string"]
    }
  ],
  "evidence": [
    {
      "id": "string",
      "source_type": "listing|review|maintenance|buying_guide",
      "title": "string",
      "snippet": "string"
    }
  ]
}
```

## MVP Acceptance Criteria

- The app returns ranked recommendations for at least 10 realistic user queries.
- The app displays citations for recommendation reasons and risk flags.
- Retrieval debug output is available for development.
- Eval cases can be run with one command once code exists.
- The README can explain what works, what is limited, and what will be improved next.

