/**
 * App.js — top-level shell: auth gate, sidebar/panel chrome, and view routing.
 *
 * auth state:
 *   null                                  → show Login screen
 *   { token, refreshToken, name }         → show the app shell
 *
 * Both JWTs are kept in React state (memory), not localStorage.
 * Why? localStorage is accessible to any JS on the page (XSS risk).
 * In-memory means the token is gone when the tab closes, which is fine
 * for a banking session.
 *
 * dashboard state: fetched once per login from GET /accounts,
 * GET /transactions, GET /cards — the real numbers behind Overview,
 * Accounts, Transactions, Cards, Analytics and the right-side panel.
 * `null` while loading; every one of those views waits on it via
 * <DashboardGate> rather than rendering with undefined data.
 *
 * There's no router — this is a single conversational product, not a
 * multi-page dashboard, so `view` is just local state.
 */

import { useEffect, useState } from "react";
import Login from "./components/Login";
import Sidebar from "./components/layout/Sidebar";
import MobileNav from "./components/layout/MobileNav";
import Header from "./components/layout/Header";
import RightPanel from "./components/layout/RightPanel";
import Drawer from "./components/ui/Drawer";
import Toast from "./components/ui/Toast";
import ChatWindow from "./components/chat/ChatWindow";
import { freezeCard, getAccounts, getCard, getTransactions, refreshAccessToken, unfreezeCard } from "./api";
import { mapAccount, mapSpending, mapTransactions } from "./services/dashboardData";
import {
  AccountsView,
  AnalyticsView,
  CardsView,
  OverviewView,
  PaymentsView,
  ProfileView,
  TransactionsView,
} from "./components/views/Views";
import ObservabilityView from "./components/views/ObservabilityView";

const VIEW_TITLES = {
  overview: "Overview",
  accounts: "Accounts",
  transactions: "Transactions",
  cards: "Cards",
  payments: "Payments",
  analytics: "Analytics",
  observability: "Observability",
  assistant: "AI Banking Assistant",
  profile: "Profile",
};

async function fetchDashboard(token) {
  const [accounts, tx, card] = await Promise.all([getAccounts(token), getTransactions(token, 10), getCard(token)]);
  return {
    account: mapAccount(accounts),
    transactions: mapTransactions(tx.transactions),
    spending: mapSpending(tx.spending_by_category),
    monthOverMonthPct: tx.month_over_month_pct,
    card,
  };
}

