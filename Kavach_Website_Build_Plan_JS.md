# KAVACH — Website Build Plan
### Governance & Trust Layer for Autonomous Financial Agents

A 13-phase, frontend-first production build plan. Every phase is a self-contained master prompt you can hand to a different model — starting with the design system and every screen in the product, then the data layer, backend, ML, and infrastructure that make it real.

**Tracks:** Design · Frontend · Data · Backend · Security · ML · Real-Time · Governance · Integration · DevOps · QA

**Stack:** React + Tailwind + shadcn/ui · FastAPI + PostgreSQL + Redis · scikit-learn + XGBoost · No external LLM API in the decisioning path

> **Change note:** This version replaces TypeScript with plain JavaScript throughout the frontend stack. All `.ts`/`.tsx` file references have been changed to `.js`/`.jsx`, and TypeScript-specific tooling/setup steps have been removed. Backend (Python/FastAPI) and ML (Python) sections are unaffected.

---

## Contents

- Executive Overview
- System Architecture
- Build Roadmap
- 01 Design System & Visual Language — DESIGN
- 02 Application Shell, Navigation & Public Pages — FRONTEND
- 03 Delegation Graph & Live Operator Dashboard — FRONTEND
- 04 Governance Control Panels — FRONTEND
- 05 Database Layer — DATA
- 06 Backend Core — Domain Models, Rule Engine & Transaction Pipeline — BACKEND
- 07 Authentication & Authorization — SECURITY
- 08 ML / Intelligence Layer — ML
- 09 Real-Time Infrastructure & Sandbox Environment — REAL-TIME
- 10 Advanced Governance Features — GOVERNANCE
- 11 Frontend–Backend Integration — INTEGRATION
- 12 DevOps & Deployment — DEVOPS
- 13 Testing, QA & Production Hardening — QA

---

## Executive Overview

### What we're building

Kavach is a governance and trust layer for autonomous financial agents — a website where a bank's operators can watch a live fleet of AI agents (and every sub-agent they spawn) as a graph, set spend policies on them, catch behavior that deviates from an agent's own normal pattern, and — if something goes wrong — instantly cut off one agent, an entire branch of delegated sub-agents, or the whole fleet, with a tamper-evident record of every decision.

It is explicitly not a chatbot, and it makes no calls to any external LLM API anywhere in its decision-making — every governance decision is either a deterministic rule or a locally-trained classical ML model (Isolation Forest + XGBoost), which is what makes every decision explainable and reproducible to an operator or an auditor.

### Why this plan starts at the frontend

Most backend-first plans build the database and API before anyone has seen a single screen — which means the first time real usability problems show up is after the hard engineering is already locked in. This plan works the other way: Phases 01-04 build the entire product's UI first, against mock data, using the same request/response shapes the real backend will eventually implement. That mocked contract becomes the spec every backend phase is held to. By the time Phase 05 (the database) starts, every screen in the product already exists and already defines exactly what data it needs — nothing is designed twice.

### How to read this document

Each phase below is a self-contained master prompt — full context, exact specifications, and a checklist of what "done" means for that phase, written so you can copy the entire phase section into a fresh conversation with any model and it has everything it needs, independent of who builds any other phase. Complex phases are split into lettered sub-phases (1A, 1B, 1C...) so a single session can stay focused rather than trying to hold an entire domain in context at once.

---

## System Architecture

### How the Pieces Fit Together

```
React + Tailwind + shadcn/ui
Operator Console — Phases 01, 02, 03, 04, 11
        │
        │  REST + WebSocket
        ▼
FastAPI Backend (single service)
 ┌───────────────┬───────────────┬────────────────┬──────────────────────┐
 │ RBAC / Auth    │ Rule Engine   │ Risk Scoring    │ Kill Switch /        │
 │ Phase 07       │ Phase 06B     │ (ML) Phase 08D  │ Governance Phase 10  │
 ├───────────────┴───────────────┴─────────────────┴──────────────────────┤
 │ Redis Spend-Cap Enforcement + WebSocket Feed — Phase 09                 │
 │ Transaction Pipeline Orchestrator — Phase 06C — process_transaction()   │
 └───────────────────────────────────────────────────────────────────────┘
   No external LLM API is called anywhere in this system — every decision
   is a deterministic rule or a locally-trained classical model.
        │                 │                    │
        ▼                 ▼                    ▼
   PostgreSQL           Redis               ML Artifacts
   organizations ·      spend:{agent_id}:    isolation_forest.pkl
   users · agents ·     {window}             xgboost_risk.pkl
   policies ·           agent_status:        (Phase 08B/08C)
   transactions ·       {agent_id}
   audit_log ·          session:{session_id}
   escalation_queue     (Phase 05B)
   (Phase 05A)
```

Local dev: Vite + Uvicorn · Production: Docker + Nginx + TLS reverse proxy (Phase 12)
Hosting: containerized, horizontally scalable behind the FastAPI layer — Postgres never sits on the real-time hot path.

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React + JavaScript + Tailwind CSS + shadcn/ui | Component design curated from 21st.dev, re-themed to the Phase 01 token set |
| Data visualization | react-force-graph | The delegation graph is the product's signature screen |
| Backend | FastAPI (Python 3.11+) | Single service — rule engine and ML scoring run in-process |
| Database | PostgreSQL | Multi-tenant from day one (`organizations` / `org_id` scoping) |
| Cache / real-time hot path | Redis | Spend-cap counters, agent status, sessions |
| Real-time transport | WebSockets (FastAPI native) | Same message contract the frontend mocks from Phase 03 onward |
| ML | scikit-learn (Isolation Forest) + XGBoost | Trained offline, loaded from disk, zero inference-time network calls |
| Auth | JWT access/refresh + bcrypt | Role-based access control: viewer / reviewer / operator / admin |
| Deployment | Docker + Nginx + GitHub Actions CI/CD | Separate staging/production environments and databases |

---

## Build Roadmap — 13 Phases, Frontend to Infrastructure

Recommended order: top to bottom. Phases 02-04 (all frontend) can run as three back-to-back sessions with the same or different models. Once Phase 07 (Auth) is done, Phases 08 and 09 can run in parallel. Phase 11 cannot start until every phase above it is complete.

1. Design System & Visual Language — DESIGN
2. Application Shell, Navigation & Public Pages — FRONTEND
3. Delegation Graph & Live Operator Dashboard — FRONTEND
4. Governance Control Panels — FRONTEND
5. Database Layer — DATA
6. Backend Core — Domain Models, Rule Engine & Transaction Pipeline — BACKEND
7. Authentication & Authorization — SECURITY
8. ML / Intelligence Layer — ML
9. Real-Time Infrastructure & Sandbox Environment — REAL-TIME
10. Advanced Governance Features — GOVERNANCE
11. Frontend–Backend Integration — INTEGRATION
12. DevOps & Deployment — DEVOPS
13. Testing, QA & Production Hardening — QA

