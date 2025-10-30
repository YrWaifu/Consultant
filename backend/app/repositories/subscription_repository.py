from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models import Subscription


class SubscriptionRepository:
    """Репозиторий для работы с подписками"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user_id(self, user_id: int) -> Optional[Subscription]:
        """Получить подписку пользователя"""
        return self.db.query(Subscription).filter(Subscription.user_id == user_id).first()
    
    def create_trial(self, user_id: int, days: int = 7) -> Subscription:
        """Создать пробную подписку на N дней с лимитом 5 проверок"""
        started_at = datetime.utcnow()
        expires_at = started_at + timedelta(days=days)
        
        subscription = Subscription(
            user_id=user_id,
            status="active",
            plan="trial",
            started_at=started_at,
            expires_at=expires_at,
            checks_quota=5,  # 5 проверок для trial
            checks_used=0,
            last_reset_at=started_at
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def create_pro(self, user_id: int, days: int = 30) -> Subscription:
        """Создать pro подписку на N дней с лимитом 20 проверок в неделю"""
        started_at = datetime.utcnow()
        expires_at = started_at + timedelta(days=days)
        
        subscription = Subscription(
            user_id=user_id,
            status="active",
            plan="pro",
            started_at=started_at,
            expires_at=expires_at,
            checks_quota=20,  # 20 проверок в неделю для pro
            checks_used=0,
            last_reset_at=started_at
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def _reset_weekly_quota_if_needed(self, subscription: Subscription) -> None:
        """Сброс недельной квоты для pro подписки, если прошла неделя"""
        if subscription.plan == "trial":
            # Для trial не сбрасываем квоту
            return
        
        if not subscription.last_reset_at:
            subscription.last_reset_at = subscription.started_at
        
        # Проверяем, прошла ли неделя с последнего сброса
        week_passed = datetime.utcnow() - subscription.last_reset_at >= timedelta(weeks=1)
        
        if week_passed:
            subscription.checks_used = 0
            subscription.last_reset_at = datetime.utcnow()
            self.db.commit()
    
    def is_active(self, subscription: Subscription) -> bool:
        """Проверить, активна ли подписка"""
        if subscription.status != "active":
            return False
        
        # Проверяем, не истекла ли подписка
        if datetime.utcnow() > subscription.expires_at:
            # Автоматически помечаем как истекшую
            subscription.status = "expired"
            self.db.commit()
            return False
        
        # Для pro подписки проверяем и сбрасываем недельную квоту
        self._reset_weekly_quota_if_needed(subscription)
        
        return True
    
    def has_checks_available(self, subscription: Subscription) -> bool:
        """Проверить, есть ли доступные проверки"""
        if not self.is_active(subscription):
            return False
        
        # Проверяем недельную квоту для pro подписки
        self._reset_weekly_quota_if_needed(subscription)
        
        return subscription.checks_used < subscription.checks_quota
    
    def increment_checks(self, subscription: Subscription) -> None:
        """Увеличить счетчик использованных проверок"""
        subscription.checks_used += 1
        self.db.commit()
    
    def extend_subscription(self, subscription: Subscription, days: int = 30) -> Subscription:
        """Продлить подписку на N дней"""
        subscription.expires_at = subscription.expires_at + timedelta(days=days)
        subscription.status = "active"
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def cancel_subscription(self, subscription: Subscription) -> Subscription:
        """Отменить подписку"""
        subscription.status = "cancelled"
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def add_checks(self, subscription: Subscription, amount: int = 30) -> Subscription:
        """Добавить дополнительные проверки к квоте"""
        subscription.checks_quota += amount
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

