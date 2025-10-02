from __future__ import annotations
from datetime import date, timedelta
from typing import Literal
from pydantic import BaseModel

class Account(BaseModel):
    id: int = 1
    role: str = "guest"
    first_name: str = ""
    last_name: str = "Гость"
    email: str = "guest@example.com"
    avatar_url: str | None = None

_state: dict = Account().model_dump()

def get_account() -> dict:
    return _state.copy()

def update_account(data: dict) -> dict:
    global _state
    cleaned = {k: v for k, v in data.items() if v is not None}
    _state |= cleaned
    return _state.copy()

class Subscription(BaseModel):
    status: Literal["none", "active"] = "none"
    plan: str | None = None           # напр. "Pro"
    price: str | None = None          # напр. "990 ₽/мес"
    renews_at: str | None = None      # ISO-строка даты, напр. "2025-12-01"
    quota_month: int | None = None    # месячный лимит проверок
    used: int | None = None           # сколько уже использовано в текущем месяце

# Память процесса для подписки
_sub_state: dict = Subscription().model_dump()

def _next_renewal_iso(days: int = 30) -> str:
    return (date.today() + timedelta(days=days)).isoformat()

def get_subscription() -> dict | None:
    """
    Вернёт dict с данными подписки, если она активна; иначе None.
    """
    if _sub_state.get("status") != "active":
        return None
    return _sub_state.copy()

def start_subscription(
    plan: str = "Pro",
    price: str = "990 ₽/мес",
    renew_days: int = 30,
    quota_month: int = 1000,
) -> dict:
    """
    Включает подписку с дефолтными (или переданными) параметрами.
    """
    global _sub_state
    _sub_state = Subscription(
        status="active",
        plan=plan,
        price=price,
        renews_at=_next_renewal_iso(renew_days),
        quota_month=quota_month,
        used=0,
    ).model_dump()
    return _sub_state.copy()

def cancel_subscription() -> dict:
    """
    Полностью отключает подписку (возврат к состоянию 'none').
    """
    global _sub_state
    _sub_state = Subscription().model_dump()
    return _sub_state.copy()

def consume_checks(n: int = 1) -> dict | None:
    """
    Сервисная утилита: отметить использование n проверок из месячного лимита.
    Возвращает текущее состояние подписки (или None, если подписки нет).
    """
    if _sub_state.get("status") != "active":
        return None
    if isinstance(_sub_state.get("used"), int):
        _sub_state["used"] = max(0, int(_sub_state["used"])) + max(0, n)
    return _sub_state.copy()
