import { motion } from "framer-motion";
import { formatINR } from "../../services/mockBankingData";

export default function BalanceCard({ account }) {
  return (
    <motion.div
      className="rounded-xl2 border border-navy-100 bg-white p-5 shadow-card"
      whileHover={{ y: -2 }}
      transition={{ duration: 0.15 }}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-navy-400">Total Balance</span>
        <span className="text-[11px] font-medium text-navy-400">{account.accountNumberMasked}</span>
      </div>

      <div className="mt-2 text-3xl font-bold tracking-tight text-navy-900 tabular-nums">
        {formatINR(account.totalBalance)}
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-navy-50 pt-3">
        <div>
          <div className="text-xs text-navy-400">Available</div>
          <div className="text-sm font-semibold text-navy-800 tabular-nums">
            {formatINR(account.availableBalance)}
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-positive">
          <span className="h-1.5 w-1.5 rounded-full bg-positive" />
          {account.updatedLabel}
        </div>
      </div>
    </motion.div>
  );
}
