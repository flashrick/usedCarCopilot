# Product Brief

## Product Name

AI Used Car Decision Copilot

中文名: AI 二手车决策助手

## One Sentence

An AI decision support system that combines structured used car listings with unstructured reviews, maintenance knowledge, and buying guides to recommend cars, explain trade-offs, and highlight risk with citations.

## Target Users

- First-time used car buyers
- Budget-sensitive buyers who are afraid of making a costly mistake
- Buyers comparing several similar listings
- Portfolio reviewers, recruiters, and interviewers evaluating AI engineering ability

## User Problem

Used car buyers face too much scattered and unreliable information. A listing may include price, mileage, year, and seller description, but the buyer still needs to understand reliability, maintenance cost, common model issues, and whether the price looks reasonable.

The user needs a decision aid, not another search box.

## Product Promise

For a given user need, the system should return a small ranked set of used car options with:

- Why each car fits the user
- What risks the buyer should check
- Whether the price looks reasonable
- Which evidence supports each conclusion
- What the buyer should do next before purchase

## Core Differentiator

The project should be presented as a grounded AI decision system:

- Structured data narrows the candidate listings.
- Vector retrieval brings in reviews, buying guides, and maintenance knowledge.
- Hybrid retrieval and reranking connect the user need to both hard constraints and soft evidence.
- LLM generation turns retrieved evidence into recommendations with citations.
- Evaluation checks whether retrieval and generation are useful and grounded.

## MVP User Journey

1. User enters a natural language request such as: "I need a reliable car under $12,000 for commuting and weekend trips."
2. The backend extracts budget, usage, brand preferences, mileage tolerance, and other structured signals.
3. The system filters listings and retrieves relevant knowledge snippets.
4. The system ranks candidate cars.
5. The UI presents top recommendations, risk flags, evidence snippets, and next-step advice.
6. User opens a detail view or comparison view to understand trade-offs.

## Success Criteria

- A user can submit one realistic car-buying request and receive top 3 recommendations.
- Each recommendation has a clear match reason.
- Each important claim has evidence attached.
- Each listing has visible risk flags.
- The UI makes comparison easier than reading raw listings.
- The project README explains architecture, retrieval strategy, evaluation, and limitations clearly enough for an AI Engineer interview.

## Non-Goals For MVP

- Real-time scraping from multiple marketplaces
- Fine-tuning
- Multi-agent workflows
- Image-based car damage detection
- Full market price prediction
- Support for every brand and region

