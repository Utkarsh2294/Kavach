from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from .agent import CamelModel

class UserResponse(CamelModel):
    id: UUID
    name: str
    email: str
    role: str
    organization_id: UUID
    created_at: datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(CamelModel):
    user: UserResponse
    access_token: str
    refresh_token: str

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class SignupResponse(CamelModel):
    user: UserResponse
    access_token: str
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class RefreshResponse(CamelModel):
    access_token: str
    refresh_token: str

class MessageResponse(BaseModel):
    message: str

class MeResponse(CamelModel):
    user: UserResponse

class UserUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
