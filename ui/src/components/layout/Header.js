import { Menu, MoreVertical, PanelRightOpen, ShieldCheck } from "lucide-react";

export default function Header({ title, showStatus, onOpenSidebar, onOpenPanel, onNewChat }) {
  return (
    <header className="flex shrink-0 items-center justify-between border-b border-navy-100 bg-white/90 px-4 py-3 backdrop-blur">
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenSidebar}
          aria-label="Open menu"
          className="rounded-lg p-2 text-navy-500 hover:bg-navy-50 md:hidden"
        >
          <Menu size={18} />
        </button>
        <div>
          <div className="text-sm font-bold text-navy-900">{title}</div>
          {showStatus && (
            <div className="flex items-center gap-1 text-[11px] font-medium text-positive">
              <span className="h-1.5 w-1.5 rounded-full bg-positive" />
              Secure &amp; Online
              <ShieldCheck size={11} className="ml-1 text-navy-300" />
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1">
        {showStatus && (
          <button
            onClick={onOpenPanel}
            aria-label="Open account panel"
            className="rounded-lg p-2 text-navy-500 hover:bg-navy-50 lg:hidden"
          >
            <PanelRightOpen size={18} />
          </button>
        )}
        {onNewChat && (
          <button
            onClick={onNewChat}
            aria-label="Start a new chat"
            className="rounded-lg p-2 text-navy-400 hover:bg-navy-50"
          >
            <MoreVertical size={18} />
          </button>
        )}
      </div>
    </header>
  );
}
