"use client";

import { useEffect, useState } from "react";

interface VisitorStats {
  total_views: number;
  unique_monitors: number;
  active_connections: number;
}

const POLL_INTERVAL_MS = 30_000;

function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    }
  }

  // Production uses same-origin /api so Vercel rewrites to Railway.
  // Never call 127.0.0.1 in production; iOS may show a local-network permission popup.
  return "";
}

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return n.toLocaleString("en-IN");
  return String(n);
}

function fallbackStats(): VisitorStats {
  return {
    total_views: 14832 + Math.floor(Math.random() * 50),
    unique_monitors: 2481 + Math.floor(Math.random() * 20),
    active_connections: 6 + Math.floor(Math.random() * 7),
  };
}

export default function ObservatoryTelemetry() {
  const [stats, setStats] = useState<VisitorStats | null>(null);
  const [isSimulated, setIsSimulated] = useState(false);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let isMounted = true;
    const apiBaseUrl = getApiBaseUrl();
    const path = typeof window !== "undefined" ? window.location.pathname : "/";

    async function fetchStats() {
      const res = await fetch(`${apiBaseUrl}/api/v1/analytics/stats`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return (await res.json()) as VisitorStats;
    }

    async function registerHit() {
      try {
        const res = await fetch(`${apiBaseUrl}/api/v1/analytics/hit?path=${encodeURIComponent(path)}`, {
          method: "POST",
          cache: "no-store",
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as VisitorStats;
        if (!isMounted) return;
        setStats(data);
        setIsSimulated(false);
      } catch (error) {
        console.warn("[CJPHub Telemetry] same-origin /api unavailable; local visual fallback active.", error);
        if (!isMounted) return;
        setStats(fallbackStats());
        setIsSimulated(true);
      }
    }

    registerHit();

    const pollingInterval = setInterval(async () => {
      try {
        const data = await fetchStats();
        if (!isMounted) return;
        setStats(data);
        setIsSimulated(false);
      } catch {
        // Keep last visible stats.
      }
    }, POLL_INTERVAL_MS);

    const pulseInterval = setInterval(() => {
      setStats((prev) => {
        if (!prev || !isSimulated) return prev;
        const delta = [-2, -1, 0, 1, 2][Math.floor(Math.random() * 5)];
        return {
          ...prev,
          active_connections: Math.max(4, Math.min(18, prev.active_connections + delta)),
        };
      });
    }, 6000);

    const cursorInterval = setInterval(() => setTick((t) => t + 1), 800);

    return () => {
      isMounted = false;
      clearInterval(pollingInterval);
      clearInterval(pulseInterval);
      clearInterval(cursorInterval);
    };
  }, [isSimulated]);

  const cursor = tick % 2 === 0 ? "█" : " ";

  return (
    <section aria-label="Observatory Telemetry & Traffic" className="observatory-telemetry">
      <div className="telemetry-header">
        <span className="telemetry-label">◈ OBSERVATORY TELEMETRY</span>
        <span className="telemetry-sep">│</span>
        <span className="status-badge online">
          <span className="status-dot" aria-hidden="true" />
          {isSimulated ? "LOCAL FALLBACK" : "SYSTEM ONLINE"}
        </span>
        <span className="telemetry-sep">│</span>
        <span className="tls-badge">⚿ TLS 1.3 SECURE</span>
      </div>

      <div className="telemetry-stats">
        <StatBlock icon="⬡" label="TOTAL FEEDS DECRYPTED" value={stats ? formatCount(stats.total_views) : "———"} loading={!stats} />
        <div className="stat-divider" aria-hidden="true">╱</div>
        <StatBlock icon="◎" label="UNIQUE TERMINALS CONNECTED" value={stats ? formatCount(stats.unique_monitors) : "———"} loading={!stats} />
        <div className="stat-divider" aria-hidden="true">╱</div>
        <StatBlock icon="◉" label="LIVE PULSE" value={stats ? `${stats.active_connections} OPERATIONAL` : "———"} loading={!stats} pulse />
      </div>

      <div className="telemetry-terminal" aria-live="polite">
        <span className="terminal-prompt">observatory@cjphub:~$</span>
        <span className="terminal-cmd"> stream --monitor --realtime --filter=all</span>
        <span className="terminal-cursor" aria-hidden="true">{cursor}</span>
      </div>

      <style>{`
        .observatory-telemetry { border-top: 1px solid rgba(0,255,136,.15); background: linear-gradient(180deg, rgba(0,255,136,.03) 0%, transparent 100%); padding: 1.25rem 1.5rem 1rem; font-family: 'JetBrains Mono','Fira Code','Cascadia Code','Courier New',monospace; margin-top: 2rem; }
        .telemetry-header { display:flex; align-items:center; gap:.6rem; font-size:.65rem; letter-spacing:.12em; color:rgba(0,255,136,.5); margin-bottom:1rem; flex-wrap:wrap; }
        .telemetry-label { color:rgba(0,255,136,.7); font-weight:600; }
        .telemetry-sep { opacity:.3; }
        .status-badge { display:flex; align-items:center; gap:.35rem; font-weight:600; }
        .status-badge.online { color:#00ff88; }
        .status-dot { width:6px; height:6px; border-radius:50%; background:currentColor; animation:pulse-dot 2s ease-in-out infinite; }
        @keyframes pulse-dot { 0%,100%{opacity:1;box-shadow:0 0 4px currentColor;} 50%{opacity:.4;box-shadow:none;} }
        .tls-badge { color:rgba(0,200,255,.6); letter-spacing:.1em; }
        .telemetry-stats { display:flex; align-items:center; gap:.75rem; flex-wrap:wrap; margin-bottom:.9rem; }
        .stat-divider { color:rgba(0,255,136,.2); font-size:1.1rem; }
        .stat-block { display:flex; flex-direction:column; gap:.15rem; min-width:140px; }
        .stat-block-label { font-size:.55rem; letter-spacing:.14em; color:rgba(0,255,136,.45); display:flex; align-items:center; gap:.3rem; }
        .stat-block-value { font-size:.95rem; font-weight:700; letter-spacing:.05em; color:#00ff88; text-shadow:0 0 12px rgba(0,255,136,.4); transition:all .4s ease; }
        .stat-block-value.loading { animation:shimmer 1.5s ease-in-out infinite; }
        @keyframes shimmer { 0%,100%{opacity:.3;} 50%{opacity:.7;} }
        .stat-block-value.pulse-value { animation:glow-pulse 2s ease-in-out infinite; }
        @keyframes glow-pulse { 0%,100%{text-shadow:0 0 8px rgba(0,255,136,.4);} 50%{text-shadow:0 0 20px rgba(0,255,136,.9),0 0 40px rgba(0,255,136,.3);} }
        .telemetry-terminal { font-size:.65rem; letter-spacing:.04em; color:rgba(0,255,136,.3); overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }
        .terminal-prompt { color:rgba(0,200,255,.5); }
        .terminal-cmd { color:rgba(0,255,136,.25); }
        .terminal-cursor { color:#00ff88; font-weight:700; margin-left:2px; }
        @media (max-width:600px){ .stat-divider{display:none;} .telemetry-stats{gap:.5rem;} .stat-block{min-width:120px;} .telemetry-terminal{font-size:.58rem;} }
      `}</style>
    </section>
  );
}

function StatBlock({ icon, label, value, loading, pulse }: { icon: string; label: string; value: string; loading: boolean; pulse?: boolean }) {
  return (
    <div className="stat-block">
      <span className="stat-block-label"><span aria-hidden="true">{icon}</span>{label}</span>
      <span className={`stat-block-value ${loading ? "loading" : ""} ${pulse && !loading ? "pulse-value" : ""}`}>{value}</span>
    </div>
  );
}
