from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from ..models import User


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_nickname(self, nickname: str) -> Optional[User]:
        """Получить пользователя по никнейму"""
        return self.db.query(User).filter(User.nickname == nickname).first()
    
    def create(self, nickname: str, email: str, hashed_password: str) -> User:
        """Создать нового пользователя"""
        # Проверяем уникальность email
        if self.get_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        
        # Проверяем уникальность nickname
        if self.get_by_nickname(nickname):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким никнеймом уже существует"
            )
        
        user = User(
            nickname=nickname,
            email=email,
            hashed_password=hashed_password
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка при создании пользователя"
            )
    
    def update(self, user: User, **kwargs) -> User:
        """Обновить данные пользователя"""
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                # Проверяем уникальность при изменении email
                if key == "email" and value != user.email:
                    existing = self.get_by_email(value)
                    if existing and existing.id != user.id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email уже используется другим пользователем"
                        )
                
                # Проверяем уникальность при изменении nickname
                if key == "nickname" and value != user.nickname:
                    existing = self.get_by_nickname(value)
                    if existing and existing.id != user.id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Никнейм уже используется другим пользователем"
                        )
                
                setattr(user, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка при обновлении пользователя"
            )
    
    def delete(self, user: User) -> None:
        """Удалить пользователя"""
        self.db.delete(user)
        self.db.commit()

