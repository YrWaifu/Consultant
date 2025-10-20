from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models import Check


class CheckRepository:
    """Репозиторий для работы с проверками"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(
        self, 
        user_id: int, 
        input_text: Optional[str] = None,
        input_media_path: Optional[str] = None,
        status: str = "queued"
    ) -> Check:
        """Создать новую проверку"""
        check = Check(
            user_id=user_id,
            input_text=input_text,
            input_media_path=input_media_path,
            status=status,
            created_at=datetime.utcnow()
        )
        
        self.db.add(check)
        self.db.commit()
        self.db.refresh(check)
        return check
    
    def update_result(
        self, 
        check_id: int, 
        summary: str, 
        result: dict, 
        status: str = "done"
    ) -> Optional[Check]:
        """Обновить результат проверки"""
        check = self.db.query(Check).filter(Check.id == check_id).first()
        if not check:
            return None
        
        check.status = status
        check.summary = summary
        check.result = result
        
        self.db.commit()
        self.db.refresh(check)
        return check
    
    def get_by_id(self, check_id: int) -> Optional[Check]:
        """Получить проверку по ID"""
        return self.db.query(Check).filter(Check.id == check_id).first()
    
    def get_user_checks(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Check]:
        """Получить историю проверок пользователя"""
        return (
            self.db.query(Check)
            .filter(Check.user_id == user_id)
            .filter(Check.status == "done")
            .order_by(desc(Check.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def count_user_checks(self, user_id: int) -> int:
        """Подсчитать количество проверок пользователя"""
        return (
            self.db.query(Check)
            .filter(Check.user_id == user_id)
            .filter(Check.status == "done")
            .count()
        )
    
    def get_user_stats(self, user_id: int) -> dict:
        """Получить статистику проверок пользователя"""
        checks = self.db.query(Check).filter(
            Check.user_id == user_id,
            Check.status == "done"
        ).all()
        
        total = len(checks)
        ok_count = 0
        warn_count = 0
        bad_count = 0
        
        for check in checks:
            if check.result and isinstance(check.result, dict):
                is_ok = check.result.get('is_ok', False)
                violations = check.result.get('violations', [])
                
                if is_ok:
                    ok_count += 1
                elif len(violations) > 3:
                    bad_count += 1
                else:
                    warn_count += 1
        
        return {
            "total_checks": total,
            "ok": ok_count,
            "warn": warn_count,
            "bad": bad_count
        }

