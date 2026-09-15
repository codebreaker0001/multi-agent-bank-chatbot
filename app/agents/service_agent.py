"""Service agent — handles address change, cheque book request, KYC update.

Key design: confirm before write.
  The agent proposes the change and asks "Can you confirm? (yes/no)"
  Only when the user replies "yes" does it write to the database.

Why confirm before write?
  Mutations based on a misunderstood message are hard to undo and erode
  customer trust. A confirmation step catches errors cheaply.

Three operations:
  update_address(user_id, new_address)   → marks old address inactive, inserts new one
  request_cheque_book(user_id, account)  → creates a ServiceRequest ticket
  update_kyc(user_id, doc_type, doc_no)  → updates KYC record status to pending
"""

from datetime import date

from sqlalchemy.orm import Session

from app.models import KYC, Account, Address, ServiceRequest, User


def get_context(customer_id: str, db: Session) -> str:
    """Return current address and KYC status so the agent knows the current state."""
    user = db.query(User).filter(User.customer_id == customer_id).first()
    if not user:
        return "No customer information found."

    lines = [f"Customer: {user.name}"]

    # Current address
    current_address = (
        db.query(Address)
        .filter(Address.user_id == user.id, Address.is_current == True)
        .first()
    )
    if current_address:
        lines.append(
            f"Current Address: {current_address.line1}, {current_address.city}, "
            f"{current_address.state} - {current_address.pincode}"
        )
    else:
        lines.append("Current Address: Not on record")

    # KYC status
    kyc_records = db.query(KYC).filter(KYC.user_id == user.id).all()
    for kyc in kyc_records:
        lines.append(f"KYC - {kyc.document_type.upper()}: {kyc.status}")

    # Open service requests
    open_requests = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.user_id == user.id,
                ServiceRequest.status == "submitted")
        .all()
    )
    if open_requests:
        for req in open_requests:
            lines.append(f"Pending Request: {req.ticket_id} - {req.request_type}")

    return "\n".join(lines)


def update_address(customer_id: str, line1: str, city: str,
                   state: str, pincode: str, db: Session) -> str:
    """Mark old address inactive and insert the new one. Returns a confirmation message."""
    user = db.query(User).filter(User.customer_id == customer_id).first()
    if not user:
        return "Customer not found."

    # Deactivate current address
    db.query(Address).filter(
        Address.user_id == user.id, Address.is_current == True
    ).update({"is_current": False})

    # Insert new address
    db.add(Address(
        user_id=user.id,
        line1=line1, city=city, state=state, pincode=pincode,
        is_current=True,
        updated_on=date.today(),
    ))
    db.commit()
    return f"Address updated to: {line1}, {city}, {state} - {pincode}"


def request_cheque_book(customer_id: str, db: Session) -> str:
    """Create a cheque book service request ticket."""
    user = db.query(User).filter(User.customer_id == customer_id).first()
    if not user:
        return "Customer not found."

    account = db.query(Account).filter(Account.user_id == user.id).first()

    # Generate a simple ticket ID
    count = db.query(ServiceRequest).count()
    ticket_id = f"SR{date.today().strftime('%Y%m')}{count + 1:04d}"

    db.add(ServiceRequest(
        ticket_id=ticket_id,
        user_id=user.id,
        request_type="cheque_book",
        status="submitted",
        details="25 leaves requested via chatbot",
        created_on=date.today(),
    ))
    db.commit()
    return f"Cheque book requested. Ticket ID: {ticket_id}. Delivery in 5-7 working days."


def update_kyc(customer_id: str, document_type: str, db: Session) -> str:
    """Set KYC status to pending — bank staff will verify and update."""
    user = db.query(User).filter(User.customer_id == customer_id).first()
    if not user:
        return "Customer not found."

    kyc = db.query(KYC).filter(
        KYC.user_id == user.id,
        KYC.document_type == document_type.lower()
    ).first()

    if kyc:
        kyc.status = "pending"
        kyc.updated_on = date.today()
    else:
        db.add(KYC(
            user_id=user.id,
            document_type=document_type.lower(),
            document_number="PENDING",
            status="pending",
            updated_on=date.today(),
        ))
    db.commit()
    return f"KYC update request submitted for {document_type.upper()}. Our team will contact you within 2 working days."