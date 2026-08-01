import React, { useState, useEffect, useRef } from 'react';

export function AnimatedCounter({ value, durationMs = 450, prefix = '', suffix = '', decimals = 0, className = '' }) {
  const [display, setDisplay] = useState(value);
  const [animKey, setAnimKey] = useState(0);
  const prevValue = useRef(value);
  const rafRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    const from = prevValue.current;
    const to = value;
    prevValue.current = to;
    if (from === to) return;
    setAnimKey(k => k + 1);

    startRef.current = null;

    const step = (ts) => {
      if (startRef.current === null) startRef.current = ts;
      const elapsed = (ts - startRef.current) / 1000;
      const progress = Math.min(elapsed / (durationMs / 1000), 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(from + (to - from) * eased);
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(step);
      }
    };

    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [value, durationMs]);

  const formatted = decimals > 0
    ? parseFloat(display).toFixed(decimals)
    : Math.round(display).toLocaleString();

  return (
    <span key={animKey} className={`animate-number-pop inline-block ${className}`}>
      {prefix}{formatted}{suffix}
    </span>
  );
}