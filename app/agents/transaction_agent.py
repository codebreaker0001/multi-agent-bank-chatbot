"""Transaction agent — fetches transaction data from the DB for the LLM.

get_context() returns the last 10 transactions plus a category-wise spending
summary for the current month. Both are injected into the agent prompt so the
LLM can answer history and spending questions directly.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Account, Transaction, User


def get_context(customer_id: str, db: Session) -> str:
    """Return recent transactions and monthly spending summary for the LLM prompt."""
    user = db.query(User).filter(User.customer_id == customer_id).first()
    if not user:
        return "No transaction information found."

    # Get the customer's primary account (first one)
    account = db.query(Account).filter(Account.user_id == user.id).first()
    if not account:
        return "No accounts found."

    # Last 10 transactions, newest first
    recent = (
        db.query(Transaction)
        .filter(Transaction.account_id == account.id)
        .order_by(Transaction.date.desc())
        .limit(10)
        .all()
    )

    lines = [f"Account: {account.masked_number} | Current Balance: ₹{account.balance:,.2f}", ""]
    lines.append("Recent Transactions (latest 10):")
    if not recent:
        lines.append("  No transactions found.")
    else:
        for txn in recent:
            sign = "-" if txn.type == "debit" else "+"
            lines.append(
                f"  {txn.date.strftime('%d %b %Y')} | {sign}₹{txn.amount:,.2f} | "
                f"{txn.category} | {txn.description}"
            )

    # Monthly spending by category (current month, debits only)
    month_start = date.today().replace(day=1)
    monthly = (
        db.query(Transaction)
        .filter(
            Transaction.account_id == account.id,
            Transaction.type == "debit",
            Transaction.date >= month_start,
        )
        .all()
    )

    if monthly:
        lines.append("\nThis Month's Spending by Category:")
        by_category: dict[str, Decimal] = {}
        for txn in monthly:
            cat = txn.category or "other"
            by_category[cat] = by_category.get(cat, Decimal("0")) + txn.amount
        for cat, total in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {cat.capitalize()}: ₹{total:,.2f}")

    return "\n".join(lines)