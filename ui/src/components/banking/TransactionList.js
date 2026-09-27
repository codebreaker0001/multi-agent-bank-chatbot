import { motion } from "framer-motion";
import { formatINR } from "../../services/mockBankingData";
import { categoryMeta } from "./categoryMeta";

function TransactionRow({ txn, index }) {
  const { icon: Icon, tint } = categoryMeta(txn.category);
  const isCredit = txn.type === "credit";

  return (
    <motion.div
      className="flex items-center gap-3 py-2.5"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.03 }}
    >
      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${tint}`}>
        <Icon size={16} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium text-navy-800">{txn.merchant}</div>
        <div className="text-xs text-navy-400">{txn.date}</div>
      </div>
      <div className={`shrink-0 text-sm font-semibold tabular-nums ${isCredit ? "text-positive" : "text-navy-800"}`}>
        {isCredit ? "+" : "-"}
        {formatINR(txn.amount)}
      </div>
    </motion.div>
  );
}

export default function TransactionList({ transactions, title = "Recent Activity" }) {
  return (
    <div className="rounded-xl2 border border-navy-100 bg-white p-5 shadow-card">
      <div className="text-sm font-medium text-navy-400">{title}</div>
      <div className="mt-1 divide-y divide-navy-50">
        {transactions.map((txn, i) => (
          <TransactionRow key={txn.id} txn={txn} index={i} />
        ))}
      </div>
    </div>
  );
}
