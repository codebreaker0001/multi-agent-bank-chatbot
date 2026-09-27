import { AnimatePresence, motion } from "framer-motion";

/** Slide-over drawer — mobile sidebar and mobile context panel share this. */
const SIDE_POSITION = { left: "left-0", right: "right-0" };

export default function Drawer({ open, onClose, side = "left", children }) {
  const fromX = side === "left" ? "-100%" : "100%";
  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <motion.div
            className="absolute inset-0 bg-navy-900/40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            className={`absolute top-0 ${SIDE_POSITION[side]} h-full w-[85%] max-w-sm overflow-y-auto bg-white shadow-elevated`}
            initial={{ x: fromX }}
            animate={{ x: 0 }}
            exit={{ x: fromX }}
            transition={{ type: "tween", duration: 0.22, ease: "easeOut" }}
          >
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
