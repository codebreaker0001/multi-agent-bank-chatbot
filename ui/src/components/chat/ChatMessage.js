import { useState } from "react";
import { motion } from "framer-motion";
import {
  Bot, Check, Copy, CreditCard, RotateCcw, Settings, ShieldCheck, ThumbsDown, ThumbsUp, User, Wallet,
} from "lucide-react";

function SystemMessage({ content }) {
  return (
    <div className="my-2 flex justify-center">
      <span className="rounded-full bg-warning-bg px-3 py-1 text-xs font-medium text-warning">{content}</span>
    </div>
  );
}

// Which sub-agent answered — from ChatResponse.agent (None for "unknown"
// intent, where no sub-agent runs at all). See app/observability.py's
// AGENT_NAMES for where these labels come from.
const AGENT_ICONS = {
  "Account Agent": Wallet,
  "Transaction Agent": CreditCard,
  "Service Agent": Settings,
};

function AgentBadge({ agent }) {
  const Icon = AGENT_ICONS[agent];
  if (!Icon) return null;
  return (
    <span className="mb-1 flex items-center gap-1 rounded-full bg-navy-50 px-2 py-0.5 text-[10px] font-medium text-navy-500">
      <Icon size={10} />
      {agent}
    </span>
  );
}

export default function ChatMessage({ role, content, agent, timestamp, isLast, onRegenerate }) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null); // "up" | "down" | null

  if (role === "system") return <SystemMessage content={content} />;

  const isUser = role === "user";

  function copy() {
    navigator.clipboard?.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <motion.div
      className={`group flex items-end gap-2 py-1.5 ${isUser ? "justify-end" : "justify-start"}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      {!isUser && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-navy-900 text-white">
          <Bot size={14} />
        </div>
      )}

      <div className={`flex max-w-[75%] flex-col ${isUser ? "items-end" : "items-start"}`}>
        {!isUser && <AgentBadge agent={agent} />}
        <div
          className={
            isUser
              ? "rounded-[18px] rounded-br-[4px] bg-navy-900 px-4 py-2.5 text-[14px] leading-relaxed text-white"
              : "rounded-[18px] rounded-bl-[4px] border border-navy-100 bg-white px-4 py-2.5 text-[14px] leading-relaxed text-navy-800 shadow-card"
          }
        >
          <span className="whitespace-pre-wrap">{content}</span>
        </div>

        <div className="mt-1 flex items-center gap-2 px-1 text-[11px] text-navy-300">
          {timestamp && <span>{timestamp}</span>}
          {!isUser && (
            <span className="hidden items-center gap-2 group-hover:flex">
              <button onClick={copy} aria-label="Copy response" className="hover:text-navy-500">
                {copied ? <Check size={12} /> : <Copy size={12} />}
              </button>
              {isLast && (
                <button onClick={onRegenerate} aria-label="Regenerate response" className="hover:text-navy-500">
                  <RotateCcw size={12} />
                </button>
              )}
              <button
                onClick={() => setFeedback((f) => (f === "up" ? null : "up"))}
                aria-label="Good response"
                className={feedback === "up" ? "text-positive" : "hover:text-navy-500"}
              >
                <ThumbsUp size={12} />
              </button>
              <button
                onClick={() => setFeedback((f) => (f === "down" ? null : "down"))}
                aria-label="Bad response"
                className={feedback === "down" ? "text-negative" : "hover:text-navy-500"}
              >
                <ThumbsDown size={12} />
              </button>
            </span>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-navy-100 text-navy-500">
          <User size={14} />
        </div>
      )}
    </motion.div>
  );
}

export function SecureNotice() {
  return (
    <div className="flex items-center gap-1.5 text-[11px] text-navy-300">
      <ShieldCheck size={12} />
      Messages are encrypted and PII is masked before reaching the AI model
    </div>
  );
}
