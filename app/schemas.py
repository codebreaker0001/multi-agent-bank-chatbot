"""Request and response schemas."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_id: str
    name: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(..., min_length=1, max_length=100)


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class ServiceActionRequest(BaseModel):
    """Called after the user confirms a service change in chat."""
    action: Literal["update_address", "request_cheque_book", "update_kyc"]
    # update_address fields
    line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    # update_kyc field
    document_type: Optional[str] = None


class ServiceActionResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str