import { motion } from "framer-motion";
import { BarChart2, CreditCard, Settings, Wallet } from "lucide-react";

const ICONS = { wallet: Wallet, "bar-chart-2": BarChart2, "credit-card": CreditCard, settings: Settings };

export function WelcomeSuggestions({ cards, onSelect }) {
  return (
    <div className="grid w-full max-w-xl grid-cols-1 gap-3 sm:grid-cols-2">
      {cards.map((card, i) => {
        const Icon = ICONS[card.icon];
        return (
          <motion.button
            key={card.id}
            onClick={() => onSelect(card.prompt)}
            className="flex items-start gap-3 rounded-xl2 border border-navy-100 bg-white p-4 text-left shadow-card transition-shadow hover:shadow-elevated"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: i * 0.05 }}
            whileHover={{ y: -2 }}
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent-50 text-accent-600">
              <Icon size={16} />
            </div>
            <div>
              <div className="text-sm font-semibold text-navy-900">{card.title}</div>
              <div className="mt-0.5 text-xs text-navy-400">{card.subtitle}</div>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}

export function InputChips({ items, onSelect }) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((label) => (
        <button
          key={label}
          onClick={() => onSelect(label)}
          className="rounded-full border border-navy-100 bg-white px-3 py-1.5 text-xs font-medium text-navy-600 transition-colors hover:border-accent-500 hover:text-accent-600"
        >
          {label}
        </button>
      ))}
    </div>
  );
}
