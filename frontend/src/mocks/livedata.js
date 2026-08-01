import { useState, useEffect, useCallback, useRef } from 'react';

/* ------------------------------------------------------------------ */
/*  Risk-score → color mapping (shared utility — exported for reuse)  */
/* ------------------------------------------------------------------ */
export const RISK_LEVELS = {
  LOW: { min: 0, max: 29, color: 'var(--color-success-500)', label: 'Low' },
  MID: { min: 30, max: 59, color: 'var(--color-warning-500)', label: 'Mid' },
  HIGH: { min: 60, max: 84, color: 'var(--color-danger-400)', label: 'High' },
  CRITICAL: { min: 85, max: 100, color: 'var(--color-danger-500)', label: 'Critical' },
};

export function riskScoreToLevel(score) {
  if (score <= RISK_LEVELS.LOW.max) return 'LOW';
  if (score <= RISK_LEVELS.MID.max) return 'MID';
  if (score <= RISK_LEVELS.HIGH.max) return 'HIGH';
  return 'CRITICAL';
}

export function riskScoreToColor(score) {
  return RISK_LEVELS[riskScoreToLevel(score)].color;
}

export function riskScoreToBadgeVariant(score) {
  const level = riskScoreToLevel(score);
  if (level === 'LOW' || level === 'MID') return 'warning';
  return 'danger';
}

/* ------- agent node color: green/amber/red/grey  ------- */
export function agentNodeColor(agent) {
  if (!agent.active) return 'var(--color-surface-500)';
  if (agent.trustScore >= 80) return 'var(--color-success-500)';
  if (agent.trustScore >= 50) return 'var(--color-warning-500)';
  return 'var(--color-danger-500)';
}

export function agentStatusLabel(agent) {
  if (!agent.active) return 'revoked';
  if (agent.trustScore >= 80) return 'active';
  if (agent.trustScore >= 50) return 'degraded';
  return 'critical';
}

export function decisionBadgeVariant(decision) {
  if (decision === 'approve') return 'success';
  if (decision === 'deny') return 'danger';
  return 'warning'; // escalate
}

/* ------------------------------------------------------------------ */
/*  Static seed data                                                   */
/* ------------------------------------------------------------------ */
let uid = 1;
const MAKE_ID = () => `agent_${String(uid++).padStart(3, '0')}`;