export default function App() {
  const [auth, setAuth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [dashboardError, setDashboardError] = useState(null);
  const [view, setView] = useState("assistant");
  const [collapsed, setCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false);
  const [contextHint, setContextHint] = useState(null);
  const [chatKey, setChatKey] = useState(0);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  // Fetch once per login. Keyed on refreshToken (stable across the 15-min
  // access-token refresh) rather than token, so this doesn't re-fire and
  // flash a loading state every time ChatWindow silently refreshes.
  useEffect(() => {
    if (!auth) return;
    let cancelled = false;
    setDashboard(null);
    setDashboardError(null);

    (async () => {
      try {
        const data = await fetchDashboard(auth.token);
        if (!cancelled) setDashboard(data);
      } catch (err) {
        if (err.status === 401) {
          try {
            const { access_token } = await refreshAccessToken(auth.refreshToken);
            handleTokenRefresh(access_token);
            const data = await fetchDashboard(access_token);
            if (!cancelled) setDashboard(data);
            return;
          } catch {
            handleLogout();
            return;
          }
        }
        if (!cancelled) setDashboardError("Couldn't load your account data.");
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth?.refreshToken]);

  function handleLogin(data) {
    setAuth({ token: data.access_token, refreshToken: data.refresh_token, name: data.name });
  }

  function handleLogout() {
    setAuth(null);
    setView("assistant");
    setContextHint(null);
  }

  function handleTokenRefresh(accessToken) {
    setAuth((prev) => (prev ? { ...prev, token: accessToken } : prev));
  }

  function handleNewChat() {
    setChatKey((k) => k + 1);
    setContextHint(null);
    setView("assistant");
    setMobileSidebarOpen(false);
  }

  function navigate(nextView) {
    setView(nextView);
    setMobileSidebarOpen(false);
  }

  function handleQuickAction(id) {
    if (id === "card") navigate("cards");
    else if (id === "transactions") navigate("transactions");
    else if (id === "bill") navigate("payments");
  }

  async function handleFreezeCard() {
    try {
      const card = await freezeCard(auth.token);
      setDashboard((d) => ({ ...d, card }));
    } catch {
      setToast("Couldn't freeze the card. Try again.");
    }
  }

  async function handleUnfreezeCard() {
    try {
      const card = await unfreezeCard(auth.token);
      setDashboard((d) => ({ ...d, card }));
    } catch {
      setToast("Couldn't unfreeze the card. Try again.");
    }
  }

  if (!auth) {
    return <Login onLogin={handleLogin} />;
  }

  const isAssistant = view === "assistant";

  return (
    <div className="flex h-[100dvh] w-screen overflow-hidden bg-navy-50/40 text-navy-900">
      {/* Desktop sidebar */}
      <div className="hidden border-r border-navy-100 md:block">
        <Sidebar
          view={view}
          onNavigate={navigate}
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed((c) => !c)}
          userName={auth.name}
          onLogout={handleLogout}
          onNewChat={handleNewChat}
        />
      </div>

      {/* Mobile sidebar drawer */}
      <Drawer side="left" open={mobileSidebarOpen} onClose={() => setMobileSidebarOpen(false)}>
        <Sidebar
          view={view}
          onNavigate={navigate}
          collapsed={false}
          userName={auth.name}
          onLogout={handleLogout}
          onNewChat={handleNewChat}
          hideCollapseToggle
        />
      </Drawer>

      <div className="flex min-w-0 flex-1 flex-col pb-14 md:pb-0">
        <Header
          title={VIEW_TITLES[view]}
          showStatus={isAssistant}
          onOpenSidebar={() => setMobileSidebarOpen(true)}
          onOpenPanel={() => setMobilePanelOpen(true)}
          onNewChat={isAssistant ? handleNewChat : undefined}
        />

        <div className="flex min-h-0 flex-1">
          {view === "overview" && (
            <ScrollArea>
              <DashboardGate dashboard={dashboard} error={dashboardError}>
                <OverviewView {...dashboard} onFreeze={handleFreezeCard} onUnfreeze={handleUnfreezeCard} />
              </DashboardGate>
            </ScrollArea>
          )}
          {view === "accounts" && (
            <ScrollArea>
              <DashboardGate dashboard={dashboard} error={dashboardError}>
                <AccountsView account={dashboard?.account} />
              </DashboardGate>
            </ScrollArea>
          )}
          {view === "transactions" && (
            <ScrollArea>
              <DashboardGate dashboard={dashboard} error={dashboardError}>
                <TransactionsView transactions={dashboard?.transactions} />
              </DashboardGate>
            </ScrollArea>
          )}
          {view === "cards" && (
            <ScrollArea>
              <DashboardGate dashboard={dashboard} error={dashboardError}>
                <CardsView card={dashboard?.card} onFreeze={handleFreezeCard} onUnfreeze={handleUnfreezeCard} />
              </DashboardGate>
            </ScrollArea>
          )}
          {view === "payments" && <ScrollArea><PaymentsView /></ScrollArea>}
          {view === "analytics" && (
            <ScrollArea>
              <DashboardGate dashboard={dashboard} error={dashboardError}>
                <AnalyticsView spending={dashboard?.spending} monthOverMonthPct={dashboard?.monthOverMonthPct} />
              </DashboardGate>
            </ScrollArea>
          )}
          {view === "observability" && <ScrollArea><ObservabilityView token={auth.token} /></ScrollArea>}
          {view === "profile" && <ScrollArea><ProfileView userName={auth.name} onLogout={handleLogout} /></ScrollArea>}
          {isAssistant && (
            <>
              <ChatWindow
                key={chatKey}
                token={auth.token}
                refreshToken={auth.refreshToken}
                userName={auth.name}
                onTokenRefresh={handleTokenRefresh}
                onLogout={handleLogout}
                onContextHint={setContextHint}
              />
              <RightPanel
                contextView={contextHint}
                onQuickAction={handleQuickAction}
                account={dashboard?.account}
                transactions={dashboard?.transactions ?? []}
                spending={dashboard?.spending ?? []}
                monthOverMonthPct={dashboard?.monthOverMonthPct}
                card={dashboard?.card}
                onFreeze={handleFreezeCard}
                onUnfreeze={handleUnfreezeCard}
                loading={!dashboard}
                className="hidden shrink-0 border-l border-navy-100 lg:flex"
              />
            </>
          )}
        </div>
      </div>

      {/* Mobile context panel drawer */}
      <Drawer side="right" open={mobilePanelOpen} onClose={() => setMobilePanelOpen(false)}>
        <RightPanel
          contextView={contextHint}
          onQuickAction={(id) => {
            setMobilePanelOpen(false);
            handleQuickAction(id);
          }}
          account={dashboard?.account}
          transactions={dashboard?.transactions ?? []}
          spending={dashboard?.spending ?? []}
          monthOverMonthPct={dashboard?.monthOverMonthPct}
          card={dashboard?.card}
          onFreeze={handleFreezeCard}
          onUnfreeze={handleUnfreezeCard}
          loading={!dashboard}
        />
      </Drawer>

      <MobileNav view={view} onNavigate={navigate} />

      <Toast message={toast} />
    </div>
  );
}

function ScrollArea({ children }) {
  return <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>;
}

function DashboardGate({ dashboard, error, children }) {
  if (error) return <div className="p-6 text-sm text-negative">{error}</div>;
  if (!dashboard) return <div className="p-6 text-sm text-navy-400">Loading your account…</div>;
  return children;
}
