import { useState } from "react";
import { motion } from "framer-motion";
import { LandmarkIcon, Lock, ShieldCheck, User } from "lucide-react";
import { login } from "../api";
import Button from "./ui/Button";

export default function Login({ onLogin }) {
  const [customerId, setCustomerId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(customerId, password);
      onLogin(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-[100dvh] items-center justify-center bg-navy-50/60 px-4">
      <motion.div
        className="w-full max-w-sm rounded-xl2 border border-navy-100 bg-white p-8 shadow-elevated"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <div className="flex flex-col items-center text-center">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-navy-900 text-white">
            <LandmarkIcon size={20} />
          </div>
          <h1 className="mt-3 text-xl font-bold text-navy-900">DemoBank</h1>
          <p className="mt-1 text-sm text-navy-400">Sign in to your AI banking assistant</p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <Field label="Customer ID" icon={User}>
            <input
              className="w-full bg-transparent text-sm text-navy-800 placeholder:text-navy-300 focus:outline-none"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              placeholder="e.g. CUST1001"
              autoComplete="username"
              required
            />
          </Field>

          <Field label="Password" icon={Lock}>
            <input
              className="w-full bg-transparent text-sm text-navy-800 placeholder:text-navy-300 focus:outline-none"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              required
            />
          </Field>

          {error && (
            <p role="alert" className="rounded-lg bg-negative-bg px-3 py-2 text-xs font-medium text-negative">
              {error}
            </p>
          )}

          <Button type="submit" variant="primary" size="lg" className="w-full" disabled={loading}>
            {loading ? "Signing in…" : "Sign In"}
          </Button>
        </form>

        <div className="mt-5 flex items-center justify-center gap-1.5 text-[11px] text-navy-300">
          <ShieldCheck size={12} />
          Bank-grade encryption &middot; PII masked before reaching the AI
        </div>

        <p className="mt-4 text-center text-xs text-navy-400">
          Demo credentials: <strong className="text-navy-600">CUST1001</strong> /{" "}
          <strong className="text-navy-600">CUST1001</strong>
        </p>
      </motion.div>
    </div>
  );
}

function Field({ label, icon: Icon, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-navy-500">{label}</span>
      <div className="flex items-center gap-2 rounded-xl border border-navy-100 bg-white px-3 py-2.5 transition-colors focus-within:border-accent-500 focus-within:shadow-[0_0_0_3px_rgba(59,91,219,0.12)]">
        <Icon size={15} className="shrink-0 text-navy-300" />
        {children}
      </div>
    </label>
  );
}
