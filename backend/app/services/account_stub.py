from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Literal, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models import User, Subscription
from ..repositories import UserRepository, SubscriptionRepository


class Account(BaseModel):
    id: int = 1
    role: str = "guest"
    nickname: str = "Гость"
    email: str = "guest@example.com"
    avatar_url: str | None = None


def get_account(current_user: Optional[User] = None) -> dict:
    """Получение данных аккаунта текущего пользователя"""
    if current_user:
        return {
            "id": current_user.id,
            "role": "user",
            "nickname": current_user.nickname,
            "email": current_user.email,
            "avatar_url": None,  # Пока без аватара
        }
    # Возвращаем данные гостя если пользователь не авторизован
    return Account().model_dump()


def update_account(data: dict, current_user: Optional[User] = None, db: Optional[Session] = None) -> dict:
    """Обновление данных аккаунта"""
    if current_user and db:
        user_repo = UserRepository(db)
        # Фильтруем только те поля, которые можно обновить
        update_data = {}
        
        # Email нельзя менять после регистрации
        # if "email" in data and data["email"]:
        #     update_data["email"] = data["email"]
        
        if "nickname" in data and data["nickname"]:
            update_data["nickname"] = data["nickname"]
        
        # Обновляем через репозиторий
        if update_data:
            updated_user = user_repo.update(current_user, **update_data)
            return get_account(updated_user)
        
        return get_account(current_user)
    
    return Account().model_dump()

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

def get_subscription(user_id: int, db: Session) -> dict | None:
    """
    Вернёт dict с данными подписки, если она активна; иначе None.
    """
    subscription_repo = SubscriptionRepository(db)
    subscription = subscription_repo.get_by_user_id(user_id)
    
    if not subscription:
        return None
    
    # Проверяем активность подписки
    is_active = subscription_repo.is_active(subscription)
    
    if not is_active:
        return None
    
    # Форматируем дату истечения
    days_left = (subscription.expires_at - datetime.utcnow()).days
    
    return {
        "status": subscription.status,
        "plan": "Пробная" if subscription.plan == "trial" else "Pro",
        "price": "Бесплатно" if subscription.plan == "trial" else "990 ₽/мес",
        "renews_at": subscription.expires_at.isoformat(),
        "expires_at_formatted": subscription.expires_at.strftime("%d.%m.%Y"),
        "days_left": days_left,
        "quota_month": subscription.checks_quota,
        "used": subscription.checks_used,
    }

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
