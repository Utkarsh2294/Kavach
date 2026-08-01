# Governance API Contract

Phase 04 implements these mock endpoints in-memory via the `useLiveData` context. Phases 06 and 10 implement them for real against Postgres/Redis. Every field name and response shape here is binding.

---

## `POST /api/v1/agents/:id/kill?mode=node|subtree|fleet`

Kill-switch revocation. Requires `admin` role (Phase 07).

### Request

```
POST /api/v1/agents/:id/kill?mode=node
```

| Query param | Type | Values |
|---|---|---|
| `mode` | string | `node`, `subtree`, `fleet` |

### Response 200

```json
{
  "revokedAgentIds": ["agent_002"],
  "propagationMs": 42,
  "mode": "node",
  "timestamp": "2026-08-01T12:00:00Z"
}
```

### Response 403

```json
{ "error": "Forbidden — admin role required" }
```

---

## `POST /api/v1/agents/:id/simulate-exposure`

Blast radius simulation — strictly read-only (zero DB writes).

### Request body

```json
{
  "spendCap": 10000,
  "maxSubAgents": 5,
  "maxDelegationDepth": 3
}
```

### Response 200

```json
{
  "worstCaseDollarExposure": 160000,
  "breakdown": {
    "rootCap": 10000,
    "maxSubAgentsPerLevel": 5,
    "maxDelegationDepth": 3,
    "totalNodesWorstCase": 16,
    "formulaExplained": "10000 × (1 + 5 sub-agents × 3 delegation depth)"
  }
}
```

---

## `POST /api/v1/policies/:id/dry-run`

Policy dry-run sandbox — strictly non-mutating. Replays a proposed rule JSON against historical transactions.

### Request body

```json
{
  "conditions": [
    { "field": "amount", "op": "<=", "value": 250 }
  ]
}
```

### Response 200

```json
{
  "beforeAfterDiff": [
    {
      "txId": "txn_00035",
      "agentName": "Payment Gateway",
      "amount": 342.50,
      "merchantCategory": "SaaS License",
      "riskScore": 28,
      "before": "approve",
      "after": "deny",
      "triggered": true
    }
  ],
  "summary": {
    "newlyBlocked": 3,
    "newlyAllowed": 1,
    "unchanged": 16
  }
}
```

---

## `GET /api/v1/audit/verify`

Hash-chain integrity verification.

### Response 200 (clean chain)

```json
{
  "valid": true,
  "recordsVerified": 42,
  "breaks": []
}
```

### Response 200 (tampered)

```json
{
  "valid": false,
  "recordsVerified": 42,
  "breaks": [
    {
      "recordId": 12,
      "expectedHash": "a1b2c3...",
      "actualHash": "zz99..."
    }
  ]
}
```

---

## `GET /api/v1/compliance/nist-mapping`

NIST AI RMF compliance mapping — static data.

### Response 200

```json
{
  "mappings": [
    {
      "category": "GOVERN",
      "description": "Policies and processes to oversee AI system life cycles",
      "subcategories": ["Policy Establishment (GOVERN 1.1)", "Accountability (GOVERN 1.2)", "Training & Culture (GOVERN 2)"]
    },
    {
      "category": "MAP",
      "description": "Establish the context of the AI system",
      "subcategories": ["System Mapping (MAP 1.1)", "Risk Identification (MAP 2.1)"]
    },
    {
      "category": "MEASURE",
      "description": "Assess & quantify risk",
      "subcategories": ["Bias & Accuracy (MEASURE 1.1)", "Performance Monitoring (MEASURE 3.1)"]
    },
    {
      "category": "MANAGE",
      "description": "Treat and control risk",
      "subcategories": ["Incident Response (MANAGE 1.1)", "Explainability (MANAGE 2.1)"]
    }
  ]
}
```

---

## `GET /api/v1/escalations` | `POST /api/v1/escalations/:id`

Human-review escalation queue.

### GET Response 200

```json
{
  "items": [
    {
      "id": "esc_001",
      "transactionId": "txn_00053",
      "agentName": "Refund Handler",
      "amount": 189.00,
      "merchantCategory": "Data Transfer",
      "riskScore": 62,
      "status": "pending",
      "reviewedBy": null,
      "reviewedAt": null
    }
  ]
}
```

### POST /api/v1/escalations/:id — action body

```json
{
  "action": "approve",
  "adjustedCapAmount": null
}
```

```json
{
  "action": "adjust_cap",
  "adjustedCapAmount": 800
}
```

### POST Response 200

```json
{
  "id": "esc_001",
  "status": "approved",
  "reviewedAt": "2026-08-01T12:05:00Z"
}
```