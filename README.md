# Page Pulse

Page Pulse audits any public URL and returns a clean report on HTTP health,
response time, and on-page SEO/structure signals — in about a second, with
no signup and no crawling delay.

Built for **Digital Heroes Training Task** ([Task A + Task B](https://digitalheroesco.com)).

![Idle state](docs/screenshots/idle-state.png)
![Audit report](docs/screenshots/audit-report.png)

---

## Table of contents

- [Project overview](#project-overview)
- [Architecture](#architecture)
- [Technology choices](#technology-choices)
- [Folder structure](#folder-structure)
- [Installation & running locally](#installation--running-locally)
- [Environment variables](#environment-variables)
- [API documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Design decisions & trade-offs](#design-decisions--trade-offs)
- [Error handling matrix](#error-handling-matrix)
- [Security](#security)
- [Future improvements](#future-improvements)

---

## Project overview

Given a URL, Page Pulse:

1. Validates the URL and rejects obviously dangerous targets (private/loopback IPs).
2. Fetches the page with a bounded timeout, capped redirects, and a capped response size.
3. Parses the HTML for title, meta description, H1 count, image alt-text
   coverage, and an approximate visible word count.
4. Returns a single JSON report — or a clean, specific error if any step fails.

The frontend is a single-page React app: paste a URL, click **Audit page**,
read the report. It never shows a stack trace, never hangs indefinitely, and
degrades gracefully on every failure mode listed in the assignment brief.

## Architecture

```
┌─────────────┐        POST /audit        ┌──────────────────┐
│   React SPA │ ─────────────────────────▶ │   FastAPI app     │
│ (Vite + TS) │ ◀───────────────────────── │                    │
└─────────────┘        JSON report /       │  routes.py         │
                        JSON error         │    │                │
                                            │    ▼                │
                                            │  auditor.py         │
                                            │  (orchestrator)      │
                                            │    │        │         │
                                            │    ▼        ▼          │
                                            │ security.py fetcher.py  │
                                            │ (SSRF guard) (httpx)     │
                                            │              │            │
                                            │              ▼             │
                                            │           parser.py         │
                                            │        (BeautifulSoup4)      │
                                            └──────────────────┘
```

**Request flow:** `AuditForm` → `api/client.ts` (Axios) → `POST /audit` →
Pydantic validates the body → `security.py` validates URL format and blocks
private/reserved network targets → `fetcher.py` performs the HTTP GET with
a timeout, retry, and redirect budget → `parser.py` extracts every signal
from the HTML → `auditor.py` assembles the `AuditReport` → FastAPI
serializes it back to JSON.

**Error flow:** every failure mode (bad input, DNS failure, timeout, SSL
error, non-HTML content, oversized response, upstream 4xx/5xx, or a truly
unexpected exception) is raised as a typed `PagePulseError` subclass. A
single set of exception handlers in `api/error_handlers.py` translates every
one of them into the same `{error_code, message}` JSON shape and the
correct HTTP status — so the frontend only ever needs one error-rendering
path, and nothing ever leaks a Python traceback to the client.

**Validation flow:** Pydantic validates the request shape first (empty/too-long
URL → `422 validation_error`), then `security.py` validates URL structure
and scheme (`422 invalid_url`), then resolves the hostname and rejects
private/loopback/reserved IPs (`422 disallowed_target`) before any request
is made to the target server.

## Technology choices

| Layer      | Choice                                   | Why |
|------------|-------------------------------------------|-----|
| Backend    | FastAPI + Python 3.12                     | Async-native, automatic OpenAPI docs, first-class Pydantic validation |
| HTTP client| httpx (async)                              | Native async support, fine-grained timeout/redirect controls, streaming reads for size-capping |
| Parsing    | BeautifulSoup4 (`html.parser`)             | Battle-tested, tolerant of malformed markup, no compiled dependencies to install |
| Frontend   | React + Vite + TypeScript                  | Fast dev loop, typed contracts shared conceptually with the Pydantic models |
| HTTP client (FE) | Axios                                | Clean interceptor-friendly error handling vs. raw fetch |
| Testing    | pytest + pytest-asyncio + FastAPI TestClient | Standard, fast, no external services required |

## Folder structure

```
page-pulse/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI app, CORS, router wiring
│   │   ├── api/
│   │   │   ├── routes.py          # /audit, /health
│   │   │   └── error_handlers.py  # centralized exception → JSON translation
│   │   ├── core/
│   │   │   ├── config.py          # env-driven Settings (pydantic-settings)
│   │   │   ├── exceptions.py      # typed domain exception hierarchy
│   │   │   ├── security.py        # URL validation + SSRF guard
│   │   │   └── logging_config.py
│   │   ├── models/
│   │   │   └── schemas.py         # AuditRequest / AuditReport / ErrorResponse
│   │   └── services/
│   │       ├── fetcher.py         # httpx fetch with retries/timeout/redirect caps
│   │       ├── parser.py          # pure HTML → signals extraction
│   │       └── auditor.py         # orchestrates fetch + parse → report
│   ├── tests/
│   │   ├── test_parser.py         # happy path + 6 failure/edge cases
│   │   ├── test_security.py       # URL validation + SSRF guard
│   │   └── test_api.py            # endpoint-level integration tests
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/client.ts          # typed Axios client, normalized errors
│   │   ├── components/            # Header, PulseLine, AuditForm, ReportCard,
│   │   │                          # SkeletonLoader, ErrorAlert, EmptyState, Toast, Footer
│   │   ├── styles/                # tokens.css (design system) + index.css
│   │   ├── types/audit.ts         # TS mirror of the backend contract
│   │   └── App.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── vercel.json
│   └── .env.example
├── docs/screenshots/
├── render.yaml
└── .gitignore
```

## Installation & running locally

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # optional - defaults already work
uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000`. Interactive docs (Swagger UI) at
`http://localhost:8000/docs`, ReDoc at `http://localhost:8000/redoc`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env        # set VITE_API_BASE_URL if not localhost:8000
npm run dev
```

The app is now at `http://localhost:5173`.

## Environment variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Free-text environment label, surfaced in logs |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed origins |
| `REQUEST_TIMEOUT_SECONDS` | `10.0` | Total time budget per fetch attempt |
| `CONNECT_TIMEOUT_SECONDS` | `5.0` | TCP/TLS connect budget |
| `MAX_REDIRECTS` | `5` | Redirect cap (protects against redirect loops) |
| `MAX_RESPONSE_BYTES` | `5000000` | Response size cap (5 MB) |
| `USER_AGENT` | `PagePulseBot/1.0 (+https://digitalheroesco.com)` | Sent on every outbound request |
| `MAX_RETRIES` | `2` | Retry attempts on timeout |
| `RETRY_BACKOFF_SECONDS` | `0.5` | Linear backoff between retries |
| `ALLOW_PRIVATE_NETWORK_TARGETS` | `false` | Set `true` only for local testing against localhost targets |
| `ALLOWED_SCHEMES` | `http,https` | Accepted URL schemes |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL of the backend API |

## API documentation

Full interactive docs are auto-generated by FastAPI at `/docs` and `/redoc`.
Summary of the contract:

### `POST /audit`

Request:

```json
{ "url": "https://example.com" }
```

Success response — `200 OK`:

```json
{
  "url": "https://example.com/",
  "status": 200,
  "response_time_ms": 128,
  "title": "Example Domain",
  "meta_description": null,
  "h1_count": 1,
  "images_without_alt": 0,
  "word_count": 28,
  "total_images": 0,
  "canonical_url": null,
  "og_title": null,
  "favicon_present": false,
  "language": null,
  "content_size_bytes": 1256,
  "seo_score": 55
}
```

The first eight fields (`url` through `word_count`) are the required
assignment contract. Everything after `total_images` is an additive bonus
field — removing them would not break the contract.

Error response — status varies by failure (`422` / `502` / `504`):

```json
{ "error_code": "timeout", "message": "The request to the target page timed out." }
```

### `GET /health`

```json
{ "status": "ok", "version": "1.0.0" }
```

## Testing

```bash
cd backend
source .venv/bin/activate
pytest -v
```

24 tests across three files:

- `test_parser.py` — happy path, missing title, missing meta description,
  malformed/unclosed HTML, empty HTML, word-count accuracy, images-without-alt
  counting (missing vs. blank `alt`), multiple `<h1>` tags.
- `test_security.py` — valid URL, empty URL, missing scheme, unsupported
  scheme, missing host, localhost blocked, loopback IP blocked.
- `test_api.py` — `/health`, full happy-path `/audit`, invalid URL, empty
  URL, timeout, DNS failure, non-HTML content, upstream 404, and a guarantee
  that unexpected exceptions never leak internal details to the client.

The HTTP fetch layer is mocked in API tests (`monkeypatch`), so the suite
runs offline and deterministically.

## Deployment

**Backend → Render** (`render.yaml` provided at the repo root):

1. Push this repo to GitHub.
2. In Render, "New +" → "Blueprint" → point at the repo. Render reads
   `render.yaml` and provisions the service automatically (free plan,
   `rootDir: backend`).
3. Update the `CORS_ORIGINS` env var to your deployed frontend URL.

**Frontend → Vercel** (`frontend/vercel.json` provided):

1. Import the repo in Vercel, set the root directory to `frontend`.
2. Set `VITE_API_BASE_URL` to your deployed Render URL.
3. Deploy — Vercel auto-detects the Vite framework preset.

**Live URLs:** _add your deployed links here before submission_
- Frontend: `https://<your-app>.vercel.app`
- Backend: `https://<your-app>.onrender.com`
- GitHub: `https://github.com/<your-username>/page-pulse`

## Design decisions & trade-offs

1. **Domain exceptions instead of inline HTTP error handling.**
   Every failure mode (`InvalidURLError`, `RequestTimeoutError`,
   `DNSResolutionError`, etc.) is a typed exception with its own
   `error_code`/`http_status`, raised deep inside services and translated
   to JSON in exactly one place (`api/error_handlers.py`). *Trade-off:* more
   files/classes up front than a few `try/except` blocks in the route
   handler, but it means adding a new failure mode never risks an
   inconsistent error shape, and the route handler itself stays a two-line
   pass-through.

2. **A best-effort SSRF guard, not a bulletproof one.**
   `core/security.py` blocks `localhost` and resolves the hostname to reject
   private/loopback/link-local/reserved IPs before fetching. *Trade-off:*
   this doesn't defend against DNS-rebinding attacks (resolving safely, then
   the target re-resolving to a private IP on the actual connection) — a
   production system would pin the resolved IP and connect to it directly.
   For a 3-4 hour assignment scope, the cheaper static-hostname + resolved-IP
   check was the right level of effort, and it's isolated in one module so
   it can be swapped for a stricter implementation later without touching
   anything else.

3. **Streaming reads with a hard size cap, over `response.text` directly.**
   `fetcher.py` reads the response in chunks via `response.aiter_bytes()`
   and aborts once `MAX_RESPONSE_BYTES` is exceeded, rather than letting
   httpx buffer an arbitrarily large body first. *Trade-off:* slightly more
   code than `httpx.get(url).text`, but it means a multi-gigabyte or
   infinite-stream response can never exhaust server memory — necessary
   for a tool whose whole job is fetching arbitrary, untrusted URLs.

## Error handling matrix

| Failure | HTTP status | `error_code` |
|---|---|---|
| Empty / malformed request body | 422 | `validation_error` |
| Invalid URL / bad scheme / missing host | 422 | `invalid_url` |
| Private/loopback/reserved network target | 422 | `disallowed_target` |
| Non-HTML content type | 422 | `unsupported_content_type` |
| Response exceeds size cap | 422 | `response_too_large` |
| DNS resolution failure | 502 | `dns_error` |
| Connection refused / reset | 502 | `connection_failed` |
| SSL certificate error | 502 | `ssl_error` |
| Too many redirects | 502 | `redirect_loop` |
| Upstream 4xx / 5xx | 502 | `upstream_http_error` |
| Timeout | 504 | `timeout` |
| Anything unanticipated | 500 | `internal_error` (message is always generic; details are logged server-side only) |

## Security

- URL scheme allow-list (`http`/`https` only).
- SSRF guard rejects localhost and private/loopback/reserved IP targets
  (see trade-offs above for its limits).
- Bounded request timeout, connect timeout, redirect count, and response
  size on every fetch.
- A descriptive `User-Agent` is always sent, and content-type is validated
  before parsing.
- Every error response is a fixed `{error_code, message}` shape — never a
  raw exception message or stack trace.
- CORS is restricted to an explicit origin allow-list via `CORS_ORIGINS`.

## Future improvements

Given another day, in priority order:

1. **DNS-rebinding-safe fetching** — resolve once, connect to the pinned IP,
   and re-validate on every redirect hop (closes the gap noted in trade-off #2).
2. **Response caching** — a short-TTL cache keyed by URL to make repeated
   audits of the same page instant and reduce load on target sites.
3. **Historical trend view** — persist past audits (per URL) so the frontend
   can show response-time and score trends over time, not just a snapshot.
4. **Headless rendering option** — an opt-in mode using a headless browser
   for JS-heavy SPAs, since the current fetch-and-parse approach only sees
   server-rendered HTML.
5. **Rate limiting** — per-IP request throttling on `/audit` before this is
   exposed publicly at scale.
