import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Clock, Cpu, HardDrive } from "lucide-react";
import { getMetrics } from "../../api";

const POLL_MS = 4000;

const AGENT_COLORS = {
  "Account Agent": "#3b5bdb",
  "Transaction Agent": "#1a9c5b",
  "Service Agent": "#b3791d",
};
const UNCLASSIFIED_COLOR = "#8b95a8"; // "unknown" intent — no sub-agent ran

function StatTile({ icon: Icon, label, value, sub }) {
  return (
    <div className="rounded-xl2 border border-navy-100 bg-white p-4 shadow-card">
      <div className="flex items-center gap-1.5 text-xs font-medium text-navy-400">
        <Icon size={13} />
        {label}
      </div>
      <div className="mt-1.5 text-2xl font-bold tabular-nums text-navy-900">{value}</div>
      {sub && <div className="text-xs text-navy-400">{sub}</div>}
    </div>
  );
}

function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

/**
 * Polls GET /metrics — this process's own CPU/memory (via psutil) and every
 * /chat call's classified intent + latency, recorded server-side in
 * app/observability.py. In-memory on the backend, single process: restart
 * the server and the counters reset, and a second uvicorn worker would keep
 * its own separate numbers (see that module's docstring).
 */
export default function ObservabilityView({ token }) {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const data = await getMetrics(token);
        if (!cancelled) {
          setMetrics(data);
          setError("");
        }
      } catch {
        if (!cancelled) setError("Couldn't load metrics.");
      }
    }
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [token]);

  if (error && !metrics) return <div className="p-6 text-sm text-negative">{error}</div>;
  if (!metrics) return <div className="p-6 text-sm text-navy-400">Loading metrics…</div>;

  const agentEntries = Object.entries(metrics.agent_counts);
  const maxCount = Math.max(...agentEntries.map(([, n]) => n), 1);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 md:px-8">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-navy-900">Observability</h1>
        <span className="flex items-center gap-1.5 text-xs font-medium text-positive">
          <span className="h-1.5 w-1.5 rounded-full bg-positive" />
          Live · refreshes every {POLL_MS / 1000}s
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile icon={Cpu} label="CPU" value={`${metrics.cpu_percent.toFixed(1)}%`} sub="this process" />
        <StatTile icon={HardDrive} label="Memory" value={`${metrics.memory_mb.toFixed(0)} MB`} sub="RSS" />
        <StatTile icon={Clock} label="Uptime" value={formatUptime(metrics.uptime_seconds)} />
        <StatTile icon={Activity} label="Chat calls" value={metrics.total_calls} sub="since restart" />
      </div>

      <div className="mt-4 rounded-xl2 border border-navy-100 bg-white p-5 shadow-card">
        <div className="text-sm font-medium text-navy-400">Calls by Agent</div>
        {agentEntries.length === 0 ? (
          <p className="mt-3 text-sm text-navy-300">No chat messages yet this session.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {agentEntries.map(([intent, count], i) => {
              const label = metrics.recent_calls.find((c) => c.intent === intent)?.agent || `Unclassified (${intent})`;
              const color = AGENT_COLORS[label] || UNCLASSIFIED_COLOR;
              return (
                <div key={intent}>
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="font-medium text-navy-600">{label}</span>
                    <span className="tabular-nums text-navy-400">{count}</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-navy-50">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: color }}
                      initial={{ width: 0 }}
                      animate={{ width: `${(count / maxCount) * 100}%` }}
                      transition={{ duration: 0.4, delay: i * 0.05 }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-4 rounded-xl2 border border-navy-100 bg-white p-5 shadow-card">
        <div className="text-sm font-medium text-navy-400">Recent Agent Calls</div>
        {metrics.recent_calls.length === 0 ? (
          <p className="mt-3 text-sm text-navy-300">Nothing recorded yet — send a chat message.</p>
        ) : (
          <div className="mt-3 divide-y divide-navy-50">
            {metrics.recent_calls.map((c, i) => (
              <div key={i} className="flex items-center justify-between py-2 text-sm">
                <div>
                  <span className="font-medium text-navy-800">{c.agent || `Unclassified (${c.intent})`}</span>
                  <span className="ml-2 text-xs text-navy-300">
                    {new Date(c.timestamp * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                  </span>
                </div>
                <span className="tabular-nums text-navy-400">{c.latency_ms.toFixed(0)} ms</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
