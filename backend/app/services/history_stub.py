from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..repositories import CheckRepository


def _format_history_date(dt: Optional[datetime]) -> str:
    """
    Форматирование даты для истории проверок.
    В БД время проверки уже сохраняется в московском часовом поясе (без tzinfo),
    поэтому здесь мы просто выводим его «как есть», без дополнительного сдвига.
    """
    if not dt:
        return ""
    return dt.strftime("%d.%m.%Y %H:%M")


def list_history(user_id: Optional[int] = None, db: Optional[Session] = None) -> List[Dict]:
    """Получить историю проверок пользователя"""
    if not user_id or not db:
        # Возвращаем пустой список если нет пользователя
        return []
    
    check_repo = CheckRepository(db)
    checks = check_repo.get_user_checks(user_id, limit=50)
    
    result = []
    for check in checks:
        # Определяем статус по результатам
        is_ok = check.result.get('is_ok', False) if check.result else False
        violations_count = len(check.result.get('violations', [])) if check.result else 0
        
        # Реклама либо без нарушений, либо с нарушениями
        if is_ok and violations_count == 0:
            badge_text = "Нарушений не обнаружено"
            badge_class = "bg-emerald-100 text-emerald-700"
        else:
            # Любое количество нарушений (даже 1) = с нарушениями
            badge_text = "Есть нарушения"
            badge_class = "bg-rose-100 text-rose-950"
        
        result.append({
            "id": check.id,
            "date": _format_history_date(check.created_at),
            "title": check.input_text[:50] + "..." if check.input_text and len(check.input_text) > 50 else check.input_text or "Проверка",
            "summary": check.summary or "Результаты проверки",
            "badge_text": badge_text,
            "badge_class": badge_class,
            "pdf_url": f"/v2/check/history/{check.id}/pdf" if check.result else None
        })
    
    return result


