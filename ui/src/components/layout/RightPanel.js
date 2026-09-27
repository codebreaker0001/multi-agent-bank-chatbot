import { AnimatePresence, motion } from "framer-motion";
import { CreditCard, List, Receipt } from "lucide-react";
import BalanceCard from "../banking/BalanceCard";
import TransactionList from "../banking/TransactionList";
import SpendingChart from "../banking/SpendingChart";
import CardPreview from "../banking/CardPreview";

const QUICK_ACTIONS = [
  { id: "bill", label: "Pay Bill", icon: Receipt },
  { id: "card", label: "Manage Card", icon: CreditCard },
  { id: "transactions", label: "View Transactions", icon: List },
];

/** Contextual panel: swaps its featured card based on what the user's asking about. */
export default function RightPanel({
  contextView,
  onQuickAction,
  account,
  transactions,
  spending,
  monthOverMonthPct,
  card,
  onFreeze,
  onUnfreeze,
  loading,
  className = "",
}) {
  const featured =
    contextView === "spending" ? (
      <SpendingChart categories={spending} monthOverMonthPct={monthOverMonthPct} />
    ) : contextView === "card" ? (
      <CardPreview card={card} onFreeze={onFreeze} onUnfreeze={onUnfreeze} />
    ) : (
      <BalanceCard account={account} />
    );

  return (
    <aside className={`flex h-full w-full flex-col gap-4 overflow-y-auto bg-navy-50/40 p-4 lg:w-[320px] ${className}`}>
      {loading ? (
        <div className="py-8 text-center text-sm text-navy-400">Loading your account…</div>
      ) : (
        <>
          <AnimatePresence mode="wait">
            <motion.div
              key={contextView || "balance"}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18 }}
            >
              {featured}
            </motion.div>
          </AnimatePresence>

          <TransactionList transactions={transactions.slice(0, 4)} />
        </>
      )}

      <div className="rounded-xl2 border border-navy-100 bg-white p-4 shadow-card">
        <div className="mb-2 text-sm font-medium text-navy-400">Quick Actions</div>
        <div className="grid grid-cols-2 gap-2">
          {QUICK_ACTIONS.map((a) => (
            <button
              key={a.id}
              onClick={() => onQuickAction(a.id)}
              className="flex flex-col items-start gap-2 rounded-xl border border-navy-100 p-3 text-left text-xs font-medium text-navy-700 transition-colors hover:border-accent-500 hover:bg-accent-50 hover:text-accent-600"
            >
              <a.icon size={15} />
              {a.label}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
