import Badge from "../ui/Badge";
import { formatINR } from "../../services/mockBankingData";
import { categoryMeta } from "./categoryMeta";

/** A single transaction, detailed — used inline in a chat reply. */
export default function TransactionCard({ txn }) {
  const { icon: Icon, tint } = categoryMeta(txn.category);
  const isCredit = txn.type === "credit";

  return (
    <div className="w-full max-w-xs rounded-xl2 border border-navy-100 bg-white p-4 shadow-card">
      <div className="flex items-start gap-3">
        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${tint}`}>
          <Icon size={18} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate text-sm font-semibold text-navy-900">{txn.merchant}</div>
          <div className="text-xs capitalize text-navy-400">{txn.category}</div>
          <div className="text-xs text-navy-400">{txn.date}</div>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-navy-50 pt-3">
        <div className={`text-lg font-bold tabular-nums ${isCredit ? "text-positive" : "text-navy-900"}`}>
          {isCredit ? "+" : "-"}
          {formatINR(txn.amount)}
        </div>
        {txn.status && <Badge tone="positive">{txn.status}</Badge>}
      </div>
    </div>
  );
}
