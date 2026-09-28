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

Intent is classified once by the caller (app/main.py — it also needs the
intent to pick which agent's get_context() to call for DB data), and passed
into run() rather than reclassified here, so each message costs one
classification call, not two.

Provider: LLM_PROVIDER=groq (default, what the deployed backend uses) or
LLM_PROVIDER=ollama (local dev — nothing leaves the machine Ollama runs on).
Ollama exposes an OpenAI-compatible endpoint, so the same openai.OpenAI
client just gets pointed at localhost instead of Groq's API — same
request/response shape either way, only the client and model name differ.
"""

from app.config import (
    GROQ_API_KEY, GROQ_MODEL, LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL,
)

if LLM_PROVIDER == "ollama":
    from openai import OpenAI

    client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")  # key is required by the SDK, ignored by Ollama
    MODEL = OLLAMA_MODEL
else:
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    MODEL = GROQ_MODEL

# reasoning_effort is a Groq/gpt-oss-specific knob most Ollama models don't
# recognize — only pass it when it means something.
_EXTRA_KWARGS = {"reasoning_effort": "low"} if LLM_PROVIDER != "ollama" else {}

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
        model=MODEL,
        messages=[
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0,   # deterministic — we want consistent classification
        max_tokens=200,  # gpt-oss spends tokens on internal reasoning before the answer
        **_EXTRA_KWARGS,
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

def run(intent: str, message: str, history: list[dict], context: str = "") -> str:
    """Route to the sub-agent for `intent` and return its reply.

    Args:
        intent:   already-classified intent (account/transaction/service/unknown)
        message:  the user's current message (already PII-masked)
        history:  conversation history from Redis [ {role, content}, ... ]
        context:  bank data fetched from DB to inject into the prompt
    """
    if intent == "unknown":
        return UNKNOWN_REPLY

    system_prompt = AGENT_PROMPTS[intent]
    if context:
        system_prompt += f"\n\nCustomer data:\n{context}"

    # Build the message list: system + history + current message
    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=512,
        **_EXTRA_KWARGS,
    )

    return response.choices[0].message.content.strip()