const seedAgents = [
  { id: 'root',      name: 'Root Orchestrator', type: 'orchestrator', trustScore: 98, role: 'owner',     parentId: null,     cap: 50000, totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Core Auth Broker',   type: 'auth',         trustScore: 95, role: 'broker',    parentId: 'root',   cap: 10000, totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Payment Gateway',    type: 'payment',      trustScore: 88, role: 'broker',    parentId: 'root',   cap: 7500,  totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Data Warehouse',     type: 'storage',      trustScore: 92, role: 'broker',    parentId: 'root',   cap: 3000,  totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Bill Processor',     type: 'payment',      trustScore: 90, role: 'worker',    parentId: 'agent_002', cap: 2500,  totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Refund Handler',     type: 'payment',      trustScore: 76, role: 'worker',    parentId: 'agent_002', cap: 1500,  totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Login Sentinel',     type: 'auth',         trustScore: 97, role: 'worker',    parentId: 'agent_001', cap: 500,   totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'MFA Guardian',       type: 'auth',         trustScore: 94, role: 'worker',    parentId: 'agent_007', cap: 500,   totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Audit Archiver',     type: 'storage',      trustScore: 100, role: 'worker',   parentId: 'agent_003', cap: 1000,  totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Export Service',     type: 'storage',      trustScore: 45, role: 'worker',    parentId: 'agent_003', cap: 2000,  totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Fraud Committee',    type: 'compliance',   trustScore: 60, role: 'committee', parentId: 'agent_002', cap: 3000,  totalSpend: 0, active: true },
  { id: MAKE_ID(),   name: 'Rate Limiter',       type: 'auth',         trustScore: 82, role: 'worker',    parentId: 'agent_001', cap: 800,   totalSpend: 0, active: true },
];

const MERCHANT_CATEGORIES = [
  'Cloud Compute', 'SaaS License', 'API Gateway', 'Storage', 'Data Transfer',
  'Monitoring', 'Security Audit', 'Compliance Check', 'ML Training', 'CDN Cache',
];

let txnSeq = 0;

function makeTransaction(agent) {
  const amount = +(Math.random() * agent.cap * 0.25 + 0.5).toFixed(2);
  const riskScore = Math.floor(Math.random() * 100);
  const decision = riskScore > 80 ? (Math.random() > 0.5 ? 'deny' : 'escalate') : 'approve';

  return {
    id: `txn_${String(++txnSeq).padStart(5, '0')}`,
    agentId: agent.id,
    agentName: agent.name,
    amount,
    merchantCategory: MERCHANT_CATEGORIES[Math.floor(Math.random() * MERCHANT_CATEGORIES.length)],
    decision,
    riskScore,
    timestamp: Date.now() / 1000,
  };
}

function driftTrustScore(agent) {
  if (!agent.active) return agent.trustScore;
  return Math.max(0, Math.min(100, agent.trustScore + (Math.random() * 8 - 4)));
}

/* ------------------------------------------------------------------ */
/*  The shared live-data provider hook                                 */
/* ------------------------------------------------------------------ */
export function useLiveData({ tickMs = 2200 } = {}) {
  const [agentMap, setAgentMap] = useState(() => {
    const m = {};
    for (const a of seedAgents) m[a.id] = { ...a };
    return m;
  });
  const [transactionLog, setTransactionLog] = useState([]);
  const [pulsing, setPulsing] = useState(new Set());

  const agentsRef = useRef(agentMap);
  agentsRef.current = agentMap;

  const lastTxRef = useRef(null);

  /* Central tick: drift trust + emit a transaction */
  useEffect(() => {
    const id = setInterval(() => {
      setAgentMap(prev => {
        const next = {};
        for (const k of Object.keys(prev)) {
          next[k] = { ...prev[k], trustScore: driftTrustScore(prev[k]) };
        }
        // Spend update from last transaction
        const lastTx = lastTxRef.current;
        if (lastTx && lastTx.decision === 'approve' && next[lastTx.agentId]) {
          next[lastTx.agentId] = {
            ...next[lastTx.agentId],
            totalSpend: next[lastTx.agentId].totalSpend + lastTx.amount,
          };
        }
        return next;
      });

      // Generate a transaction from a random active agent
      const activeIds = Object.keys(agentsRef.current).filter(k => agentsRef.current[k].active);
      if (activeIds.length) {
        const agentId = activeIds[Math.floor(Math.random() * activeIds.length)];
        const agent = agentsRef.current[agentId];
        const tx = makeTransaction(agent);
        setTransactionLog(prev => {
          const next = [...prev, tx];
          if (next.length > 30) next.shift();
          return next;
        });
        lastTxRef.current = tx;

        // Pulsing effect
        setPulsing(prev => new Set([...prev, agentId]));
        setTimeout(() => {
          setPulsing(prev => {
            const n = new Set(prev);
            n.delete(agentId);
            return n;
          });
        }, 3000);
      }
    }, tickMs);

    return () => clearInterval(id);
  }, [tickMs]);

  /* Derived graph data */
  const agentsList = Object.values(agentMap);

  const edges = agentsList
    .filter(a => a.parentId)
    .map(a => ({
      id: `e_${a.parentId}_${a.id}`,
      source: a.parentId,
      target: a.id,
    }));

  const nodes = agentsList.map(a => ({
    id: a.id,
    name: a.name,
    label: a.name.split(' ').map(w => w[0]).join(''), // short label for graph
    agentType: a.type,
    role: a.role,
    trustScore: a.trustScore,
    active: a.active,
    cap: a.cap,
    totalSpend: a.totalSpend,
    parentId: a.parentId,
    val: Math.max(2, (a.cap / 1000) * 4),
    color: agentNodeColor(a),
    isPulsing: pulsing.has(a.id),
  }));

  /* Summary stats */
  const stats = (() => {
    const activeAgents = agentsList.filter(a => a.active);
    const avgTrust = activeAgents.length
      ? Math.round(activeAgents.reduce((s, a) => s + a.trustScore, 0) / activeAgents.length)
      : 0;

    let maxBlast = 0;
    for (const a of agentsList) {
      if (!a.parentId && a.active) {
        const total = computeDescCap(agentMap, a.id);
        if (total > maxBlast) maxBlast = total;
      }
    }

    return {
      totalAgents: agentsList.length,
      activeAgents: activeAgents.length,
      avgTrustScore: avgTrust,
      maxBlastRadius: maxBlast,
      transactionsLastHour: transactionLog.length,
    };
  })();

  /* Kill / revoke mock handlers */
  const killAgent = useCallback((agentId) => {
    setAgentMap(prev => {
      if (!prev[agentId]) return prev;
      return { ...prev, [agentId]: { ...prev[agentId], active: false } };
    });
  }, []);

  const killSubtree = useCallback((rootId) => {
    setAgentMap(prev => {
      const next = { ...prev };
      const ids = getDescendantIds(prev, rootId);
      for (const id of ids) next[id] = { ...next[id], active: false };
      return next;
    });
  }, []);

  const killFleet = useCallback(() => {
    setAgentMap(prev => {
      const next = {};
      for (const k of Object.keys(prev)) {
        next[k] = { ...prev[k], active: false };
      }
      return next;
    });
  }, []);

  const getAffectedAgents = useCallback((mode, targetId) => {
    const map = agentsRef.current;
    if (mode === 'fleet') return Object.keys(map);
    if (mode === 'node' && map[targetId]) return [targetId];
    if (mode === 'subtree') return getDescendantIds(map, targetId);
    return [];
  }, []);

  const computeExposure = useCallback((params = {}) => {
    const { spendCap = 10000, maxSubAgents = 5, maxDelegationDepth = 3 } = params;
    const worstCase = spendCap * (1 + maxSubAgents * maxDelegationDepth);
    return {
      worstCaseDollarExposure: worstCase,
      breakdown: {
        rootCap: spendCap,
        maxSubAgentsPerLevel: maxSubAgents,
        maxDelegationDepth,
        totalNodesWorstCase: 1 + maxSubAgents * maxDelegationDepth,
        formulaExplained: `${spendCap} × (1 + ${maxSubAgents} sub-agents × ${maxDelegationDepth} delegation depth)`,
      },
    };
  }, []);

  /* Dry-run evaluation mock */
  const dryRunPolicy = useCallback((policyConditions) => {
    return transactionLog.slice(-20).map(tx => {
      const before = tx.decision;
      let after;
      let triggered = false;
      for (const c of (policyConditions || [])) {
        const value = tx[c.field];
        let match = false;
        if (c.op === '<=') match = value <= c.value;
        else if (c.op === '>') match = value > c.value;
        else if (c.op === '==') match = value === c.value;
        else if (c.op === '!=') match = value !== c.value;
        else if (c.op === 'in') match = Array.isArray(c.value) && c.value.includes(value);
        if (match) { triggered = true; break; }
      }
      after = before === 'approve' && triggered ? 'deny' : before === 'deny' && !triggered ? 'approve' : before;
      return { ...tx, before, after, triggered };
    });
  }, [transactionLog]);

  return {
    agents: agentMap,
    nodes,
    edges,
    transactions: transactionLog,
    stats,
    pulsingIds: pulsing,
    txnRef: lastTxRef,
    killAgent,
    killSubtree,
    killFleet,
    reviveAgent,
    getAffectedAgents,
    computeExposure,
    dryRunPolicy,
  };
}

function getDescendantIds(map, rootId) {
  const ids = new Set([rootId]);
  const stack = [rootId];
  while (stack.length) {
    const id = stack.pop();
    for (const a of Object.values(map)) {
      if (a.parentId === id) {
        ids.add(a.id);
        stack.push(a.id);
      }
    }
  }
  return [...ids];
}

function computeDescCap(map, rootId) {
  let total = 0;
  const stack = [rootId];
  while (stack.length) {
    const id = stack.pop();
    for (const a of Object.values(map)) {
      if (a.parentId === id && a.active) {
        total += a.cap;
        stack.push(a.id);
      }
    }
  }
  return total + (map[rootId]?.active ? map[rootId].cap : 0);
}