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

Admin routes are protected with Basic Auth. Put the credentials in the repository root `.env`:

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
```

## Pages

- `/` user-facing AI car search with recommendations, risk flags, and citations
- `/admin` workbench with query composer, recommendations, evidence, debug, and comparison
- `/admin/retrieve` retrieval explorer
- `/admin/compare` comparison matrix
- `/admin/eval` eval report summary
- `/admin/settings` provider overview
