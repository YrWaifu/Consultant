from __future__ import annotations
from random import randint
from typing import Optional
from sqlalchemy.orm import Session
from ..repositories import CheckRepository


def get_stats(user_id: Optional[int] = None, db: Optional[Session] = None) -> dict:
    """Получить статистику проверок пользователя"""
    if not user_id or not db:
        # Возвращаем пустую статистику
        return {
            "total_checks": 0,
            "ok": 0,
            "warn": 0,
            "bad": 0,
            "last30": [0] * 30
        }
    
    check_repo = CheckRepository(db)
    stats = check_repo.get_user_stats(user_id)
    
    # TODO: Добавить реальные данные для графика за последние 30 дней
    # Пока используем случайные значения для графика
    last30 = [randint(5, 100) for _ in range(30)]
    
    return {
        **stats,
        "last30": last30
    }


