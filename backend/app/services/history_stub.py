from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..repositories import CheckRepository


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
        
        if is_ok:
            badge_text = "Нарушний не обнаружено"
            badge_class = "bg-emerald-100 text-emerald-700"
        elif violations_count > 3:
            badge_text = "Нарушения"
            badge_class = "bg-rose-100 text-rose-700"
        else:
            badge_text = "Предупреждения"
            badge_class = "bg-amber-100 text-amber-700"
        
        result.append({
            "id": check.id,
            "date": check.created_at.strftime("%d.%m.%Y %H:%M"),
            "title": check.input_text[:50] + "..." if check.input_text and len(check.input_text) > 50 else check.input_text or "Проверка",
            "summary": check.summary or "Результаты проверки",
            "badge_text": badge_text,
            "badge_class": badge_class,
            "pdf_url": f"/v2/check/history/{check.id}/pdf" if check.result else None
        })
    
    return result


