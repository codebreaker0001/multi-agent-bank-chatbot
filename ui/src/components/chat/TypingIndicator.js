import { motion } from "framer-motion";

export default function TypingIndicator({ label = "Thinking…" }) {
  return (
    <div className="flex items-center gap-2 text-sm text-navy-400">
      <span className="flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="h-1.5 w-1.5 rounded-full bg-navy-300"
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }}
          />
        ))}
      </span>
      {label}
    </div>
  );
}
