from pydantic import BaseModel
from typing import Any


class CheckCreate(BaseModel):
    text: str | None = None


class CheckOut(BaseModel):
    id: int
    status: str
    summary: str | None = None
    result: dict[str, Any] | None = None
    class Config:
        from_attributes = True