# Live Data Message Contract

This document defines the shape of all real-time messages consumed by the delegation graph and operator dashboard. The `useLiveData` hook in `livedata.js` currently simulates these internally; Phase 09B will replace the simulation with a real WebSocket emitting these exact shapes.

---

## `transaction_update`

Emitted when an agent initiates or completes a transaction.

```json
{
  "type": "transaction_update",
  "payload": {
    "id": "txn_00001",
    "agentId": "agent_002",
    "agentName": "Payment Gateway",
    "amount": 342.50,
    "merchantCategory": "SaaS License",
    "decision": "approve",
    "riskScore": 28,
    "timestamp": 1753987200.0
  }
}
```

| Field | Type | Notes |
|---|---|---|
| `decision` | `"approve" \| "deny" \| "escalate"` | Color-coded on dashboard as success / danger / warning |
| `riskScore` | `0-100` integer | Mapped through `riskScoreToBadgeVariant` for UI |

---

## `agent_status_update`

Emitted when an agent's trust score, active status, or cap changes.

```json
{
  "type": "agent_status_update",
  "payload": {
    "agentId": "agent_003",
    "trustScore": 76,
    "active": true,
    "cap": 2500,
    "totalSpend": 1203.10
  }
}
```

---

## `trust_score_update`

Lightweight alias for score-only drift — for high-frequency streaming.

```json
{
  "type": "trust_score_update",
  "payload": {
    "agentId": "agent_005",
    "trustScore": 88
  }
}
```

---

## `graph_snapshot`

Full delegation tree snapshot — sent on initial connect and after structural changes.

```json
{
  "type": "graph_snapshot",
  "payload": {
    "nodes": [
      {
        "id": "root",
        "name": "Root Orchestrator",
        "agentType": "orchestrator",
        "trustScore": 98,
        "active": true,
        "cap": 50000,
        "totalSpend": 0,
        "parentId": null
      }
    ],
    "edges": [
      {
        "id": "e_root_agent_001",
        "source": "root",
        "target": "agent_001"
      }
    ]
  }
}
```

---

## Status→Color Convention

All node colors derive from the shared mapping in `livedata.js`:

| Agent State | Condition | Color |
|---|---|---|
| Active (high trust) | `trustScore >= 80` | `var(--color-success-500)` #10B981 |
| Degraded | `trustScore >= 50` | `var(--color-warning-500)` #F59E0B |
| Critical / Low trust | `trustScore < 50` | `var(--color-danger-500)` #EF4444 |
| Revoked / Inactive | `active === false` | `var(--color-surface-500)` #71717A |

---

## Risk Score → Badge Convention

| Level | Range | Badge Variant | Color |
|---|---|---|---|
| LOW | 0-29 | `warning` (amber) | `var(--color-warning-500)` |
| MID | 30-59 | `warning` (amber) | `var(--color-warning-500)` |
| HIGH | 60-84 | `danger` | `var(--color-danger-400)` |
| CRITICAL | 85-100 | `danger` | `var(--color-danger-500)` |

Note: The badge variant uses **amber** for both Low and Mid scores in the live feed row to avoid information overload (green badges don't stand out in a scrolling list). This is a UX convention, not a semantic convention. For true semantic color mapping, use `riskScoreToColor`.