# QAssist

Ask questions, get answers grounded in your own documents — with citations you can check, and an agent that decides for itself when it needs to search.

QAssist is a Retrieval-Augmented Generation (RAG) system with an agentic tool-use layer, built end-to-end rather than assembled from a managed RAG product: hand-rolled chunking, embedding, and vector search, plus [Claude](https://www.anthropic.com/claude) on [AWS Bedrock](https://aws.amazon.com/bedrock/) driving its own retrieval loop through tool calls instead of a single fixed retrieve-then-generate pass.

## What it does

1. **Upload** a PDF, `.txt`, or `.md` file. It's chunked, embedded, and stored as vectors.
2. **Ask a question.** Claude is given two tools — `search_documents` and `list_documents` — and decides on its own whether to search, how many times, and whether to refine its query.
3. **Get a grounded answer.** Every factual claim is cited back to the exact source chunk (document, page, excerpt). A citation that doesn't trace back to something actually retrieved is dropped, never rendered — see [`docs/llds/generation-agent.md`](docs/llds/generation-agent.md).
4. **See the reasoning.** The UI shows the tool-call trace — what the agent searched for, in what order — not just the final answer.

## Architecture

```
┌────────────────────┐        ┌──────────────────────────┐        ┌──────────────────────┐
│  Frontend           │        │  Backend                  │        │  AWS Bedrock          │
│  React + TS, Vercel │──HTTP──▶  FastAPI, Render          │──API───▶  Claude Haiku         │
│  chat + upload UI   │        │  ingestion / retrieval /  │        │  Titan Embed Text v2  │
└────────────────────┘        │  agent tool-use loop      │        └──────────────────────┘
                               └───────────┬───────────────┘
                                           │
                                  ┌────────▼────────┐
                                  │ Neon Postgres     │
                                  │ + pgvector        │
                                  └───────────────────┘
```

Full system design, the alternatives considered, and the reasoning behind each choice live in [`docs/high-level-design.md`](docs/high-level-design.md) and [`docs/llds/`](docs/llds/). Requirements are tracked as EARS specs in [`docs/specs/`](docs/specs/) and cited directly in code via `@spec` comments — every requirement traces to the code and tests that implement it.

## Why it's built this way

- **No managed RAG service.** No Bedrock Knowledge Bases, no Kendra, no OpenSearch Serverless (which alone carries a real monthly cost floor). RAG is rolled by hand on Postgres + [pgvector](https://github.com/pgvector/pgvector) — cheaper, and it demonstrates the mechanics rather than wiring a black box.
- **Agentic, not scripted.** The retrieval step is exposed to Claude as tools it calls on its own terms, bounded to a handful of round trips per question — not a single hardcoded retrieve-then-generate call.
- **Cost-bounded by design.** Claude Haiku + Titan embeddings on Bedrock, Postgres on Neon's free tier, hosting on Render/Vercel free tiers. Running cost is Bedrock token usage only — pay-per-use, no idle cost.

## Repository layout

```
backend/    FastAPI service — ingestion, retrieval, Bedrock agent loop, API
frontend/   React + TypeScript chat UI
docs/       HLD, LLDs, and EARS specs — the design intent behind the code
```

## Running it locally

**Backend** (Python 3.13, requires a local Postgres with the `pgvector` extension, or see the test suite for a Docker-based one):

```bash
cd backend
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp .env.example .env   # fill in AWS credentials to actually call Bedrock
.venv/bin/python -c "from app.db import run_migrations; run_migrations('<your DATABASE_URL>')"
.venv/bin/uvicorn app.main:app --reload
```

```bash
cd backend && .venv/bin/pytest              # 54 tests: unit + real Postgres/pgvector integration
.venv/bin/ruff check app tests && .venv/bin/mypy app
```

**Frontend** (Node 22+):

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL, if the backend isn't on :8000
npm run dev
```

```bash
cd frontend && npm test && npm run typecheck && npm run lint
```

## Deploying

- **Database**: [Neon](https://neon.tech) Postgres, free tier. Run `backend/migrations/001_init.sql` against it once.
- **Backend**: Render, via `render.yaml` at the repo root (`rootDir: backend`). Set `DATABASE_URL`, `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`, and `FRONTEND_ORIGIN` as Render environment variables.
- **Frontend**: Vercel, with the project root set to `frontend/` and `VITE_API_BASE_URL` pointing at the deployed Render URL.
- **AWS Bedrock**: see [`backend/aws/README.md`](backend/aws/README.md) — model access, a least-privilege IAM policy, and a budget alert.
- **CI**: `.github/workflows/ci.yml` runs backend (ruff, mypy, pytest) and frontend (oxlint, tsc, vitest, build) on every push. `.github/workflows/keep-alive.yml` pings `/health` on a schedule so Render's free tier doesn't cold-start on a recruiter's first click — set the `QASSIST_API_URL` repo variable once deployed.

## Design docs

- [`docs/high-level-design.md`](docs/high-level-design.md) — problem, approach, goals/non-goals, key design decisions
- [`docs/llds/`](docs/llds/) — one low-level design per component (ingestion, retrieval, agent, API, frontend, deployment)
- [`docs/specs/`](docs/specs/) — EARS requirements, each tagged `[x]` implemented / `[ ]` gap / `[D]` deferred, cited in code as `@spec IDS`
