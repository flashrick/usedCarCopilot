# Web README

Next.js frontend for the Used Car Copilot decision workbench.

## Setup

From `apps/web`:

```bash
npm install
npm run dev
```

The frontend proxies browser requests through Next.js `/api/*` rewrites.

Set the backend target if needed:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Pages

- `/` workbench with query composer, recommendations, evidence, debug, and comparison
- `/retrieve` retrieval explorer
- `/compare` comparison matrix
- `/eval` eval report summary
- `/settings` provider overview
