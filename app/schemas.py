"""Request and response schemas.

Pydantic validates these before the request reaches any business logic.
A bad request is rejected immediately with a clear error — the LLM never sees it.
"""

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


class ErrorResponse(BaseModel):
    error: str