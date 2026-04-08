from uuid import UUID
from typing import Literal
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class RegisterResponse(BaseModel):
    user_id: UUID
    email: str
    full_name: str
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str
