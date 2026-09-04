# KAVACH

**Governance and trust infrastructure for autonomous financial agents.**

Kavach gives teams a single operational surface for governing AI agents that initiate financial activity. It combines deterministic policy enforcement, spend-cap controls, risk scoring, real-time oversight, and an auditable decision trail—so automated action can remain fast without becoming opaque.

> **Status:** Working local prototype. The recommended way to run the complete stack is Docker Compose.

## What it does

- **Agent governance** — manage a hierarchical fleet of financial agents, including trust score, status, delegation relationships, and spending limits.
- **Policy enforcement** — author, prioritize, activate, test, and apply deterministic rules before a transaction is allowed through.
- **Risk decisioning** — combine deterministic rules with Isolation Forest anomaly detection and XGBoost classification to approve, escalate, or deny activity.
- **Spend-cap protection** — enforce per-agent rolling spend limits with Redis-backed coordination and a database fallback.
- **Human-in-the-loop review** — route uncertain or high-risk transactions to an escalation queue for review.
- **Live operations** — stream agent, transaction, and trust-score changes over a secured WebSocket feed.
- **Auditability** — record governance decisions in an append-only audit chain and verify its integrity.
- **Safe demonstrations** — use the isolated sandbox to create a sample fleet and trigger a controlled rogue-agent scenario.

## Architecture

```text
                         Browser
                            │
                    React + Vite UI
                            │
                         Nginx
                   ┌────────┴────────┐
                   │                 │
              REST /api          WebSocket /ws
                   │                 │
                   └────────┬────────┘
                            │
                     FastAPI service
          ┌─────────────────┼──────────────────┐
          │                 │                  │
  Policy & rule engine  Risk scoring      Feed publisher
          │                 │                  │
          │       XGBoost + Isolation Forest   │
          │                 │                  │
          └────────────┬────┴────┬─────────────┘
                       │         │
                  PostgreSQL    Redis
              system of record  cache, pub/sub & caps
```

All transaction decisions begin with deterministic controls. The machine-learning models are loaded once at API startup and run locally in process; the decision path makes no external inference calls.

## Technology stack

| Layer | Technologies |
| --- | --- |
| Web application | React 19, React Router, Vite, Tailwind CSS, Radix UI, Lucide |
| Visualisation | D3, Three.js, React Force Graph |
| API | Python 3.12, FastAPI, Pydantic, Uvicorn |
| Data | PostgreSQL 16, SQLAlchemy (async), Alembic |
| Realtime & cache | Redis 7, Pub/Sub, WebSockets |
| Security | JWT access/refresh tokens, bcrypt password hashing, role-based access controls, API rate limiting |
| Intelligence | XGBoost, scikit-learn Isolation Forest, NumPy |
| Operations | Docker, Docker Compose, Nginx, multi-stage production images |
| Quality | pytest, pytest-asyncio, oxlint |

## Quick start — full stack with Docker

### Prerequisites

- Docker Desktop with Docker Compose v2
- A free local port `8080`

### 1. Create local environment settings

```bash
cp .env.production.example .env.production
```

Replace `POSTGRES_PASSWORD` and `SECRET_KEY` in `.env.production` with long, unique values. Do not commit this file.

### 2. Build and start

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d
```

Open [http://localhost:8080](http://localhost:8080). The same public endpoint also exposes the health check at [http://localhost:8080/health](http://localhost:8080/health).

### 3. Sign in to the seeded demo workspace

| Role | Email | Password |
| --- | --- | --- |
| Administrator | `admin@kavach.dev` | `password123` |
| Operator | `test@kavach.dev` | `password123` |

These credentials are for local demonstration only. Change or remove seeded users before any real deployment.

### Useful Docker commands

```bash
# See service status
docker compose --env-file .env.production -f docker-compose.prod.yml ps

# Follow logs
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f

# Stop the stack without deleting persisted data
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

## Local development

For the quickest dependable setup, use Docker for PostgreSQL and Redis, then run the API and UI separately.

```bash
# Terminal 1 — infrastructure
docker compose -f docker-compose.dev.yml up -d postgres redis

# Terminal 2 — backend
cd backend
python -m venv .venv
# Windows PowerShell: .\\.venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 — frontend
cd frontend
npm install
npm run dev
```

The Vite app is available at `http://localhost:5173`; it communicates with the API on port `8000` during development.

## Risk model design

Kavach uses a layered decision model, rather than relying on a single opaque prediction:

```text
Transaction
    │
    ├── Deterministic policy & spend-cap gates ──► deny when a hard control fails
    │
    └── ML scoring ──► Isolation Forest + XGBoost ──► combined risk score
                                                       │
                               ┌───────────────────────┼───────────────────────┐
                               │                       │                       │
                         < 0.30 approve         0.30–<0.70 escalate        ≥ 0.70 deny
```

- **Isolation Forest** identifies behaviour that is anomalous for a particular agent.
- **XGBoost** estimates transaction risk from the engineered feature contract.
- **Deterministic rules** remain authoritative for explicit policy violations and governance constraints.

Model artifacts live in `ml/artifacts/` and are included in the backend production image. To rebuild them locally:

```bash
cd ml
python download_paysim.py
python augment.py
python train_isolation_forest.py
python train_xgboost.py
python validate.py
```

Retrain locally by running the scripts in the `ml/` directory in order.

## API overview

The API is served under `/api/v1`. FastAPI’s interactive API documentation is available from the backend at `http://localhost:8000/docs` in local development.

| Area | Base path | Purpose |
| --- | --- | --- |
| Authentication | `/api/v1/auth` | Sign-up, sign-in, token refresh, profile management |
| Agents | `/api/v1/agents` | Agent lifecycle, hierarchy, kill switch, exposure simulation |
| Policies | `/api/v1/policies` | Policy CRUD and dry-run evaluation |
| Transactions | `/api/v1/transactions` | Submit and inspect governed transactions |
| Escalations | `/api/v1/escalations` | Review workflow for escalated transactions |
| Audit & compliance | `/api/v1/audit`, `/api/v1/compliance` | Audit records, integrity verification, NIST mapping |
| Sandbox | `/api/v1/sandbox` | Start, reset, and demonstrate a contained scenario |
| Live feed | `/ws/feed` | JWT-authenticated real-time WebSocket updates |

## Repository layout

```text
Kavach/
├── backend/                 FastAPI API, database models, services and tests
│   ├── app/routes/          HTTP and WebSocket endpoints
│   ├── app/services/        Transaction pipeline, scoring, rule engine, audit
│   └── alembic/             Database migrations
├── frontend/                React operations console
├── ml/                      Data preparation, training scripts and model artifacts
├── scripts/                 Deployment helpers
├── docker-compose.dev.yml   Development data services
└── docker-compose.prod.yml  Complete production-like local stack
```

## Verification

```bash
# Backend tests
cd backend
python -m pytest -q

# Frontend production bundle
cd frontend
npm run build

# End-to-end service health (after Docker startup)
curl http://localhost:8080/health
```

## Security notes

- Configure strong, unique `POSTGRES_PASSWORD` and `SECRET_KEY` values for every non-local environment.
- The included demo accounts and model artifacts are intended for prototype use only.
- Put the application behind TLS and configure an explicit CORS allowlist before an internet-facing deployment.
- Treat the audit trail as an operational control, and retain backups of the PostgreSQL volume according to your organisation’s policies.

## License

No license has been declared for this repository. Do not distribute, reuse, or deploy it outside its intended context until a license is added by the project owner.
