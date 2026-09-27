import { LogOut, Receipt } from "lucide-react";
import Button from "../ui/Button";
import BalanceCard from "../banking/BalanceCard";
import TransactionList from "../banking/TransactionList";
import SpendingChart from "../banking/SpendingChart";
import CardPreview from "../banking/CardPreview";

const PAGE = "mx-auto w-full max-w-3xl px-4 py-6 md:px-8";
const TITLE = "mb-4 text-xl font-bold text-navy-900";

export function OverviewView({ account, transactions, spending, monthOverMonthPct, card, onFreeze, onUnfreeze }) {
  return (
    <div className={PAGE}>
      <h1 className={TITLE}>Overview</h1>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <BalanceCard account={account} />
        <SpendingChart categories={spending} monthOverMonthPct={monthOverMonthPct} />
        <CardPreview card={card} onFreeze={onFreeze} onUnfreeze={onUnfreeze} />
        <TransactionList transactions={transactions} />
      </div>
    </div>
  );
}

export function AccountsView({ account }) {
  return (
    <div className={PAGE}>
      <h1 className={TITLE}>Accounts</h1>
      <BalanceCard account={account} />
      <p className="mt-3 text-sm text-navy-400">
        {account.accountType} account · {account.accountNumberMasked}
      </p>
    </div>
  );
}

export function TransactionsView({ transactions }) {
  return (
    <div className={PAGE}>
      <h1 className={TITLE}>Transactions</h1>
      <TransactionList transactions={transactions} title="All Recent Transactions" />
    </div>
  );
}

export function CardsView({ card, onFreeze, onUnfreeze }) {
  return (
    <div className={PAGE}>
      <h1 className={TITLE}>Cards</h1>
      <div className="max-w-sm">
        <CardPreview card={card} onFreeze={onFreeze} onUnfreeze={onUnfreeze} />
      </div>
    </div>
  );
}

export function PaymentsView() {
  return (
    <div className={PAGE}>
      <h1 className={TITLE}>Payments</h1>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="flex items-center gap-3 rounded-xl2 border border-navy-100 bg-white p-4 opacity-60">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-navy-50 text-navy-500">
            <Receipt size={17} />
          </div>
          <div>
            <div className="text-sm font-semibold text-navy-900">Pay Bill</div>
            <div className="text-xs text-navy-400">Coming soon</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function AnalyticsView({ spending, monthOverMonthPct }) {
  return (
    <div className={PAGE}>
      <h1 className={TITLE}>Analytics</h1>
      <SpendingChart categories={spending} monthOverMonthPct={monthOverMonthPct} />
    </div>
  );
}

export function ProfileView({ userName, onLogout }) {
  return (
    <div className={PAGE}>
      <h1 className={TITLE}>Profile</h1>
      <div className="flex items-center gap-3 rounded-xl2 border border-navy-100 bg-white p-4 shadow-card">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-navy-100 text-sm font-semibold text-navy-700">
          {userName?.[0]?.toUpperCase() || "U"}
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-navy-900">{userName}</div>
          <div className="text-xs text-navy-400">Signed in</div>
        </div>
        <Button variant="secondary" size="sm" onClick={onLogout}>
          <LogOut size={14} />
          Sign out
        </Button>
      </div>
    </div>
  );
}
