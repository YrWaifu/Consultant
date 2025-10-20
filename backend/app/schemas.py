from pydantic import BaseModel, EmailStr
from typing import Any
from datetime import datetime


class CheckCreate(BaseModel):
    text: str | None = None


class CheckOut(BaseModel):
    id: int
    status: str
    summary: str | None = None
    result: dict[str, Any] | None = None
    class Config:
        from_attributes = True


# Auth schemas
class UserRegister(BaseModel):
    nickname: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    nickname: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str