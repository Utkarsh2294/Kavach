import React, { useRef, useCallback, useEffect, useState } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { agentNodeColor } from '@/mocks/livedata';

/* Resolve a token like 'var(--color-success-500)' to an actual rgb/hex value
   by reading the computed style on :root. Falls back to default hex values
   so the graph always renders even if the CSS variable is unavailable. */
const TOKEN_CACHE = {};
function resolveToken(token) {
  if (TOKEN_CACHE[token]) return TOKEN_CACHE[token];
  let value;
  if (typeof window !== 'undefined') {
    value = getComputedStyle(document.documentElement)
      .getPropertyValue(token.replace(/^var\(--(.*?)\)$/, '--$1'))
      .trim();
  }
  if (!value) {
    const fallback = {
      'var(--color-success-500)': '#10B981',
      'var(--color-warning-500)': '#F59E0B',
      'var(--color-danger-500)': '#EF4444',
      'var(--color-danger-400)': '#F87171',
      'var(--color-surface-500)': '#71717A',
      'var(--color-surface-100)': '#F4F4F5',
    };
    value = fallback[token] || '#A1A1AA';
  }
  TOKEN_CACHE[token] = value;
  return value;
}

function hexToRgba(hex, alpha) {
  const h = hex.replace('#', '');
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function nodeHex(node) {
  const token = node.color || agentNodeColor(node);
  return resolveToken(token);
}

export function DelegationGraph({
  nodes: incomingNodes,
  edges: incomingEdges,
  onNodeClick,
  pulsingIds,
  width,
  height,
  txnRef,
}) {
  const fgRef = useRef();
  const [hoveredNode, setHoveredNode] = useState(null);
  const [pointer, setPointer] = useState({ x: 0, y: 0 });

  /* Pulse edge state: edgeId -> remaining alpha */
  const edgePulse = useRef({});

  /* When a new transaction arrives, pulse the parent→child edge for that agent. */
  const lastTxnId = useRef(null);
  useEffect(() => {
    const id = setInterval(() => {
      const tx = txnRef?.current;
      if (!tx || tx.id === lastTxnId.current) return;
      lastTxnId.current = tx.id;
      const edgeId = findEdgeForAgent(incomingEdges, tx.agentId);
      if (edgeId) {
        edgePulse.current[edgeId] = 1;
      }
    }, 250);
    return () => clearInterval(id);
  }, [txnRef, incomingEdges]);

  /* Decay edge pulses every frame and repaint only while a pulse is active. */
  useEffect(() => {
    let raf;
    const loop = () => {
      const ep = edgePulse.current;
      for (const k of Object.keys(ep)) {
        ep[k] -= 0.035;
        if (ep[k] <= 0) delete ep[k];
      }
      if (Object.keys(ep).length > 0) {
        fgRef.current?.refresh?.();
        raf = requestAnimationFrame(loop);
      }
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  /* Link canvas drawer */
  const linkCanvasObject = useCallback((link, ctx) => {
    const start = link.source;
    const end = link.target;
    if (!start || !end || typeof start.x !== 'number' || typeof end.x !== 'number') return;

    const edgeId = link.id || `${start.id}_${end.id}`;
    const pulseAlpha = edgePulse.current[edgeId] || 0;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    if (pulseAlpha > 0) {
      ctx.strokeStyle = `rgba(167, 139, 250, ${pulseAlpha})`;
      ctx.lineWidth = 3;
    } else {
      ctx.strokeStyle = resolveToken('var(--color-surface-500)');
      ctx.lineWidth = 1.5;
    }
    ctx.stroke();
    ctx.restore();
  }, []);

  /* Node canvas drawer */
  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    const { x, y } = node;
    if (x === undefined || y === undefined) return;
    const size = Math.max(5, node.val * 0.55);
    const hex = nodeHex(node);
    const isPulsing = node.isPulsing || pulsingIds?.has(node.id);

    /* Pulsing ring */
    if (isPulsing) {
      ctx.save();
      const t = (Date.now() % 1200) / 1200;
      const ringR = size * (1.4 + t * 1.5);
      ctx.beginPath();
      ctx.arc(x, y, ringR, 0, 2 * Math.PI);
      ctx.strokeStyle = hexToRgba(hex, 1 - t);
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();
    }

    /* Body */
    ctx.save();
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI);
    ctx.fillStyle = hex;
    ctx.fill();

    /* Gloss highlight */
    const grad = ctx.createRadialGradient(
      x - size * 0.3, y - size * 0.3, 0,
      x, y, size
    );
    grad.addColorStop(0, 'rgba(255,255,255,0.35)');
    grad.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.restore();

    /* Label */
    if (globalScale > 0.6) {
      ctx.save();
      ctx.font = `${Math.max(9, 11 / globalScale)}px Inter, sans-serif`;
      ctx.fillStyle = resolveToken('var(--color-surface-100)');
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(node.label || node.name, x, y + size + 3);
      ctx.restore();
    }

    /* Revoked marker — X overlay */
    if (!node.active) {
      ctx.save();
      ctx.strokeStyle = 'rgba(0,0,0,0.6)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(x - size * 0.5, y - size * 0.5);
      ctx.lineTo(x + size * 0.5, y + size * 0.5);
      ctx.moveTo(x + size * 0.5, y - size * 0.5);
      ctx.lineTo(x - size * 0.5, y + size * 0.5);
      ctx.stroke();
      ctx.restore();
    }
  }, [pulsingIds]);

  const handleNodeHover = useCallback((node) => {
    setHoveredNode(node || null);
  }, []);

  const handleNodeDragEnd = useCallback((node) => {
    node.fx = node.x;
    node.fy = node.y;
  }, []);

  /* Configure forces once data arrives */
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    fg.d3Force('charge')?.strength?.(-280);
    fg.d3Force('link')?.distance?.((d) => 70 + (d.source.val + d.target.val) * 2.5);
    fg.d3Force('center')?.strength?.(0.04);
    fg.d3VelocityDecay?.(0.3);
  }, [incomingNodes.length]);

  /* Continuously repaint so the pulsing rings animate */
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    let raf;
    const tick = () => {
      fg.refresh?.();
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div
      className="relative w-full h-full"
      onMouseMove={(e) => setPointer({ x: e.nativeEvent.offsetX, y: e.nativeEvent.offsetY })}
    >
      <ForceGraph2D
        ref={fgRef}
        graphData={{ nodes: incomingNodes, links: incomingEdges }}
        width={width}
        height={height}
        nodeCanvasObject={nodeCanvasObject}
        linkCanvasObject={linkCanvasObject}
        onNodeClick={onNodeClick}
        onNodeHover={handleNodeHover}
        onNodeDragEnd={handleNodeDragEnd}
        nodePointerAreaPaint={(node, color, ctx) => {
          const size = Math.max(8, node.val * 0.55);
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
          ctx.fill();
        }}
        linkPointerAreaPaint={(link, color, ctx) => {
          ctx.strokeStyle = color;
          ctx.lineWidth = 6;
          ctx.beginPath();
          ctx.moveTo(link.source.x, link.source.y);
          ctx.lineTo(link.target.x, link.target.y);
          ctx.stroke();
        }}
        backgroundColor="rgba(0,0,0,0)"
        cooldownTicks={120}
        enableZoomInteraction
        enablePanInteraction
        enableNodeDrag
      />
      {hoveredNode && (
        <GraphTooltip node={hoveredNode} pointer={pointer} />
      )}
    </div>
  );
}

