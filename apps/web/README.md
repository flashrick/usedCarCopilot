# Web README

Next.js frontend for the Used Car Copilot decision workbench.

## Setup

For the default local stack, start everything from the repository root:

```bash
docker compose up --build
```

This serves the web app on `http://127.0.0.1:3000` and connects it to the Compose API service automatically.

Optional standalone frontend setup:

From `apps/web`:

```bash
npm install
npm run dev
```

The frontend proxies browser requests through Next.js `/api/*` rewrites.

The UI supports English and Simplified Chinese. Users can switch languages from the floating toggle, and the preference is persisted in browser local storage.

Set the backend target if needed:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Admin routes are protected with Basic Auth. In Docker Compose, defaults are `admin` / `change-me` unless overridden. For standalone local runs, put the credentials in the repository root `.env`:

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
```

User-facing auth uses the API's `HttpOnly` session cookie. Local defaults come from the root `.env`:

```bash
SESSION_COOKIE_NAME=used_car_session
SESSION_TTL_DAYS=30
SESSION_COOKIE_SECURE=false
```

## Pages

- `/` user-facing two-stage car search: retrieve a shortlist first, then request AI advice for selected listings
- `/login` and `/register` for user auth
- `/history` and `/history/[id]` for saved recommendation snapshots
- `/admin` workbench with query composer, shortlist retrieval, second-stage recommendations, evidence, debug, and comparison
- `/admin/retrieve` retrieval explorer
- `/admin/compare` shortlist comparison flow backed by the same second-stage AI recommendation contract
- `/admin/reports` operational reports for data coverage, retrieval health, AI advice logs, ingestion, and embeddings
- `/admin/eval` eval report summary
- `/admin/settings` provider overview
