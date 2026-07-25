# Page Pulse — Loom Demo Script (~5 minutes)

Record with your screen shared, backend running (`uvicorn app.main:app --reload`)
and frontend running (`npm run dev`) side by side, plus the code editor ready
to jump to specific files.

---

## 0:00 – 0:30 — Intro & what it does

> "Hey, this is my walkthrough of Page Pulse — a tool that audits any public
> URL and reports back HTTP status, response time, and on-page SEO signals
> like title, meta description, H1 count, images missing alt text, and word
> count. I'll cover the architecture, do a live demo, look at the backend
> and frontend code, walk through the tests, talk through a few design
> decisions, and end with what I'd change with another day."

## 0:30 – 1:30 — Architecture (screen: README architecture diagram)

> "At a high level: a React/Vite/TypeScript frontend calls a single FastAPI
> endpoint, `POST /audit`. That endpoint validates the URL, runs it through
> an SSRF guard that blocks localhost and private IP ranges, fetches the
> page with httpx under a timeout and redirect budget, parses the HTML with
> BeautifulSoup, and returns a JSON report.
>
> The thing I cared about most here was error handling, since that's 40% of
> the scoring rubric. Every failure mode — bad URL, timeout, DNS failure,
> SSL error, non-HTML content, oversized response, upstream 404/500 — is
> its own typed exception, and there's exactly one place, `error_handlers.py`,
> that turns any of them into a clean JSON error with a status code. So the
> route handler itself is basically two lines, and the frontend only needs
> one error-rendering code path no matter what went wrong."

## 1:30 – 3:00 — Live demo (screen: the running app)

> "Let's try it live."

- Paste a normal site (e.g. `https://github.com`) → click **Audit page** →
  narrate the skeleton loader, then the report: status pill, response time,
  title, meta description, H1 count, images missing alt, word count, and
  the bonus SEO score / canonical URL / OG title fields.
- Click **Copy JSON** → show the toast.
- Now break it on purpose:
  - Submit an invalid string like `not-a-url` → show the inline validation
    message (client-side) before it even hits the network.
  - Submit `http://localhost:8000` → show the `disallowed_target` error —
    "this is the SSRF guard rejecting a private network target."
  - Submit a URL that 404s → show the clean error alert, no stack trace.
  - (Optional) Open `/docs` in another tab and show the Swagger UI, run
    `/audit` from there directly.

> "Notice nothing ever crashes or shows a raw traceback — every failure
> becomes a specific, readable message."

## 3:00 – 3:45 — Backend code tour (screen: editor)

> "Quick tour of the backend structure."

- Open `app/services/fetcher.py` — "this is the only file that talks
  httpx directly. It streams the response in chunks so a huge or infinite
  response can't exhaust memory, and it translates every httpx exception
  into one of our domain errors."
- Open `app/services/parser.py` — "pure function, no I/O, which is why it's
  trivial to unit test in isolation — feed it a string, get back structured
  data."
- Open `app/core/security.py` — "the SSRF guard — rejects localhost by name
  and resolves the hostname to reject private/loopback/reserved IPs before
  we ever make a request."

## 3:45 – 4:15 — Frontend code tour (screen: editor)

> "On the frontend, `api/client.ts` wraps Axios and normalizes every
> possible failure — server error, timeout, network failure — into one
> `AuditRequestError` shape, so `App.tsx` just has a simple state machine:
> idle, loading, success, error. The design itself leans into the product
> name — that animated line in the header is a literal pulse/ECG waveform
> that speeds up while an audit is running."

## 4:15 – 4:35 — Tests (screen: terminal, `pytest -v`)

> "24 tests: parser happy path plus six failure/edge cases — missing title,
> missing meta description, malformed unclosed HTML, empty HTML, multiple
> H1s, images with missing vs. blank alt text — plus SSRF/validation tests
> and full API integration tests that mock the fetch layer so they run
> offline. Everything's green."

## 4:35 – 5:00 — What I'd change with another day

> "If I had another day, the first thing I'd fix is the SSRF guard — right
> now it resolves the hostname once and checks that IP, but it doesn't
> defend against DNS rebinding, where the hostname resolves safely at
> validation time and then re-resolves to a private IP at connection time.
> A production version would resolve once and pin that exact IP for the
> actual outbound connection. After that: response caching so repeated
> audits of the same URL are instant, and a headless-rendering fallback for
> JS-heavy single-page apps, since right now this only sees server-rendered
> HTML. That's Page Pulse — thanks for watching."

---

**Recording checklist before hitting record:**
- [ ] Backend running locally with `--reload`
- [ ] Frontend running locally (`npm run dev`)
- [ ] `/docs` Swagger tab pre-opened
- [ ] Terminal ready for `pytest -v`
- [ ] Editor tabs pre-opened: `fetcher.py`, `parser.py`, `security.py`, `api/client.ts`, `App.tsx`
