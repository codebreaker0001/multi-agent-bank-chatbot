import { AlertTriangle } from "lucide-react";
import Modal from "../ui/Modal";
import Button from "../ui/Button";

/**
 * Confirm-before-you-act for freezing a card — a real action (Account.card_frozen
 * in Postgres), just not one worth doing by accident.
 */
export default function ConfirmationModal({ open, onClose, data, onConfirm }) {
  return (
    <Modal open={open} onClose={onClose}>
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-full bg-warning-bg text-warning">
        <AlertTriangle size={20} />
      </div>

      <h3 className="text-lg font-semibold text-navy-900">Block card ending in {data.cardLast4}?</h3>
      <p className="mt-1 text-sm text-navy-400">You won't be able to use this card until you unfreeze it.</p>

      <div className="mt-5 flex gap-3">
        <Button variant="secondary" className="flex-1" onClick={onClose}>
          Cancel
        </Button>
        <Button
          variant="destructive"
          className="flex-1"
          onClick={() => {
            onConfirm();
            onClose();
          }}
        >
          Block Card
        </Button>
      </div>
    </Modal>
  );
}
