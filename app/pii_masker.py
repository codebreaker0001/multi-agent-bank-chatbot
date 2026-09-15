"""PII masker — strip sensitive data before sending anything to the LLM.

Why this matters:
  The LLM is a third-party API. We should never send it real account numbers,
  phone numbers, or email addresses. If a prompt or response is ever logged
  on Anthropic's side, no real customer data is exposed.

How it works:
  1. mask()   — scan the text, replace each PII value with a token like [ACCOUNT],
                and save the mapping  token -> real value.
  2. unmask() — after the LLM replies, swap the tokens back to real values
                so the customer sees their actual data.

Patterns covered (enough for a banking chatbot):
  - Account numbers  (10-16 digits)
  - Indian phone numbers
  - Email addresses
  - PAN card numbers  (AAAAA0000A format)
  - Aadhaar numbers   (12 digits, optionally spaced)
"""

import re
from dataclasses import dataclass, field

# Order matters — more specific patterns first
PATTERNS = [
    ("PAN",     r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    ("AADHAAR", r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b"),
    ("PHONE",   r"\b[6-9]\d{9}\b"),
    ("ACCOUNT", r"\b\d{10,16}\b"),
    ("EMAIL",   r"\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b"),
]


@dataclass
class MaskResult:
    masked_text: str
    mapping: dict = field(default_factory=dict)  # token -> original value


def mask(text: str) -> MaskResult:
    """Replace PII in text with tokens. Returns masked text + the mapping."""
    mapping = {}
    counter = {}

    for label, pattern in PATTERNS:
        def replace(m, label=label):
            original = m.group()
            # If we've already masked this exact value, reuse the same token
            for token, val in mapping.items():
                if val == original:
                    return token
            # New value — create a new numbered token
            counter[label] = counter.get(label, 0) + 1
            token = f"[{label}_{counter[label]}]" if counter[label] > 1 else f"[{label}]"
            mapping[token] = original
            return token

        text = re.sub(pattern, replace, text)

    return MaskResult(masked_text=text, mapping=mapping)


def unmask(text: str, mapping: dict) -> str:
    """Swap tokens back to real values in the LLM's response."""
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text