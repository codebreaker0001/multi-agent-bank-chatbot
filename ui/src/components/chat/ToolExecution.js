import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check } from "lucide-react";

const STEPS = ["Reading your message", "Checking your account context", "Preparing a response"];

/**
 * Cosmetic step list shown while the real /chat request is in flight. The
 * backend answers in one round trip (no streamed tool-call events), so this
 * doesn't reflect real server-side steps — it's an honest-ish approximation
 * (generic verbs, no claims like "transactions found") to make the wait feel
 * like an agent at work rather than a stalled spinner.
 */
export default function ToolExecution() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (step >= STEPS.length - 1) return;
    const t = setTimeout(() => setStep((s) => s + 1), 550);
    return () => clearTimeout(t);
  }, [step]);

  return (
    <div className="space-y-1.5">
      {STEPS.map((label, i) => (
        <div key={label} className="flex items-center gap-2 text-sm">
          {i < step ? (
            <Check size={14} className="text-positive" />
          ) : i === step ? (
            <motion.span
              className="h-3.5 w-3.5 rounded-full border-2 border-navy-200 border-t-accent-500"
              animate={{ rotate: 360 }}
              transition={{ duration: 0.7, repeat: Infinity, ease: "linear" }}
            />
          ) : (
            <span className="h-3.5 w-3.5 rounded-full border-2 border-navy-100" />
          )}
          <span className={i <= step ? "text-navy-600" : "text-navy-300"}>{label}</span>
        </div>
      ))}
    </div>
  );
}
