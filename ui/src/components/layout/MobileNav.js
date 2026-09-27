import { CreditCard, List, MessageSquareText, User, Wallet } from "lucide-react";

const ITEMS = [
  { id: "overview", label: "Home", icon: Wallet },
  { id: "transactions", label: "Transactions", icon: List },
  { id: "assistant", label: "Assistant", icon: MessageSquareText },
  { id: "cards", label: "Cards", icon: CreditCard },
  { id: "profile", label: "Profile", icon: User },
];

export default function MobileNav({ view, onNavigate }) {
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-around border-t border-navy-100
        bg-white/95 py-1.5 backdrop-blur md:hidden"
      style={{ paddingBottom: "max(0.375rem, env(safe-area-inset-bottom))" }}
    >
      {ITEMS.map((item) => {
        const Icon = item.icon;
        const active = view === item.id;
        return (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`flex flex-col items-center gap-0.5 rounded-lg px-3 py-1 text-[10px] font-medium ${
              active ? "text-accent-600" : "text-navy-400"
            }`}
            aria-current={active ? "page" : undefined}
          >
            <Icon size={19} />
            {item.label}
          </button>
        );
      })}
    </nav>
  );
}
