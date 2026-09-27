import { motion } from "framer-motion";
import { formatINR } from "../../services/mockBankingData";

/**
 * Category spending breakdown as horizontal progress bars — deliberately not
 * a charting library. A handful of animated <div> bars covers this and
 * keeps the bundle free of a dependency for five numbers.
 */
export default function SpendingChart({ categories, monthOverMonthPct }) {
  const total = categories.reduce((sum, c) => sum + c.amount, 0);
  const max = Math.max(...categories.map((c) => c.amount), 1);
  const trendingDown = monthOverMonthPct <= 0;

  return (
    <div className="rounded-xl2 border border-navy-100 bg-white p-5 shadow-card">
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium text-navy-400">This Month's Spending</span>
        {/* No comparison shown when there's no prior-month data to compare against. */}
        {monthOverMonthPct != null && (
          <span className={`text-xs font-semibold ${trendingDown ? "text-positive" : "text-negative"}`}>
            {trendingDown ? "▼" : "▲"} {Math.abs(monthOverMonthPct)}% vs last month
          </span>
        )}
      </div>
      <div className="mt-1 text-2xl font-bold tabular-nums text-navy-900">{formatINR(total)}</div>

      <div className="mt-4 space-y-3">
        {categories.map((c, i) => (
          <div key={c.category}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="font-medium text-navy-600">{c.category}</span>
              <span className="tabular-nums text-navy-400">{formatINR(c.amount)}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-navy-50">
              <motion.div
                className="h-full rounded-full"
                style={{ background: c.color }}
                initial={{ width: 0 }}
                animate={{ width: `${(c.amount / max) * 100}%` }}
                transition={{ duration: 0.5, delay: i * 0.06, ease: "easeOut" }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
