import {
  Car,
  CircleDollarSign,
  Home,
  ShoppingBag,
  Tv,
  Utensils,
  Wallet,
  Zap,
} from "lucide-react";

// One place mapping a transaction category to its icon + tint — reused by
// TransactionList, TransactionCard, and the spending chart legend.
export const CATEGORY_META = {
  food: { icon: Utensils, tint: "bg-orange-50 text-orange-600" },
  shopping: { icon: ShoppingBag, tint: "bg-accent-50 text-accent-600" },
  transport: { icon: Car, tint: "bg-violet-50 text-violet-600" },
  entertainment: { icon: Tv, tint: "bg-rose-50 text-rose-600" },
  utilities: { icon: Zap, tint: "bg-amber-50 text-amber-600" },
  salary: { icon: Wallet, tint: "bg-positive-bg text-positive" },
  rent: { icon: Home, tint: "bg-navy-50 text-navy-600" },
};

export function categoryMeta(category) {
  return CATEGORY_META[category] || { icon: CircleDollarSign, tint: "bg-navy-50 text-navy-500" };
}