---

## PHASE 01 · DESIGN — Design System & Visual Language

**Suggested model:** A frontend-design-capable model (e.g. Claude Sonnet 5 or Claude Opus 4.8 with design attention, or a dedicated UI tool). This phase outputs tokens and a component style guide, not application logic — there is no real data anywhere in this phase.

Establish the complete visual identity — colors, type, spacing, components — before a single real screen gets built, so every later phase, even executed by a different model, produces UI that looks like one coherent product.

### Why this phase exists and comes first

Every phase after this one — every dashboard, every panel, every table — inherits its look from decisions made here. If this phase is skipped or left implicit, five different models building five different screens will each invent their own spacing, their own greys, their own idea of what a "card" looks like, and the product will read as five products stitched together. This phase's entire job is to prevent that.

### 1A — Color, Typography & Spacing Tokens

Build a Tailwind theme extension that becomes the single source of truth every later phase imports from — never redefine colors inline in a component.

**Color system** (zinc-based neutral, indigo/violet primary — a modern, trustworthy, security-product palette; avoid generic Bootstrap blue or default Tailwind slate-only palettes):

| Token | Hex | Use |
|---|---|---|
| background (light / dark) | #FAFAFA / #09090B | App background |
| surface (light / dark) | #FFFFFF / #18181B | Cards, panels |
| border | #E4E4E7 / #27272A | Dividers, card outlines |
| text-primary | #18181B / #FAFAFA | Body text |
| text-secondary | #71717A / #A1A1AA | Muted/meta text |
| primary-500 (brand) | #6366F1 | Primary actions, links, focus rings |
| primary-600 | #4F46E5 | Primary hover/active |
| violet-500 (accent) | #8B5CF6 | Secondary accent, design-phase branding |
| success-500 | #10B981 | Approved, active, healthy |
| warning-500 | #F59E0B | Escalated, elevated risk, trust score dropping |
| danger-500 | #EF4444 | Denied, revoked, kill switch, tampered audit chain |
| info-500 | #0EA5E9 | Informational, neutral highlights |

Ship both a light and a dark theme from day one, class-based (`dark:` variants), not media-query-only — an operator console for financial governance is a long-session control-room tool, and dark mode is the expected default for that category of product (mirror the aesthetic of tools like Linear, Vercel's dashboard, and Stripe's dashboard, not a marketing site).

**Typography:** Inter for all UI text (variable weights 400/500/600/700/800), JetBrains Mono for anything that is data, not prose — agent IDs, hashes, JSON, code, timestamps. Never render a UUID or a hash in the UI font; the monospace switch is itself a usability signal that "this is copyable data."

**Spacing & radius:** 4px base spacing unit; card/panel radius 12px (`rounded-xl`), button/input radius 8px (`rounded-lg`), pill/badge radius 9999px (`rounded-full`). Consistent shadow scale: a single soft `shadow-sm` for resting cards, a slightly stronger `shadow-md` only on hover/focus — avoid heavy drop shadows, which read as dated rather than modern.

**Deliverable:** `frontend/tailwind.config.js` with the full token set above under `theme.extend`, plus `design/tokens.md` documenting every token and when to use it.

### 1B — Component Foundations: shadcn/ui + curated 21st.dev references

