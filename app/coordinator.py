"""Coordinator agent — the brain of the chatbot.

Two responsibilities:
  1. Classify the user's intent from their message.
  2. Route to the right sub-agent based on that intent.

Why a coordinator instead of one big prompt?
  Each sub-agent has a focused system prompt and only the tools it needs.
  This keeps responses accurate and prevents, say, the account agent from
  accidentally trying to change an address.

Intent categories:
  account     → balance, account details, account number
  transaction → transaction history, statements, spending
  service     → address change, cheque book, KYC update
  unknown     → anything outside banking scope

Flow:
  user message
    → coordinator classifies intent  (one fast LLM call)
    → route to sub-agent             (another LLM call with tools)
    → return reply
"""

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

# ── intent classification ─────────────────────────────────────────────────────

INTENT_PROMPT = """You are a classifier for a banking chatbot. 
Classify the user message into exactly one of these intents:
  account     - balance inquiry, account details, account number, account status
  transaction - transaction history, past payments, statements, spending summary
  service     - address change, cheque book request, KYC update, document update

Reply with only the intent word. Nothing else.
If the message is unrelated to banking, reply: unknown"""


def classify_intent(message: str) -> str:
    """Ask the LLM to classify the intent. Returns one of: account / transaction / service / unknown."""
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0,      # deterministic — we want consistent classification
        max_tokens=10,      # intent is one word, no need for more
    )
    intent = response.choices[0].message.content.strip().lower()
    # Guard against unexpected responses
    if intent not in ("account", "transaction", "service"):
        intent = "unknown"
    return intent


# ── sub-agent system prompts ──────────────────────────────────────────────────

AGENT_PROMPTS = {
    "account": """You are the Account Agent for DemoBank. 
You help customers with balance inquiries and account details.
You have access to the customer's account information provided in the context.
Be concise, friendly, and professional. Always refer to account numbers in masked form (last 4 digits only).
If asked about something outside accounts, say you'll transfer them to the right team.""",

    "transaction": """You are the Transaction Agent for DemoBank.
You help customers view transaction history, understand their spending, and get statements.
You have access to the customer's recent transactions provided in the context.
Summarise spending clearly. Format amounts in Indian Rupees (₹).
If asked about something outside transactions, say you'll transfer them to the right team.""",

    "service": """You are the Service Agent for DemoBank.
You help customers with address changes, cheque book requests, and KYC updates.
Always confirm the details with the customer before making any changes.
For example: "I'll update your address to X. Can you confirm?"
Wait for explicit confirmation before saying the change has been made.
If asked about something outside services, say you'll transfer them to the right team.""",
}

UNKNOWN_REPLY = (
    "I can help you with account balances, transaction history, and banking services "
    "like address changes or cheque book requests. What would you like help with?"
)


# ── main entry point ──────────────────────────────────────────────────────────

def run(message: str, history: list[dict], context: str = "") -> tuple[str, str]:
    """Classify intent, route to sub-agent, return (reply, intent).

    Args:
        message:  the user's current message (already PII-masked)
        history:  conversation history from Redis [ {role, content}, ... ]
        context:  bank data fetched from DB to inject into the prompt (Day 6+)

    Returns:
        (reply, intent) — reply is the agent's response, intent is for logging
    """
    intent = classify_intent(message)

    if intent == "unknown":
        return UNKNOWN_REPLY, intent

    system_prompt = AGENT_PROMPTS[intent]
    if context:
        system_prompt += f"\n\nCustomer data:\n{context}"

    # Build the message list: system + history + current message
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=512,
    )

    reply = response.choices[0].message.content.strip()
    return reply, intent