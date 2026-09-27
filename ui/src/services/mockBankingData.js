/**
 * Static UI copy (suggestion prompts, chips) plus the INR formatter.
 *
 * Account/transaction/card numbers used to live here as mock data before
 * GET /accounts, GET /transactions, and GET /cards existed — see
 * dashboardData.js for the real thing now.
 */

export const suggestionCards = [
  { id: "balance", icon: "wallet", title: "Check my balance", subtitle: "See your current account balance", prompt: "What's my current balance?" },
  { id: "spending", icon: "bar-chart-2", title: "Analyze my spending", subtitle: "Understand where your money goes", prompt: "How much did I spend this month?" },
  { id: "cards", icon: "credit-card", title: "Manage my cards", subtitle: "Freeze, unfreeze, or view details", prompt: "Show my card details" },
  { id: "service", icon: "settings", title: "Update my details", subtitle: "Address, KYC, or cheque book", prompt: "I want to update my address" },
];

export const inputSuggestions = [
  "Check balance",
  "Recent transactions",
  "Analyze spending",
  "Update my address",
];

export function formatINR(amount) {
  const value = Number(amount);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: value % 1 === 0 ? 0 : 2,
  }).format(value);
}