Install shadcn/ui as the headless component foundation (Radix primitives + Tailwind, not a heavyweight component framework like MUI or Ant — shadcn keeps every component's code in-repo and fully restylable, which matters when five different phases/models are going to be extending these).

Use 21st.dev as a reference gallery, not a dependency — browse it for the handful of pieces that are genuinely hard to get right from scratch, adapt what you find to the exact tokens from 1A, and commit the adapted version into the repo's own component library:

- A bento-grid dashboard layout (mixed-size metric cards) for the main overview page
- An animated number/counter component (for live spend totals, trust scores ticking)
- A command palette (`Cmd/Ctrl+K`) for fast navigation between agents/policies
- A slide-over / sheet panel (used for kill-switch confirmation and the blast-radius preview)
- A sticky-header data table with sortable columns (transaction feed, audit log, agent list)
- A toast/notification system (transaction denials, kill-switch confirmations)
- A segmented control (view toggles: graph view / list view)

Every component adapted from an external reference must be re-themed to the token set from 1A before it's committed — nothing should visually read as "a component someone else designed for someone else's product."

**Deliverable:** `frontend/src/components/ui/` — the shadcn base set plus the curated, re-themed additions above, each with a one-line comment noting what it's for.

### 1C — Reference Screens & UI States

Before any screen with real routing or data exists, build 5-6 static reference components (hardcoded fake data, no API calls) that lock in the "house style" every later phase must match:

- A metric card (the bento-grid tile used on the dashboard)
- A table row with a risk-score badge (color-coded: green <0.3, amber 0.3–0.7, red >0.7 — pick your own thresholds but keep them consistent everywhere this badge appears)
- A graph-node tooltip (hover state for the delegation graph)
- Empty state (e.g. "No agents yet")
- Loading skeleton (shimmer placeholders, not spinners, for card/table content)
- Error state (a failed API call, styled as a recoverable inline message, not a full-page crash)

**Deliverable:** `frontend/src/components/reference/` — these components are throwaway scaffolding once later phases build the real thing, but they must exist first so the visual contract is unambiguous.

### Interface contract this phase produces (every later frontend phase depends on this)

- `tailwind.config.js` token names — reuse `primary-500`, `success-500`, `danger-500` etc. by name, never hardcode a hex value in a component file again after this phase.
- The component names and props exported from `components/ui/` — later phases import these, they do not rebuild a second button or card component.
- The risk-score badge color thresholds from 1C — reused verbatim in the transaction feed, audit log, and agent detail pages.

### Acceptance criteria

- [ ] `tailwind.config.js` compiles and every token in the table above resolves to the correct hex in both light and dark mode
- [ ] Inter and JetBrains Mono are loaded and applied correctly (UI text vs. data/code text) across the reference screens
- [ ] All 6 reference screens/states from 1C render correctly in both light and dark mode
- [ ] Every component in `components/ui/` has zero hardcoded color values — everything traces back to a token

---

## PHASE 02 · FRONTEND — Application Shell, Navigation & Public Pages

**Suggested model:** A general-purpose frontend coding model or agentic coding tool. Depends entirely on Phase 1's component library — do not proceed if that phase isn't done.

Build the skeleton every screen lives inside — routing, layout, navigation — plus the pages a visitor sees before they're a logged-in operator: the public marketing page and the auth flow.

### What this phase assumes (from Phase 01)

The full token set and component library at `frontend/src/components/ui/` exist and are ready to import. Every layout/nav element built in this phase must be composed from those components, not new one-off styling.

### Full site map (build routing for all of it now, even where the page is a stub until later phases fill it in)

```
/                              Public landing page (2C)
/login /signup /forgot-password /reset-password   Auth pages (2B)
/app                           Redirects to /app/dashboard once authenticated
/app/dashboard                 Overview — bento grid + graph preview (Phase 03)
/app/graph                     Full delegation graph (Phase 03)
/app/agents                    Agent list
/app/agents/:id                Agent detail (policies, history, sub-agents)
/app/policies                  Policy list
/app/policies/new /:id/edit    Policy builder (Phase 04)
/app/kill-switch               Kill switch console (Phase 04)
/app/blast-radius              Blast radius simulator (Phase 04)
/app/dry-run                   Policy dry-run sandbox (Phase 04)
/app/audit-log                 Audit log explorer (Phase 04)
/app/compliance                NIST RMF compliance panel (Phase 04)
/app/escalations               Escalation / human-review queue (Phase 04)
/app/sandbox                   Sandbox environment controls (Phase 09)
/app/settings                  Org & user settings, API keys
```

### 2A — App Shell, Routing & Layout

- Vite + React + JavaScript + React Router.
- Two distinct layouts: an unauthenticated `PublicLayout` (simple top nav, footer) for `/`, `/login` etc., and an authenticated `AppLayout` for everything under `/app` — collapsible left sidebar (icon-only collapsed state), top bar with the command palette trigger, user menu, and a global "Sandbox Mode" indicator (from Phase 09 — build the toggle's visual slot now even though it does nothing yet).
- Sidebar groups, in this order: Overview, Fleet (Graph, Agents), Governance (Policies, Kill Switch, Blast Radius, Dry-Run, Audit Log, Compliance), Review (Escalations), Sandbox, Settings.
- Route guards: an authenticated-only wrapper redirecting to `/login` — wire this against a placeholder `useAuth()` hook now; Phase 07/11 will fill in the real implementation, this phase just needs the seam to exist.
- Command palette (`Cmd+K`, from 1B) wired to route navigation across the whole site map above.

### 2B — Auth Pages UI

Build `/login`, `/signup`, `/forgot-password`, `/reset-password` as fully designed pages — form validation, loading/error states (using the states from 1C) — but backed by a mock handler, not a real backend. Use MSW (Mock Service Worker) to intercept `POST /api/v1/auth/login` etc. and return realistic fake responses. Document the exact mocked request/response JSON shape in `frontend/src/mocks/handlers/auth.js` — this file is the API contract Phase 07 (backend auth) must implement against.

### 2C — Public Landing Page

A real marketing page — this is a "proper website," not just an internal tool, so it needs a public face: hero section (product name, one-line value proposition, CTA to sign up/request access), a features section (3-4 cards: delegation-aware kill switch, real-time risk scoring, tamper-evident audit log, NIST RMF alignment), and a footer. Keep copy factual and product-focused, not pitch-deck language.

### Interface contract this phase produces

- The full route list above — every later frontend phase builds inside these exact paths.
- `frontend/src/mocks/handlers/auth.js` — the request/response contract Phase 07's backend auth must match exactly (field names, status codes, error shape).
- The `useAuth()` hook signature (`{ user, isAuthenticated, login(), logout() }`) — Phase 11 replaces its internals, not its call sites.

### Acceptance criteria

- [ ] Every route in the site map resolves to at least a stub page without a 404 or crash
- [ ] Authenticated routes redirect to `/login` when `useAuth()` reports logged-out, and back to `/app/dashboard` after a successful mock login
- [ ] Login/signup forms validate input, show loading and error states, and succeed against the MSW mock
- [ ] Command palette navigates to every route in the site map
- [ ] Landing page is responsive down to a normal mobile viewport width

---

## PHASE 03 · FRONTEND — Delegation Graph & Live Operator Dashboard

**Suggested model:** A frontend coding model comfortable with data visualization libraries and animation. Depends on Phases 01 and 02.

Build the two screens that make the product legible at a glance: the live delegation graph and the main operator dashboard — both driven by simulated live data so they're fully interactive before any backend exists.

### What this phase assumes

`AppLayout` and the `/app/dashboard` and `/app/graph` route stubs exist from Phase 02. The component library and tokens from Phase 01 are used throughout — do not introduce new one-off colors for graph nodes; derive node states from the `success/warning/danger` tokens.

### 3A — Delegation Graph Visualization

- Library: `react-force-graph` (2D). This is the single most distinctive screen in the product — an operator should be able to see, at a glance, which agent spawned which sub-agents, and which part of the tree is currently a problem.
- Node encoding: color = status/trust (green = active + high trust, amber = active + degraded trust, red/grey = revoked), size = relative spend cap or recent activity level, a small pulsing ring on any node with a transaction in the last few seconds.
- Edge encoding: parent→child delegation edges; animate a brief pulse along the edge when a transaction flows through it.
- Interaction: hover shows the tooltip component from Phase 01's reference screens (agent name, type, trust score, current spend vs. cap); click opens a slide-over with full agent detail; a visible, unmistakable **kill-switch affordance** reachable directly from a node's context menu (even though it doesn't call a real endpoint yet — wire the click through to a mock handler that just updates local state, matching the eventual real contract from Phase 10A).
- Data source for this phase: **not a real backend** — build a local mock data generator (a small class or hook simulating 8-12 agents transacting at varied intervals, using `setInterval`/`requestAnimationFrame`, structured so its output shape is identical to the real WebSocket message contract Phase 09B will define). This is the same pattern as MSW for REST — you're mocking the real-time layer too, not skipping it.

### 3B — Operator Dashboard

- Bento-grid overview (from Phase 01's curated component): total active agents, transactions in the last hour, average trust score, current max blast-radius exposure across the fleet, all as animated-counter tiles.
- A compact preview of the delegation graph (links through to the full `/app/graph` view).
- Live transaction feed: a scrolling list of the last ~30 simulated transactions, each row showing agent, amount, merchant category, decision (approve/deny/escalate, color-coded via the risk badge convention from Phase 01), risk score.
- Per-agent spend bars and trust-score tickers as small live-updating widgets, driven by the same mock data generator as 3A — both screens must consume the same mock data source so numbers agree between the dashboard and the graph view.

### Interface contract this phase produces

- The mock live-data generator's message shape (`transaction_update`, `agent_status_update`, `trust_score_update`, `graph_snapshot` — matches the WebSocket contract Phase 09B will implement for real) documented in `frontend/src/mocks/livedata-contract.md`.
- The risk-score-to-color mapping function, exported and reused by Phase 04's audit log and policy screens.

### Acceptance criteria

- [ ] Graph renders a 3-level delegation tree cleanly and stays readable as simulated sub-agents are added
- [ ] Node/edge visual states update live as the mock generator produces events, with no flicker or layout thrash
- [ ] Dashboard tiles animate smoothly on value change (not an abrupt number swap)
- [ ] Transaction feed and graph view show consistent numbers because both read the same mock source
- [ ] Full dark/light mode parity on both screens

---

## PHASE 04 · FRONTEND — Governance Control Panels

**Suggested model:** A frontend coding model. This is the largest single frontend phase — consider running its three sub-phases as three separate sessions even with the same model, to keep each session's context focused.

Build every screen an operator uses to actually govern the fleet: the kill switch, the blast-radius simulator, the policy builder and dry-run sandbox, the audit log, the compliance panel, and the human escalation queue — all against mock data, establishing the exact API contract the backend phases must satisfy.

### What this phase assumes

Phases 01-03 are complete. The mock live-data generator from 3A is the shared source of truth this phase's panels react to and act on.

### 4A — Kill Switch Console & Blast Radius Simulator

- **Kill Switch Console** (`/app/kill-switch`): three unmistakably distinct actions — revoke node, revoke subtree, revoke fleet — each requiring a confirmation step in a slide-over (from Phase 01B) that shows exactly which agents will be affected (rendered as a highlighted subset of the graph from 3A, reused as a component, not rebuilt) before the operator can confirm. This preview-before-you-click behavior is a hard product requirement, not a nice-to-have — build the confirmation step so it cannot be skipped.
- **Blast Radius Simulator** (`/app/blast-radius`): a form (proposed spend cap, proposed max sub-agents, proposed max delegation depth) that returns a concrete worst-case dollar exposure number with a breakdown, rendered as a small stacked bar or donut chart, against a mock calculation function matching the real formula Phase 10B will implement.

### 4B — Policy Builder & Dry-Run Sandbox

- **Policy Builder** (`/app/policies/new`, `/app/policies/:id/edit`): a form-based visual editor for the rule JSON — field/operator/value rows, with `all`/`any` grouping — no raw JSON textarea as the primary interface (power users can have a "view as JSON" toggle, but the default experience should not require reading a schema). This directly determines whether real operators can use the product without engineering help.
- **Dry-Run Sandbox** (`/app/dry-run`): pick a policy (existing or in-progress from the builder), run it against a mock set of historical transactions, show a before/after diff table — which transactions would newly be blocked, which would newly be allowed — color-coded via the risk badge convention.

### 4C — Audit Log, Compliance Panel & Escalation Queue

- **Audit Log Explorer** (`/app/audit-log`): a searchable/filterable table (event type, agent, date range) plus a prominent "Verify Chain Integrity" button that calls a mock verification function and displays either a clear success state or, if tampered (toggleable in the mock for testing), the exact broken record — this is a flagship trust feature, its success/failure state should be visually unmistakable, not a quiet toast.
- **NIST Compliance Panel** (`/app/compliance`): render the GOVERN/MAP/MEASURE/MANAGE mapping table (same table structure Phase 10E's API will serve) as a clean, presentable reference screen — this doubles as something the product can show a compliance officer directly.
- **Escalation Queue** (`/app/escalations`): a queue of medium-risk transactions awaiting human review, each row expandable to show full context (agent history, trust score, delegation chain, what triggered the flag) with one-click approve/deny/adjust-cap actions.

### Interface contract this phase produces (this is the deliverable every backend phase from here on must match)

Document every mock endpoint this phase creates, with exact request/response JSON, in `frontend/src/mocks/handlers/governance.md`:

- `POST /api/v1/agents/:id/kill` (mode: node/subtree/fleet)
- `POST /api/v1/agents/:id/simulate-exposure`
- `POST /api/v1/policies/:id/dry-run`
- `GET /api/v1/audit/verify`
- `GET /api/v1/compliance/nist-mapping`
- `GET/POST /api/v1/escalations`

Treat this document as binding — Phases 06 and 10 implement against it, not the other way around.

### Acceptance criteria

- [ ] Kill switch cannot be confirmed without the affected-agents preview being shown first
- [ ] Blast radius form returns a number + breakdown against the mock calculator
- [ ] Policy builder produces valid rule JSON without the user ever needing to hand-write it
- [ ] Dry-run diff table correctly reflects mock before/after changes
- [ ] Audit verify button has a clearly distinct success vs. tampered visual state
- [ ] Every mock endpoint used in this phase is documented in governance.md with exact JSON shapes

---

## PHASE 05 · DATA — Database Layer

**Suggested model:** A backend-focused coding model; no frontend or ML knowledge required for this phase.

Stand up the persistent data layer — PostgreSQL schema and Redis data structures — implementing exactly the API contract the frontend phases already defined.

### What this phase assumes

The mock API contracts documented in `frontend/src/mocks/handlers/*.md` (Phases 02-04) define every field this schema must be able to produce. Read those files before designing columns — this phase serves the frontend's already-established needs, it does not redesign them.

### 5A — PostgreSQL Schema & Migrations

```sql
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id),
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'operator', -- 'admin' | 'operator' | 'reviewer' | 'viewer'
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id),
  name TEXT NOT NULL,
  type TEXT NOT NULL, -- 'travel' | 'subscription' | 'procurement' | 'sub-agent'
  parent_agent_id UUID REFERENCES agents(id) NULL,
  trust_score FLOAT NOT NULL DEFAULT 0.5,
  spend_cap_current NUMERIC(12,2) NOT NULL,
  status TEXT NOT NULL DEFAULT 'active', -- 'active' | 'revoked'
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE policies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id),
  name TEXT NOT NULL,
  rule_json JSONB NOT NULL,
  priority INT NOT NULL DEFAULT 100,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agents(id),
  amount NUMERIC(12,2) NOT NULL,
  merchant_category TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  decision TEXT NOT NULL, -- 'approve' | 'deny' | 'escalate'
  risk_score FLOAT NULL,
  triggered_rule_id UUID REFERENCES policies(id) NULL,
  delegation_chain_id UUID NOT NULL
);

CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id),
  event_type TEXT NOT NULL, -- 'grant' | 'deny' | 'override' | 'revoke' | 'kill_switch'
  agent_id UUID REFERENCES agents(id) NULL,
  actor_user_id UUID REFERENCES users(id) NULL,
  payload JSONB NOT NULL,
  prev_hash TEXT NULL,
  this_hash TEXT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE escalation_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  transaction_id UUID NOT NULL REFERENCES transactions(id),
  status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'approved' | 'denied' | 'adjusted'
  reviewer_id UUID REFERENCES users(id) NULL,
  reviewed_at TIMESTAMPTZ NULL
);

CREATE INDEX idx_agents_parent ON agents(parent_agent_id);
CREATE INDEX idx_agents_org ON agents(org_id);
CREATE INDEX idx_transactions_agent ON transactions(agent_id);
CREATE INDEX idx_transactions_delegation_chain ON transactions(delegation_chain_id);
CREATE INDEX idx_audit_log_org ON audit_log(org_id);
```

Note the `organizations` / `users` / `org_id` additions versus a single-tenant demo schema — a real website has real accounts, and every table that holds governance data must be scoped to an organization even if you only ever run one org in practice initially. Use Alembic for migrations from the very first commit, not a hand-run `CREATE TABLE` script — schema changes in every later phase go through a migration, no exceptions.

### 5B — Redis Data Layer

- `spend:{agent_id}:{window}` — rolling spend counter, TTL matching the window
- `agent_status:{agent_id}` — `active` | `revoked`, sub-millisecond read on the hot path
- `session:{session_id}` — auth session data (Phase 07 will define the exact shape)
- Connection handling: a pooled async Redis client (`redis-py` with asyncio support), initialized once at app startup, not per-request.

### Interface contract this phase produces

- The exact table/column names above — every backend phase from here on uses these names verbatim.
- Redis key naming conventions above.
- A seed script (`backend/app/seed.py`) creating one organization, one admin user, 6-8 agents including a 3-level delegation chain, and 6-10 policies — this is what every later phase's local dev environment starts from.

### Acceptance criteria

- [ ] `make db-reset` (see the project Makefile) drops, recreates, migrates, and seeds cleanly from nothing
- [ ] Every table matches the schema above exactly, including indexes
- [ ] Seed script produces a working 3-level delegation chain
- [ ] Redis connection is pooled and shared, not reconnected per request

---

## PHASE 06 · BACKEND — Backend Core — Domain Models, Rule Engine & Transaction Pipeline

**Suggested model:** A strong general-purpose backend coding model, ideally agentic (can run tests and iterate).

Implement the CRUD API and the deterministic rule engine that decides, before any ML or real-time layer exists, whether a transaction is allowed — matching the API contract the frontend already committed to.

### What this phase assumes

Phase 05's schema exists and is migrated. The API contract documented by the frontend phases (`frontend/src/mocks/handlers/*.md`) defines the exact endpoints and JSON shapes this phase must produce — treat mismatches as bugs in this phase, not license to redesign the contract unilaterally; if a contract genuinely can't be satisfied, flag it rather than silently diverging.

### 6A — Domain Models & CRUD API

- FastAPI (Python 3.11+), SQLAlchemy models mirroring the Phase 05 schema exactly, Pydantic schemas for every request/response.
- `POST/GET/PUT/DELETE /api/v1/agents`, `GET /api/v1/agents/:id/children` (direct children), `POST/GET/PUT/DELETE /api/v1/policies` — all scoped to the authenticated user's `org_id` (Phase 07 supplies the auth dependency; build this phase's routes to accept an injected `current_org_id` so wiring in real auth later is a one-line change, not a rewrite).
- `DELETE /agents/:id` returns `409` if the agent has children or transactions.

### 6B — Rule Engine

A pure, side-effect-free function, unit-testable in isolation:

```python
def evaluate_rules(transaction: dict, policies: list[Policy]) -> RuleResult:
    # Deny-by-default: every ACTIVE policy, sorted by priority ascending, is a
    # condition the transaction must satisfy. First failure -> immediate deny.
    # RuleResult: passed (bool), denied_by (Policy|None), evaluation_trace (list[dict])
    ...
```

Condition shape: `{"field": "amount", "op": "<=", "value": 500}`, combinators `{"all": [...]}` / `{"any": [...]}`.

Supported `op`: `==`, `!=`, `<`, `>`, `<=`, `>=`, `in`, `not_in`. Supported `field`: `amount`, `merchant_category`, `delegation_depth`, `agent_type`, `time_of_day_hour`.

The `evaluation_trace` is what makes every decision explainable in the UI's audit log — it must contain every policy checked, in order, with its condition and whether it was satisfied, not just the final verdict.

### 6C — Transaction Pipeline Orchestrator

`process_transaction(agent_id, amount, merchant_category) -> TransactionResult` as an internal function, separate from the route handler — Phase 09 inserts a Redis check before it runs, Phase 08 inserts risk scoring after `evaluate_rules()` passes. Structure this now so those are clean insertions later, not rewrites.

`POST /api/v1/transactions` calls this function, writes a `transactions` row and an `audit_log` row (`write_audit()` — Phase 10D will modify its internals for hash-chaining without changing any call site).

### Interface contract this phase produces

- `evaluate_rules()` and `process_transaction()` signatures exactly as above.
- `write_audit(event_type, agent_id, payload, actor_user_id=None)` signature.
- Full OpenAPI schema at `/docs` — Phase 11 uses this to verify the frontend's mocked contract actually matches what got built.

### Acceptance criteria

- [ ] All CRUD endpoints match the frontend's documented mock contract field-for-field
- [ ] Rule engine unit tests cover: pass, single-rule deny, compound-rule deny, empty-policy pass-through, delegation-depth correctness against the seeded 3-level chain
- [ ] Every `POST /transactions` call writes both a `transactions` and an `audit_log` row with a full evaluation trace
- [ ] `pytest` passes fully

---

## PHASE 07 · SECURITY — Authentication & Authorization

**Suggested model:** A backend model with security-conscious defaults — this is a phase worth having your strongest available model review, since auth bugs are the highest-cost mistake category in the whole project.

Turn this from an open API into a real multi-user product: real accounts, real sessions, and role-based access control enforced on every governance-sensitive endpoint.

### What this phase assumes

Phase 05's `users` / `organizations` tables and Phase 06's routes (built with an injectable `current_org_id`) exist. Phase 02B's mock auth contract (`frontend/src/mocks/handlers/auth.js`) defines the exact request/response shape this phase must implement against.

### 7A — User Model & Credential Auth

- Password hashing: bcrypt (via `passlib`), never store or log plaintext passwords.
- `POST /api/v1/auth/signup`, `POST /api/v1/auth/login` (returns a JWT access token + refresh token), `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `POST /api/v1/auth/forgot-password` / `reset-password` (token-based, time-limited).
- JWT payload: `{sub: user_id, org_id, role, exp}`. Access tokens short-lived (~15 min), refresh tokens longer-lived and stored server-side (in the `session:{session_id}` Redis key from Phase 05B) so they can be revoked.

### 7B — RBAC Middleware & Route Protection

Four roles, least-privilege by default:

| Role | Can do |
|---|---|
| viewer | Read-only: dashboard, graph, audit log, compliance panel |
| reviewer | Everything viewer can, plus act on the escalation queue |
| operator | Everything reviewer can, plus create/edit policies, run dry-runs, use the blast radius simulator |
| admin | Everything, plus the kill switch, user management, org settings |

A FastAPI dependency (`require_role(min_role)`) applied per-route — in particular, `POST /agents/:id/kill` (any mode) must require `admin`, given what it does.

Every route from Phase 06 gets its `current_org_id` parameter replaced with a real dependency reading the JWT, and every table query gets scoped to that org — a cross-org data leak here is a severe bug, write a specific test for it (user from org A cannot read/act on org B's agents, full stop).

### Interface contract this phase produces

- The `require_role()` dependency, applied across every route in Phases 06, 08, 09, 10 going forward.
- Real implementation behind the frontend's `useAuth()` hook (Phase 02A) — token storage, refresh handling, logout.

### Acceptance criteria

- [ ] Signup/login/refresh/logout match the frontend's documented contract exactly
- [ ] Passwords are hashed, never logged, never returned in any response
- [ ] A `viewer`-role token receives 403 on every write endpoint
- [ ] A cross-org access test explicitly fails an attempt to read/act on another org's data
- [ ] Refresh tokens are revocable (logout actually invalidates the session, verified by test)

---

## PHASE 08 · ML — ML / Intelligence Layer

**Suggested model:** A model strong at data science / Python, ideally with code execution so it reports real metrics back to you rather than estimated ones.

Add real, locally-trained risk scoring on top of the deterministic rule engine — no external LLM/API calls, ever, for any decisioning logic.

### What this phase assumes

Phase 06's `process_transaction()` calls `evaluate_rules()` first; this phase adds a scoring step immediately after it passes, without altering the pipeline's overall shape.

### Hard constraint

No external LLM API (OpenAI/Anthropic/Gemini/etc.) anywhere in this phase or anywhere in the product. Every risk decision is a deterministic rule or a locally-trained classical model, loaded from disk at startup, zero network calls at inference time. This is a permanent architectural decision, not a shortcut to revisit later — it's what makes every decision reproducible and explainable to an operator or an auditor.

### 8A — Data Acquisition & Augmentation

- Base dataset: PaySim (Kaggle, `ealaxi/paysim1`) — ~6.3M synthetic transactions with a realistic 0.13% fraud rate.
- Handle the known balance-leakage caveat deliberately: engineer deltas/ratios (`balance_delta_orig = newbalanceOrig - oldbalanceOrg`) instead of feeding raw balance columns to either model, and document the decision.
- `augment.py`: group by `nameOrig` as a proxy `agent_id`; synthesize `agent_type`, `delegation_chain_id`, `declared_intent`, `authorized_by`; compute rolling per-agent behavioral features (velocity, amount deviation from the agent's own rolling mean — not a global mean, merchant-category entropy, time-of-day pattern); inject a documented, small set of scripted rogue sequences labeled `is_agent_anomaly` (a target distinct from PaySim's own `isFraud`).

### 8B — Isolation Forest (unsupervised)

- Trained per-agent or per-agent-type on the rolling behavioral features only — this is what lets it flag "unusual for this agent" rather than applying one global threshold to everyone.
- Saved via `joblib` to `ml/artifacts/isolation_forest.pkl`.

### 8C — XGBoost (supervised)

- Target: `is_agent_anomaly`. Validation split created before rogue-sequence injection, so reported metrics aren't measuring an artificially easy task.
- Output: calibrated 0-1 probability, not just a binary class. Report precision/recall/F1/AUC honestly in `ml/validation_report.md`.
- Saved to `ml/artifacts/xgboost_risk.pkl`, versions pinned in `requirements.txt`.

### 8D — Model Serving Integration

```python
def score_transaction(agent_id: str, transaction_features: dict) -> RiskScore:
    # RiskScore: score (0-1), isolation_forest_flag (bool), xgboost_score (float),
    # top_features (list[tuple[str, float]]) — feature importances, for explainability
```

Both artifacts loaded once at FastAPI startup, zero inference-time network calls (verify with network disabled if your environment allows).

Wired into `process_transaction()`: after `evaluate_rules()` passes, call this, write `transactions.risk_score`, set `decision` (approve below a threshold, escalate in a middle band, deny above a high threshold — configurable, not hardcoded magic numbers scattered through the code).

### Interface contract this phase produces

- `score_transaction()` signature exactly as above — the transaction feed, audit log, and escalation queue UI all display `top_features` for explainability.

### Acceptance criteria

- [ ] Augmentation script runs end-to-end and the leakage fix is verifiably implemented, not just claimed
- [ ] Validation split predates rogue injection, verifiable in code
- [ ] `validation_report.md` contains real metrics from an actual run
- [ ] Both artifacts load in a fresh process with zero network calls
- [ ] `score_transaction()` returns an in-range score with non-empty feature importances

---

## PHASE 09 · REAL-TIME — Real-Time Infrastructure & Sandbox Environment

**Suggested model:** An agentic coding tool spanning backend and frontend integration.

Make the product feel alive: Redis-backed spend enforcement on the hot path, a WebSocket feed replacing the frontend's mock live-data generator, and a permanent Sandbox Mode that lets any customer test policies against synthetic traffic before connecting real agents.

### What this phase assumes

Phase 05B's Redis keys exist. Phase 03A's frontend mock live-data generator defined the exact message contract (`transaction_update`, `agent_status_update`, `trust_score_update`, `graph_snapshot`) this phase's real WebSocket feed must produce byte-for-byte, so swapping mock for real in Phase 11 is a one-line change.

### 9A — Redis Spend-Cap Enforcement

```python
def check_and_reserve_spend(agent_id: str, amount: float, window: str = "1h") -> bool:
    # Atomic (Lua script or MULTI/WATCH — not GET-then-SET, which races under
    # concurrent calls for the same agent). Checks agent_status:{agent_id} first;
    # 'revoked' short-circuits to False without touching the spend counter.
```

Insert as the first step of `process_transaction()`, before the rule engine runs at all — a revoked agent or a maxed-out cap should never reach the rule engine or the ML scorer.

### 9B — WebSocket Transport

- `/ws/feed` (authenticated — a connection must present a valid session, scoped to the connecting user's `org_id`, so operators only ever see their own organization's fleet).
- On connect: push a `graph_snapshot`. Then stream `transaction_update` / `agent_status_update` / `trust_score_update` on every `process_transaction()` completion, matching the frontend's mocked message shape exactly.
- Graceful reconnect handling on the server side (don't let one dropped client break the broadcast loop for others) — this is what Phase 04's UI reconnect logic (built in Phase 11) depends on.

### 9C — Sandbox Environment (a real product feature, not a demo hack)

Reframe what would be a hackathon's "Agent Simulator" as a permanent, customer-facing capability: any organization can toggle Sandbox Mode (the UI slot for this was reserved back in Phase 02A's app shell) to spin up a synthetic fleet of 8-12 agents transacting continuously, entirely isolated from their real data (an `is_sandbox` boolean scoping every table, or a fully separate sandbox schema — pick one and document it; a separate schema is cleaner for guaranteeing no accidental mixing with real financial data).

`POST /api/v1/sandbox/start`, `POST /api/v1/sandbox/reset`, `POST /api/v1/sandbox/trigger-rogue` (spikes one synthetic agent and spawns 2 unauthorized sub-agents on demand) — this lets a prospective customer or a new operator safely learn the kill switch and blast radius simulator against fake data before ever touching real agents.

### Interface contract this phase produces

- `check_and_reserve_spend()` and the Redis key names — Phase 10A's kill switch writes directly to `agent_status:{agent_id}`.
- The real `/ws/feed` message contract, identical to the frontend's mock — Phase 11 swaps the data source, not the shape.
- `is_sandbox` scoping convention, or the sandbox-schema decision — every later query in Phases 06/08/10 that touches `agents`/`transactions` must respect it.

### Acceptance criteria

- [ ] Concurrency test proves no double-spend past the cap under simultaneous requests
- [ ] A revoked agent is denied instantly without reaching the rule engine or ML scorer
- [ ] WebSocket client authenticated to org A never receives org B's events
- [ ] Sandbox data is verifiably isolated from real data (a query scoped to real data returns zero sandbox rows, and vice versa)
- [ ] `trigger-rogue` reliably reproduces the spike + 2 sub-agents every call

---

## PHASE 10 · GOVERNANCE — Advanced Governance Features

**Suggested model:** The strongest reasoning model you have access to. Consider running each of the 5 sub-phases as a separate session even with the same model.

Implement the backend for the five features that differentiate this product from a generic policy engine: the delegation-aware kill switch, the blast radius simulator, the policy dry-run sandbox, the hash-chained audit log, and NIST AI RMF compliance mapping. Correctness here matters more than in any other backend phase — these are the controls the whole product exists to provide.

### What this phase assumes

Every endpoint below already has an exact contract defined by Phase 04's frontend mocks (`frontend/src/mocks/handlers/governance.md`) — implement against that document, don't redesign it. Phases 06, 07, 09 provide the rule engine, RBAC, and Redis layer this phase builds on.

### 10A — Kill Switch

`POST /api/v1/agents/:id/kill?mode=node|subtree|fleet` — `admin` role required (Phase 07).

- `node`: revoke one agent (DB + `agent_status:{id}` in Redis + WS broadcast + audit row).
- `subtree`: a recursive CTE (`WITH RECURSIVE`, not N+1 application queries) revokes the target and every descendant atomically. Precision matters — a test on a 4+ level tree must prove it never touches siblings or the parent.
- `fleet`: revoke everything, same atomicity guarantees.
- Response: `{"revoked_agent_ids": [...], "propagation_ms": N}`. Target under 200ms for a subtree kill on a realistic tree size — profile if you don't hit it, don't just report the number you hoped for.

### 10B — Blast Radius Simulator

`POST /api/v1/agents/:id/simulate-exposure` — strictly read-only (a test must prove zero DB writes on any call). Computes worst-case dollar exposure from proposed (not current) permissions, with a documented formula and a breakdown in the response, matching the frontend's mock calculator's shape from Phase 04A.

### 10C — Policy Dry-Run Sandbox

`POST /api/v1/policies/:id/dry-run` — replays a proposed rule against historical transactions via `evaluate_rules()`, returns a before/after diff. Strictly non-mutating — test that DB state is byte-identical before and after a call.

### 10D — Hash-Chained Audit Log

Modify `write_audit()`'s internals (Phase 06C) to compute `this_hash = sha256(prev_hash + canonical_json(payload))` per row, genesis `prev_hash = '0'*64`, deterministic JSON serialization (`sort_keys=True`).

`GET /api/v1/audit/verify` walks the chain, returns `{"valid": bool}` or the exact break point on failure.

Test both a clean chain (`valid: true`) and a manually-tampered row (verify detection actually works — this is the entire point of the feature, don't skip this test).

### 10E — Compliance Mapping API

`GET /api/v1/compliance/nist-mapping` — serves the static GOVERN/MAP/MEASURE/MANAGE table (verify exact subcategory numbers against your own NIST AI RMF Playbook copy) matching the structure Phase 04C's frontend panel already expects.

### Interface contract this phase produces

- Full parity with `frontend/src/mocks/handlers/governance.md` — Phase 11 verifies every field name and status code matches exactly.

### Acceptance criteria

- [ ] Subtree kill precision test passes on a 4+ level tree
- [ ] Subtree kill on ~20 agents completes under 200ms locally
- [ ] Blast radius and dry-run both proven read-only/non-mutating by explicit test
- [ ] Hash chain verify catches a manually-tampered row and reports the exact break point
- [ ] Compliance endpoint matches the frontend's expected table structure exactly

---

## PHASE 11 · INTEGRATION — Frontend–Backend Integration

**Suggested model:** A full-stack-capable coding model or agentic tool; this phase requires reading both the frontend and backend code closely.

Replace every mock — MSW handlers, the local live-data generator, mock calculators — with real calls to the now-complete backend, without changing how any screen looks or behaves from the user's perspective.

### What this phase assumes

All ten prior phases are complete and each backend phase's interface contract matches what the corresponding frontend phase mocked. If any endpoint discovered here doesn't match, fix the mismatch by consulting whichever contract document is authoritative (the frontend's `mocks/handlers/*.md` files) rather than silently patching around it in a way that leaves the two out of sync for the next person.

### Work, screen by screen

- **Auth (Phase 02B ↔ 07):** replace the MSW auth handlers with real calls to `/api/v1/auth/*`; implement real token storage (httpOnly cookie or secure storage, not `localStorage` for anything sensitive) and silent refresh in `useAuth()`.
- **Dashboard & graph (Phase 03 ↔ 09B):** replace the local mock live-data generator with a real WebSocket connection to `/ws/feed`, including the reconnect-with-fresh-snapshot behavior the mock never had to handle for real.
- **Governance panels (Phase 04 ↔ 10):** replace every mock handler in `governance.md` with the real endpoint, one at a time, verifying the response shape actually matches before moving to the next.
- **Environment config:** introduce `frontend/.env.development` / `.env.production` for the API base URL and WS URL — nothing hardcoded to `localhost`.
- **Error handling:** every real network call must use the error state component from Phase 01C, not a raw unhandled promise rejection — a 401 specifically should trigger the auth refresh flow before falling back to a redirect to `/login`.

### Acceptance criteria

- [ ] MSW is fully removed from production builds (dev-only, behind an explicit flag) and every real endpoint is reachable
- [ ] A full login → dashboard → trigger a governance action → see it reflected live via WebSocket loop works end to end
- [ ] A WebSocket disconnect (kill the backend mid-session) triggers the reconnect UI and recovers automatically when the backend returns
- [ ] A 401 response triggers token refresh before falling back to logout, verified by test
- [ ] No hardcoded localhost URLs remain anywhere in the frontend build output

---

## PHASE 12 · DEVOPS — DevOps & Deployment

**Suggested model:** A backend/infrastructure-competent model; this phase can be done in parallel with Phase 13 by a second person.

Take the product from 'runs on a laptop' to 'runs reliably for real users' — containerization, CI/CD, and a real production deployment with secrets managed properly.

### 12A — Local Development & Containerization

- `docker-compose.dev.yml`: Postgres + Redis only (backend/frontend run natively via `make dev` for fast reload) — matches the `db-up` / `db-down` targets already in the project Makefile.
- `Dockerfile` for the backend (multi-stage: build deps, then a slim runtime image) and for the frontend (multi-stage: `npm run build`, then served via a minimal Nginx image).
- `docker-compose.prod.yml`: backend, frontend (via Nginx), Postgres, Redis, and a reverse proxy — matches the `docker-up` / `docker-build` Makefile targets.

### 12B — CI/CD

- GitHub Actions (or equivalent): on every PR — install, lint, run the full backend + frontend test suites (Phase 13A), fail the build on any failure.
- On merge to `main`: build and push Docker images, then trigger `deploy-staging` automatically; `deploy-prod` stays a manual, explicit trigger — never auto-deploy to production on merge for a product that controls real financial agent spend.

### 12C — Production Deployment & Secrets

- Environment separation: distinct `staging` and `production` environments with separate databases — never point staging at production data.
- Reverse proxy (Nginx or a managed load balancer) terminating TLS; the backend and Postgres/Redis are never directly internet-exposed.
- Secrets (DB credentials, JWT signing key, Redis auth) via environment variables injected at deploy time or a secrets manager — never committed to the repo, and `.env.example` (with placeholder values only) is the only env file that belongs in version control.
- A `/health` endpoint the deployment platform can poll, and structured logging (JSON logs, not print statements) so production issues are debuggable without SSHing into a container.
- `scripts/deploy.sh` implementing the `deploy-staging` / `deploy-prod` Makefile targets — the exact deployment mechanism (a PaaS, a VM, a container platform) is an infrastructure choice you make based on where you're hosting; document whichever one you pick here.

### Acceptance criteria

- [ ] `make docker-up` brings up a full prod-like stack from a clean checkout
- [ ] CI blocks a PR with a failing test or lint error
- [ ] Staging and production use fully separate databases and credentials
- [ ] No secret value exists in the git history — verified with a secrets-scanning tool before first public push
- [ ] `/health` returns quickly and reflects real DB/Redis connectivity, not just "the process is running"

---

## PHASE 13 · QA — Testing, QA & Production Hardening

**Suggested model:** Any strong coding model; this phase benefits most from being run after every other phase is functionally complete, not in parallel.

Verify the whole system holds together under real conditions — not just that each phase's own unit tests pass, but that the product is reliable, secure, and fast enough for real operators making real governance decisions.

### 13A — Automated Test Strategy

- **Unit tests** (per-phase, already specified in each phase's acceptance criteria) — this sub-phase's job is to confirm coverage is real, not just present: run a coverage report and flag any governance-critical path (kill switch, rule engine, audit hash chain) below a high bar.
- **Integration tests:** full request-response cycles against a real (test) database — not everything mocked — covering the complete transaction pipeline (Redis check → rule engine → risk scoring → decision → audit write → WS broadcast) as one path, not five isolated unit tests that never prove the pipeline actually connects.
- **End-to-end tests** (Playwright): the critical user journeys — sign up → log in → view dashboard → create a policy → dry-run it → trigger a sandbox rogue sequence → kill-switch it → verify the audit log — run against a real staging-like environment, not mocks.

### 13B — Security & Performance Hardening

- **Input validation:** every endpoint's Pydantic schemas reject malformed input with a clear 422, not a 500 — audit this specifically, it's the most common gap between "works in the demo" and "survives real traffic."
- **Rate limiting** on auth endpoints (login attempts) and on the transaction ingestion endpoint, to prevent both credential-stuffing and accidental self-inflicted denial of service from a misbehaving agent.
- **SQL injection / XSS review:** confirm every query goes through the ORM's parameterization (no raw string-interpolated SQL anywhere) and every user-supplied string rendered in the UI is escaped by default (React does this by default — audit specifically for any `dangerouslySetInnerHTML` usage and justify or remove each one).
- **Load testing:** simulate a realistic multi-agent transaction volume against the real pipeline and confirm the sub-200ms kill-switch and sub-100ms transaction-decision targets from earlier phases hold under load, not just in an empty local database.
- **Accessibility pass** on the frontend: keyboard navigation through every governance panel (an operator using the kill switch should never be forced to rely on a mouse), sufficient color contrast in both light and dark themes (re-check the Phase 01 token choices against WCAG AA specifically for the risk-score badge colors, which are meaning-bearing, not decorative).

### Acceptance criteria

- [ ] Coverage report shows high coverage specifically on kill switch, rule engine, and audit chain code paths
- [ ] Full E2E journey (signup through kill-switch through audit verify) passes against a staging-like environment
- [ ] Rate limiting verified by test (Nth login attempt in a window is rejected)
- [ ] No raw SQL string interpolation found in a full codebase audit
- [ ] Load test confirms latency targets hold at a realistic simulated transaction volume
- [ ] Every governance control is operable via keyboard alone

---

## Closing Notes — Putting It All Together

### Assembling the phases

Every phase's "Interface contract" section is the seam between it and whatever comes next. If two phases don't fit together when you combine them, the fix is almost always in one place: something invented a name, a field, or a response shape that an earlier phase's contract already fixed. Go back to that contract section and correct the drift there, rather than patching around it in both places.

### A note on scope

This plan intentionally includes things a hackathon version would skip — real authentication, multi-tenant data scoping, CI/CD, production secrets handling, load testing, accessibility. That's the actual difference between a demo and a website: not more features, but the same core features held to a higher bar of "still works when you're not in the room."

### Design references

Phase 01 asks you to draw on 21st.dev for specific hard-to-design components (bento grids, command palettes, animated counters, slide-over panels). Treat everything sourced from there as a starting point to re-theme, not a final answer — the product's visual identity is the token set defined in Phase 01, and every component, wherever its first draft came from, should end up looking like it was designed for Kavach specifically.
