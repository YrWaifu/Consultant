from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from ..models import User
from ..schemas import UserRegister, UserLogin, UserOut
from ..settings import settings
from ..repositories import UserRepository, SubscriptionRepository

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хэширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    # Преобразуем user_id в строку для JWT
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Аутентификация пользователя"""
    user_repo = UserRepository(db)
    user = user_repo.get_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def register_user(db: Session, user_data: UserRegister) -> User:
    """Регистрация нового пользователя"""
    user_repo = UserRepository(db)
    subscription_repo = SubscriptionRepository(db)
    
    hashed_password = get_password_hash(user_data.password)
    
    # Создаем пользователя
    new_user = user_repo.create(
        nickname=user_data.nickname,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    # Автоматически создаем пробную подписку на 7 дней
    subscription_repo.create_trial(user_id=new_user.id, days=7)
    
    return new_user


def get_current_user_from_cookie(request: Request, db: Session) -> Optional[User]:
    """Получение текущего пользователя из cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user_id = int(user_id)  # Явное приведение к int
    except (JWTError, ValueError, TypeError):
        return None
    
    user_repo = UserRepository(db)
    return user_repo.get_by_id(user_id)


def set_auth_cookie(response: Response, user_id: int) -> None:
    """Установка cookie с токеном авторизации"""
    access_token = create_access_token(data={"sub": user_id})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 30 дней в секундах
        samesite="lax"
    )


def clear_auth_cookie(response: Response) -> None:
    """Удаление cookie с токеном авторизации"""
    response.delete_cookie(key="access_token")

