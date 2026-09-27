/**
 * Lightweight client-side keyword match, purely to decide which mock card
 * the right-side panel highlights. This is NOT the real intent classifier —
 * that runs server-side in app/coordinator.py and only returns text, never
 * a structured intent back to the frontend. This just makes the panel feel
 * responsive to the conversation.
 */
export function inferContext(message) {
  const text = message.toLowerCase();
  if (/spend|spending|category|budget/.test(text)) return "spending";
  if (/card|freeze|block|unfreeze/.test(text)) return "card";
  if (/transaction|history|statement|payment/.test(text)) return "transactions";
  if (/balance|available/.test(text)) return "balance";
  return null;
}
