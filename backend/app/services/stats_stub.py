from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session
from ..repositories import CheckRepository


def get_stats(user_id: Optional[int] = None, db: Optional[Session] = None) -> dict:
    """Получить статистику проверок пользователя"""
    if not user_id or not db:
        # Возвращаем пустую статистику
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=29)
        last30_dates = [(start_date + timedelta(days=i)).date().strftime('%d.%m') for i in range(30)]
        
        return {
            "total_checks": 0,
            "ok": 0,
            "bad": 0,
            "ok_percent": 0,
            "bad_percent": 0,
            "last30": [0] * 30,
            "last30_dates": last30_dates
        }
    
    check_repo = CheckRepository(db)
    stats = check_repo.get_user_stats(user_id)
    
    # Вычисляем проценты
    total = stats["total_checks"]
    ok_percent = round((stats["ok"] / total * 100)) if total > 0 else 0
    bad_percent = round((stats["bad"] / total * 100)) if total > 0 else 0
    
    # Получаем данные по дням за последние 30 дней
    daily_checks = check_repo.get_checks_by_day(user_id, days=30)
    
    # Генерируем список дат за последние 30 дней (отформатированные строки)
    from datetime import datetime, timedelta
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=29)  # 30 дней включая сегодня
    last30_dates = [(start_date + timedelta(days=i)).date().strftime('%d.%m') for i in range(30)]
    
    return {
        **stats,
        "ok_percent": ok_percent,
        "bad_percent": bad_percent,
        "last30": daily_checks,
        "last30_dates": last30_dates
    }


