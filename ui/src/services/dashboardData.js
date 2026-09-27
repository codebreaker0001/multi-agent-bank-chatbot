/**
 * Maps the real /accounts, /transactions, /cards responses into the shapes
 * the presentational components (BalanceCard, TransactionList, SpendingChart)
 * were built around, so those components don't need to know about API
 * field names or JSON-serialized Decimals.
 */

const CATEGORY_COLORS = [
  "#3b5bdb", // accent
  "#1a9c5b", // positive
  "#b3791d", // warning
  "#8b5cf6", // violet
  "#d6483f", // negative
  "#0d9488", // teal
];

export function mapAccount(apiAccounts) {
  const primary = apiAccounts[0];
  if (!primary) return null;
  return {
    accountNumberMasked: primary.account_number_masked,
    accountType: primary.account_type,
    availableBalance: Number(primary.available_balance),
    totalBalance: Number(primary.balance),
    updatedLabel: "Updated just now",
  };
}

export function mapTransactions(apiTransactions) {
  return apiTransactions.map((t) => ({
    id: t.id,
    merchant: t.merchant,
    category: t.category,
    date: formatRelativeDate(t.date),
    amount: Number(t.amount),
    type: t.type,
    status: "Completed",
  }));
}

export function mapSpending(apiCategorySpend) {
  return [...apiCategorySpend]
    .map((c, i) => ({ category: c.category, amount: Number(c.amount), color: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }))
    .sort((a, b) => b.amount - a.amount);
}

function formatRelativeDate(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const daysAgo = Math.round((startOfDay(now) - startOfDay(date)) / 86400000);

  const time = date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (daysAgo === 0) return `Today, ${time}`;
  if (daysAgo === 1) return "Yesterday";
  if (daysAgo < 7) return `${daysAgo} days ago`;
  return date.toLocaleDateString([], { day: "numeric", month: "short" });
}
