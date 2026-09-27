import { motion } from "framer-motion";
import {
  Activity,
  BarChart2,
  Bell,
  ChevronsLeft,
  ChevronsRight,
  CreditCard,
  HelpCircle,
  Home,
  LandmarkIcon,
  List,
  LogOut,
  MessageSquareText,
  Plus,
  Send,
  Settings,
  Sparkles,
} from "lucide-react";

const NAV = [
  { id: "overview", label: "Overview", icon: Home },
  { id: "accounts", label: "Accounts", icon: LandmarkIcon },
  { id: "transactions", label: "Transactions", icon: List },
  { id: "cards", label: "Cards", icon: CreditCard },
  { id: "payments", label: "Payments", icon: Send },
  { id: "analytics", label: "Analytics", icon: BarChart2 },
  { id: "observability", label: "Observability", icon: Activity },
  { id: "assistant", label: "AI Assistant", icon: MessageSquareText },
];

export default function Sidebar({
  view,
  onNavigate,
  collapsed,
  onToggleCollapse,
  userName,
  onLogout,
  onNewChat,
  hideCollapseToggle,
  className = "",
}) {
  return (
    <motion.aside
      animate={{ width: collapsed ? 76 : 260 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className={`flex h-full shrink-0 flex-col bg-white ${className}`}
    >
      {/* Brand */}
      <div className="flex items-center gap-2 px-4 pt-5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-navy-900 text-white">
          <LandmarkIcon size={16} />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <div className="truncate text-sm font-bold text-navy-900">DemoBank</div>
            <div className="truncate text-[11px] text-navy-400">AI Banking Assistant</div>
          </div>
        )}
      </div>

      <div className="px-3 pt-4">
        <button
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-navy-900 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-navy-800"
        >
          <Plus size={15} />
          {!collapsed && "New Chat"}
        </button>
      </div>

      {/* Nav */}
      <nav className="mt-4 flex-1 space-y-0.5 px-3">
        {NAV.map((item) => {
          const Icon = item.icon;
          const active = view === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors duration-150 ${
                active ? "bg-accent-50 text-accent-600" : "text-navy-500 hover:bg-navy-50 hover:text-navy-800"
              }`}
              aria-current={active ? "page" : undefined}
            >
              <Icon size={17} className="shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* AI status */}
      <div className="px-4 pb-2">
        <div className="flex items-center gap-2 rounded-xl bg-positive-bg px-3 py-2 text-xs font-medium text-positive">
          <Sparkles size={13} />
          {!collapsed && "Assistant Ready"}
          <span className="ml-auto h-1.5 w-1.5 shrink-0 rounded-full bg-positive" />
        </div>
      </div>

      {/* Bottom */}
      <div className="space-y-0.5 border-t border-navy-50 px-3 py-3">
        <SidebarIconRow icon={HelpCircle} label="Help & Support" collapsed={collapsed} />
        <SidebarIconRow icon={Bell} label="Notifications" collapsed={collapsed} />
        <SidebarIconRow icon={Settings} label="Settings" collapsed={collapsed} />

        <div className="mt-2 flex items-center gap-2.5 rounded-xl px-3 py-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-100 text-xs font-semibold text-navy-700">
            {userName?.[0]?.toUpperCase() || "U"}
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-navy-800">{userName}</div>
            </div>
          )}
          <button onClick={onLogout} aria-label="Sign out" className="text-navy-300 hover:text-negative">
            <LogOut size={15} />
          </button>
        </div>

        {!hideCollapseToggle && (
          <button
            onClick={onToggleCollapse}
            className="mt-1 flex w-full items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-medium text-navy-300 hover:bg-navy-50 hover:text-navy-600"
          >
            {collapsed ? <ChevronsRight size={15} /> : <ChevronsLeft size={15} />}
          </button>
        )}
      </div>
    </motion.aside>
  );
}

function SidebarIconRow({ icon: Icon, label, collapsed }) {
  return (
    <button className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm text-navy-500 hover:bg-navy-50 hover:text-navy-800">
      <Icon size={16} className="shrink-0" />
      {!collapsed && <span className="truncate">{label}</span>}
    </button>
  );
}

export { NAV };