function GraphTooltip({ node, pointer }) {
  const hex = nodeHex(node);
  return (
    <div
      className="absolute z-50 p-3 rounded-lg border border-border bg-popover text-popover-foreground shadow-md text-xs space-y-1.5 pointer-events-none"
      style={{ left: pointer.x + 14, top: pointer.y + 14 }}
    >
      <div className="font-semibold text-foreground flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: hex }} />
        {node.name}
      </div>
      <div className="text-muted-foreground capitalize">{node.agentType} · {node.role}</div>
      <div className="flex justify-between gap-6">
        <span className="text-muted-foreground">Trust</span>
        <span style={{ color: hex }}>{Math.round(node.trustScore)}%</span>
      </div>
      <div className="flex justify-between gap-6">
        <span className="text-muted-foreground">Spend</span>
        <span className="text-foreground font-mono">
          ${(node.totalSpend || 0).toFixed(0)} / ${(node.cap || 0).toLocaleString()}
        </span>
      </div>
    </div>
  );
}

function findEdgeForAgent(edges, agentId) {
  for (const e of edges) {
    const src = typeof e.source === 'string' ? e.source : e.source?.id;
    const tgt = typeof e.target === 'string' ? e.target : e.target?.id;
    if (tgt === agentId) return `e_${src}_${tgt}`;
  }
  return null;
}
