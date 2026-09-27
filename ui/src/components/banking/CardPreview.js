import { useState } from "react";
import { Lock, Unlock } from "lucide-react";
import Button from "../ui/Button";
import ConfirmationModal from "./ConfirmationModal";

/**
 * `card.frozen` is the source of truth from the backend (Account.card_frozen
 * — see POST /cards/freeze). This is a controlled component: it doesn't
 * hold its own frozen state, only the "am I mid-confirmation / mid-request"
 * UI state, so every place this renders stays in sync with the same account.
 *
 * Freezing is treated as the destructive action it is: it goes through a
 * confirmation. Unfreezing is reversible and low-risk, so it's instant.
 */
export default function CardPreview({ card, onFreeze, onUnfreeze }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  async function run(action) {
    setBusy(true);
    try {
      await action();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl2 border border-navy-100 bg-white p-5 shadow-card">
      <div className="rounded-xl bg-gradient-to-br from-navy-800 to-navy-900 p-4 text-white">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-navy-100/80">{card.network}</span>
          {card.frozen && (
            <span className="flex items-center gap-1 rounded-full bg-white/10 px-2 py-0.5 text-[11px] font-medium">
              <Lock size={11} /> Frozen
            </span>
          )}
        </div>
        <div className="mt-5 text-lg font-semibold tracking-[0.2em]">•••• •••• •••• {card.last4}</div>
        <div className="mt-4 flex items-end justify-between text-xs text-navy-100/80">
          <div>
            <div className="text-[10px] uppercase tracking-wide">Card Holder</div>
            <div className="text-sm font-medium text-white">{card.holder}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wide">Expires</div>
            <div className="text-sm font-medium text-white">{card.expiry}</div>
          </div>
        </div>
      </div>

      <Button
        variant={card.frozen ? "secondary" : "destructive"}
        size="sm"
        className="mt-4 w-full"
        disabled={busy}
        onClick={() => (card.frozen ? run(onUnfreeze) : setConfirming(true))}
      >
        {card.frozen ? <Unlock size={14} /> : <Lock size={14} />}
        {busy ? "Please wait…" : card.frozen ? "Unfreeze Card" : "Freeze Card"}
      </Button>

      <ConfirmationModal
        open={confirming}
        onClose={() => setConfirming(false)}
        data={{ cardLast4: card.last4 }}
        onConfirm={() => run(onFreeze)}
      />
    </div>
  );
}
