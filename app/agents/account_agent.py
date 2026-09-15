"""Account agent — fetches account data from the DB and formats it for the LLM.

The coordinator calls get_context() to get a text summary of the customer's
accounts. This gets injected into the agent's system prompt so the LLM can
answer questions like "what's my balance?" without making any tool calls —
the data is already in the prompt.

Why not use MCP tool calls here?
  For a resume project, injecting context directly is simpler to explain
  and easier to debug. The LLM doesn't need to decide which tool to call —
  we always give it the full account picture upfront.
"""

from sqlalchemy.orm import Session

from app.models import Account, User


def get_context(customer_id: str, db: Session) -> str:
    """Return a plain-text summary of the customer's accounts for the LLM prompt."""
    user = db.query(User).filter(User.customer_id == customer_id).first()
    if not user:
        return "No account information found."

    accounts = db.query(Account).filter(Account.user_id == user.id).all()
    if not accounts:
        return "No accounts found for this customer."

    lines = [f"Customer: {user.name} (ID: {customer_id})"]
    for acc in accounts:
        lines.append(
            f"- Account: {acc.masked_number} | Type: {acc.account_type} | "
            f"Balance: ₹{acc.balance:,.2f} | Status: {acc.status} | "
            f"IFSC: {acc.ifsc} | Branch: {acc.branch}"
        )
    return "\n".join(lines)