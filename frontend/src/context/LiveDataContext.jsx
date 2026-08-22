import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { LiveDataContext } from './useLiveDataContext';
import { useAuth } from '@/hooks/useAuth';

const API = import.meta.env.VITE_API_BASE_URL || '';
const WS = import.meta.env.VITE_WS_BASE_URL || (location.protocol === 'https:' ? `wss://${location.host}` : `ws://${location.host}`);

function toAgent(agent) {
  return { id: agent.id, name: agent.name, type: agent.type, agentType: agent.type,
    trustScore: Math.round(Number(agent.trustScore || 0) * 100),
    active: agent.status !== 'revoked', cap: Number(agent.spendCapCurrent || 0),
    totalSpend: 0, parentId: agent.parentAgentId || null };
}

function toTransaction(tx, agents) {
  return { id: tx.id, agentId: tx.agentId, agentName: agents[tx.agentId]?.name || 'Unknown agent',
    amount: Number(tx.amount), merchantCategory: tx.merchantCategory, decision: tx.decision,
    riskScore: Math.round(Number(tx.riskScore || 0) * 100), timestamp: new Date(tx.timestamp).getTime() / 1000 };
}

export function LiveDataProvider({ children }) {
  const { session, accessToken, refresh: refreshSession } = useAuth();
  const [agents, setAgents] = useState({});
  const [transactions, setTransactions] = useState([]);
  const [pulsingIds, setPulsingIds] = useState(new Set());
  const [connected, setConnected] = useState(false);
  const token = accessToken || session?.accessToken;

  const request = useCallback(async (path, options = {}) => {
    const call = async (access) => fetch(`${API}${path}`, { ...options, headers: {
      'Content-Type': 'application/json', Authorization: `Bearer ${access}`, ...(options.headers || {}),
    }});
    let response = await call(token);
    if (response.status === 401 && session?.refreshToken) {
      const renewed = await refreshSession();
      response = await call(renewed);
    }
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.detail?.message || body.detail || body.error?.message || 'Request failed');
    return body;
  }, [token, session?.refreshToken, refreshSession]);

  const refresh = useCallback(async () => {
    if (!token) return;
    const agentRows = await request('/api/v1/agents');
    const nextAgents = Object.fromEntries(agentRows.map((agent) => [agent.id, toAgent(agent)]));
    const txRows = await request('/api/v1/transactions');
    setAgents(nextAgents);
    setTransactions(txRows.map((tx) => toTransaction(tx, nextAgents)).slice(0, 30));
  }, [token, request]);

  useEffect(() => { refresh().catch(() => {}); }, [refresh]);

  useEffect(() => {
    if (!token) return undefined;
    let socket; let retry;
    const connect = () => {
      socket = new WebSocket(`${WS}/ws/feed?token=${encodeURIComponent(token)}`);
      socket.onopen = () => setConnected(true);
      socket.onmessage = ({ data }) => {
        const message = JSON.parse(data);
        if (message.type === 'graph_snapshot') {
          const map = Object.fromEntries(message.payload.nodes.map((node) => [node.id, node]));
          setAgents(map);
        } else if (message.type === 'transaction_update') {
          setTransactions((items) => [message.payload, ...items].slice(0, 30));
          setPulsingIds((old) => new Set([...old, message.payload.agentId]));
          setTimeout(() => setPulsingIds((old) => { const next = new Set(old); next.delete(message.payload.agentId); return next; }), 1200);
        } else if (message.type === 'agent_status_update' || message.type === 'trust_score_update') {
          setAgents((old) => ({ ...old, [message.payload.agentId]: { ...old[message.payload.agentId], ...message.payload } }));
        }
      };
      socket.onclose = () => { setConnected(false); retry = setTimeout(connect, 1500); };
    };
    connect();
    return () => { clearTimeout(retry); socket?.close(); };
  }, [token]);

  const nodes = useMemo(() => Object.values(agents).map((agent) => ({ ...agent, label: agent.name?.split(' ').map((word) => word[0]).join(''), val: Math.max(2, agent.cap / 1000 * 4) })), [agents]);
  const edges = useMemo(() => nodes.filter((node) => node.parentId).map((node) => ({ id: `e_${node.parentId}_${node.id}`, source: node.parentId, target: node.id })), [nodes]);
  const stats = useMemo(() => {
    const active = nodes.filter((node) => node.active);
    return { totalAgents: nodes.length, activeAgents: active.length,
      avgTrustScore: active.length ? Math.round(active.reduce((sum, node) => sum + node.trustScore, 0) / active.length) : 0,
      maxBlastRadius: nodes.reduce((sum, node) => sum + (node.active ? node.cap : 0), 0), transactionsLastHour: transactions.length };
  }, [nodes, transactions]);
  const getAffectedAgents = useCallback((mode, targetId) => {
    if (mode === 'fleet') return Object.keys(agents);
    const ids = new Set([targetId]);
    if (mode === 'subtree') for (const id of ids) Object.values(agents).filter((agent) => agent.parentId === id).forEach((agent) => ids.add(agent.id));
    return [...ids].filter(Boolean);
  }, [agents]);
  const kill = useCallback(async (agentId, mode = 'node') => {
    const result = await request(`/api/v1/agents/${agentId}/kill?mode=${mode}`, { method: 'POST' });
    setAgents((old) => { const next = { ...old }; result.revokedAgentIds.forEach((id) => { if (next[id]) next[id] = { ...next[id], active: false }; }); return next; });
    return result;
  }, [request]);
  const computeExposure = useCallback((params) => request(`/api/v1/agents/${Object.keys(agents)[0]}/simulate-exposure`, { method: 'POST', body: JSON.stringify(params) }), [agents, request]);
  const dryRunPolicy = useCallback(async (conditions) => {
    const policies = await request('/api/v1/policies');
    if (!policies[0]) throw new Error('Create a policy before running a dry-run');
    return request(`/api/v1/policies/${policies[0].id}/dry-run`, { method: 'POST', body: JSON.stringify({ conditions }) });
  }, [request]);
  const data = { agents, nodes, edges, transactions, stats, pulsingIds, connected, txnRef: { current: transactions[0] }, refresh,
    killAgent: (id) => kill(id, 'node'), killSubtree: (id) => kill(id, 'subtree'), killFleet: () => kill(Object.keys(agents)[0], 'fleet'), getAffectedAgents, computeExposure, dryRunPolicy };
  return (
    <LiveDataContext.Provider value={data}>
      {children}
    </LiveDataContext.Provider>
  );
}
