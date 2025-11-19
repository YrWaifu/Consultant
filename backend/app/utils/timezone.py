"""
Утилиты для работы с временными зонами.
Московское время (UTC+3).
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

# Московская временная зона (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))


def moscow_now() -> datetime:
    """Получить текущее время в московской зоне"""
    return datetime.now(MOSCOW_TZ)


def moscow_utcnow() -> datetime:
    """Получить текущее время в московской зоне (альтернативное название для совместимости)"""
    return datetime.now(MOSCOW_TZ)


def to_moscow_tz(dt: datetime) -> datetime:
    """
    Конвертировать datetime в московскую зону.
    Если datetime без timezone - считаем его UTC.
    """
    if dt.tzinfo is None:
        # Считаем что это UTC время
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(MOSCOW_TZ)


def format_moscow_date(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
    """
    Форматировать datetime в московском времени.
    Если datetime без timezone - считаем его UTC.
    """
    moscow_dt = to_moscow_tz(dt)
    return moscow_dt.strftime(format_str)


def format_moscow_short(dt: datetime) -> str:
    """Краткий формат даты в московском времени"""
    return format_moscow_date(dt, "%d.%m.%Y")


def format_moscow_full(dt: datetime) -> str:
    """Полный формат даты и времени в московском времени"""
    return format_moscow_date(dt, "%d.%m.%Y в %H:%M")
