"""Create the tables and fill them with sample data.

Run: python scripts/seed.py
"""

import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, SessionLocal, engine
from app.models import KYC, Account, Address, ServiceRequest, Transaction, User

# Fixed seed so the data is the same every time we run this.
random.seed(42)

USERS = [
    ("CUST1001", "Ananya Sharma", "ananya@example.com", "9812345601", "Gurugram", "Haryana", "122002"),
    ("CUST1002", "Rohit Verma", "rohit@example.com", "9812345602", "Bengaluru", "Karnataka", "560038"),
    ("CUST1003", "Meera Iyer", "meera@example.com", "9812345603", "Mumbai", "Maharashtra", "400050"),
]

# merchant, category, min amount, max amount
SPENDS = [
    ("Swiggy", "food", 200, 900),
    ("Zomato", "food", 250, 1000),
    ("Amazon", "shopping", 500, 5000),
    ("Uber", "transport", 100, 600),
    ("BigBasket", "groceries", 800, 3000),
    ("Netflix", "entertainment", 500, 650),
    ("Electricity Bill", "utilities", 1200, 3000),
]


def create_transactions(account, salary, months=3):
    """Generate transactions day by day and track the running balance."""
    txns = []
    balance = Decimal("50000.00")
    today = date.today()
    day = today - timedelta(days=months * 30)
    counter = 1

    while day <= today:
        entries = []

        # Salary on the 1st of every month
        if day.day == 1:
            entries.append(("credit", salary, "salary", "Monthly salary credit"))

        # Rent on the 5th
        if day.day == 5:
            entries.append(("debit", Decimal("25000"), "rent", "House rent payment"))

        # 0 to 3 random purchases each day
        for _ in range(random.randint(0, 3)):
            merchant, category, low, high = random.choice(SPENDS)
            amount = Decimal(str(random.randint(low, high)))
            entries.append(("debit", amount, category, f"{merchant} payment"))

        for txn_type, amount, category, description in entries:
            if txn_type == "debit":
                if balance < amount:
                    continue  # skip if not enough balance
                balance -= amount
            else:
                balance += amount

            txns.append(
                Transaction(
                    txn_id=f"TXN{account.id:02d}{counter:05d}",
                    account_id=account.id,
                    date=datetime.combine(day, datetime.min.time())
                    + timedelta(hours=random.randint(9, 20)),
                    type=txn_type,
                    amount=amount,
                    balance_after=balance,
                    category=category,
                    description=description,
                )
            )
            counter += 1

        day += timedelta(days=1)

    return txns, balance


def seed():
    Base.metadata.create_all(engine)
    db = SessionLocal()

    if db.query(User).count() > 0:
        print("Data already exists. Run: python scripts/reset.py")
        db.close()
        return

    total_txns = 0

    for i, (cust_id, name, email, phone, city, state, pincode) in enumerate(USERS, start=1):
        user = User(customer_id=cust_id, name=name, email=email, phone=phone)
        db.add(user)
        db.flush()  # get user.id before using it below

        # Address: one old (inactive), one current
        db.add(Address(user_id=user.id, line1="12 Old Street", city=city, state=state,
                       pincode=pincode, is_current=False))
        db.add(Address(user_id=user.id, line1=f"{i}0 Park Avenue", city=city, state=state,
                       pincode=pincode, is_current=True))

        # KYC: PAN verified for everyone, Aadhaar varies so agents see all cases
        db.add(KYC(user_id=user.id, document_type="pan",
                   document_number="XXXXX1234X", status="verified"))
        db.add(KYC(user_id=user.id, document_type="aadhaar",
                   document_number="XXXXXXXX5678",
                   status=["verified", "pending", "expired"][i - 1]))

        # One past service request
        db.add(ServiceRequest(ticket_id=f"SR100{i}", user_id=user.id,
                              request_type="cheque_book", status="completed",
                              details="25 leaves, delivered"))

        # Accounts
        for j in range(random.randint(1, 2)):
            account = Account(
                account_number=f"9{i:02d}{j}45678{i}{j}",
                user_id=user.id,
                account_type="savings" if j == 0 else "current",
                balance=Decimal("0"),
                ifsc="DEMO0001234",
                branch=f"{city} Main Branch",
                opened_on=date(2021, 1, 15),
            )
            db.add(account)
            db.flush()

            txns, final_balance = create_transactions(account, Decimal("80000"))
            db.add_all(txns)
            account.balance = final_balance
            total_txns += len(txns)

    db.commit()

    print("Seed complete:")
    print(f"  users         {db.query(User).count()}")
    print(f"  accounts      {db.query(Account).count()}")
    print(f"  transactions  {total_txns}")
    db.close()


if __name__ == "__main__":
    seed()