# Deployment & Infra

## Context and Design Philosophy

Deployment choices here are driven entirely by the [High-Level Design](../high-level-design.md)'s cost ceiling (~$3 total) and the goal of a live, publicly reachable demo — every service is chosen for its free tier, and the only real spend is Bedrock token usage, which is pay-per-use with no idle cost.

## Topology

| Layer | Service | Tier | Notes |
|-------|---------|------|-------|
| Frontend | Vercel | Free | Static build of the Vite/React app from [Frontend Chat UI](frontend-chat-ui.md) |
| Backend | Render (Web Service) | Free | FastAPI app from [API Backend](api-backend.md); free tier sleeps after inactivity — mitigated by keep-alive pinger |
| Database | Neon (Postgres + pgvector) | Free | Same account/pattern as prior project CreditScope |
| LLM + embeddings | AWS Bedrock | Pay-per-use | Claude Haiku (generation) + Titan Embed Text v2 (embeddings), us-east-1 |

## AWS Bedrock Setup

- **Region**: `us-east-1` (Claude and Titan embedding models both available).
- **Model access**: enabled only for the specific Claude Haiku and Titan Embed Text v2 model IDs — not a blanket "enable all models" — to keep the account's Bedrock surface minimal.
- **Budget guardrail**: an AWS Budget alert set at $5 (above the expected <$3 actual spend, as an early-warning threshold rather than a hard cap) notifying the account owner by email if crossed. **Scoped to `Service: Amazon Bedrock` via a cost filter** — an unscoped budget tracks the whole AWS account's bill, which is the wrong signal if the account runs other infrastructure unrelated to this project (confirmed the hard way: an unscoped budget alerted at $101 driven entirely by pre-existing EC2/Global Accelerator costs, not Bedrock).
- **IAM**: the backend's AWS credentials are scoped to a policy granting only `bedrock:InvokeModel` / `bedrock:Converse` on the specific resources in use — not broad Bedrock or account-level access. Because Claude Haiku is invoked through a cross-region inference profile (see below), that means the inference profile ARN *and* its three underlying regional foundation-model ARNs (Bedrock checks both), plus the Titan embedding model ARN. Template at `backend/aws/iam-policy.json`.
- **Inference profile.** Newer Claude models are not invokable via a bare on-demand model ID on Bedrock — `converse`/`invoke_model` requires the ID (or ARN) of a cross-region inference profile that contains the model, e.g. `us.anthropic.claude-haiku-4-5-20251001-v1:0` rather than `anthropic.claude-haiku-4-5-20251001-v1:0`. This changes the IAM resource list (above) but nothing else in the request shape.
- **Credentials**: passed to the Render service as environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`), never committed to the repo.

## Environment Variables

| Variable | Used by | Example |
|----------|---------|---------|
| `DATABASE_URL` | backend | `postgresql://user:pass@ep-xxx.neon.tech/qassist?sslmode=require` |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | backend | scoped IAM user, see above |
| `AWS_REGION` | backend | `us-east-1` |
| `BEDROCK_CLAUDE_MODEL_ID` | backend | `us.anthropic.claude-haiku-4-5-20251001-v1:0` (a cross-region inference profile ID, not a bare model ID — see below) |
| `BEDROCK_EMBED_MODEL_ID` | backend | `amazon.titan-embed-text-v2:0` |
| `ENVIRONMENT` | backend | `production` \| `development` |
| `VITE_API_BASE_URL` | frontend (build-time) | `https://qassist-api.onrender.com` |

`.env.example` in both `backend/` and `frontend/` documents every variable; real values live only in Render/Vercel's environment variable settings and a local `.env` (gitignored).

## Database Migrations

A single SQL migration (`backend/migrations/001_init.sql`) creates the `pgvector` extension, the `documents`/`chunks` tables from [Ingestion Pipeline](ingestion-pipeline.md), and the cosine-distance index. Run manually against the Neon connection string during initial deploy (`psql $DATABASE_URL -f backend/migrations/001_init.sql`) — no migration framework needed for a single-migration project at this scale.

## Keep-Alive

Render's free tier sleeps a web service after ~15 minutes of inactivity, causing a slow cold-start on the next request — bad for a recruiter's first impression. A lightweight external pinger (reusing the CreditScope pattern: a GitHub Actions scheduled workflow hitting `GET /health` every 10 minutes) keeps the backend warm during expected demo hours.

## CI

GitHub Actions workflow on every push/PR:
1. Backend: install deps, run `ruff`/`mypy` (lint/type-check), run `pytest`.
2. Frontend: install deps, run `oxlint` (the lint tool Vite's current React+TS template scaffolds by default), run `vitest`, run `tsc -b` for type-checking.

CI does not deploy — Render and Vercel both deploy automatically from their own GitHub integration on push to `main`; CI's job is solely to keep `main` green.

## Decisions & Alternatives

| Decision | Chosen | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Backend host | Render free tier | AWS Lambda/ECS, Fly.io | Simplest ops story reused from a prior project; keeping everything-AWS wasn't a goal — Bedrock is where the AWS depth needs to show, not hosting |
| Migration approach | One hand-written SQL file, run manually | Alembic/a migration framework | A single-table-set project doesn't need migration tooling overhead; a framework would be premature abstraction here |
| Keep-alive mechanism | GitHub Actions scheduled ping | A paid Render tier (no sleep) | Free; reuses an already-proven pattern from CreditScope |
| IAM scoping | Least-privilege policy on two specific model ARNs | Broad `bedrock:*` permissions for convenience | Minimizes blast radius of a leaked credential; costs nothing extra to set up correctly |

## Open Questions & Future Decisions

### Resolved
1. ✅ Budget alert set at $5 as an early-warning threshold, not a hard spend cap (Bedrock has no native hard-cap mechanism at time of writing).
2. ✅ Budget scoped to the Bedrock service specifically, not the whole account — see rationale above.

### Deferred
1. Moving the backend into AWS (Lambda/ECS) for an all-AWS story — not needed; documented as a natural next step if the project were to grow beyond a demo.

## References

- [High-Level Design](../high-level-design.md) — cost ceiling and Key Design Decision #5 (deployment topology).
- All other LLDs — this document describes where their components run and how they're configured in production.
