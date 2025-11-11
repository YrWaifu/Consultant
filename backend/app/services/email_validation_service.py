"""
Сервис для проверки валидности email адресов.
Поддерживает Mailtrap Email Validation API и фолбэк-проверку (синтаксис + MX-запись).
"""
import re
import socket
from typing import Tuple, Optional
import httpx
from fastapi import HTTPException

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

from ..settings import settings


def _format_mailtrap_reason(reason: str, email: str) -> str:
    """
    Преобразует технические причины от Mailtrap в понятные сообщения для пользователя.
    """
    reason_lower = reason.lower() if reason else ""
    
    if 'invalid' in reason_lower or 'syntax' in reason_lower:
        return "Неверный формат email адреса. Проверьте правильность написания."
    elif 'disposable' in reason_lower:
        return "Временные (одноразовые) email адреса не разрешены. Пожалуйста, используйте постоянный email."
    elif 'role' in reason_lower or 'catch-all' in reason_lower:
        return "Этот email адрес не может быть использован для регистрации."
    elif 'undeliverable' in reason_lower or 'not deliverable' in reason_lower:
        return f"Email адрес {email} не может получать почту. Проверьте правильность написания."
    elif 'domain' in reason_lower and 'not found' in reason_lower:
        return f"Домен в email адресе не существует. Проверьте правильность написания."
    else:
        return f"Email адрес {email} не прошел проверку. Пожалуйста, проверьте правильность написания или используйте другой email."


def validate_email_syntax(email: str) -> bool:
    """
    Проверка синтаксиса email адреса.
    Использует простое регулярное выражение для базовой проверки.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_mx_record(domain: str) -> bool:
    """
    Проверка наличия MX-записи для домена.
    Возвращает True, если домен имеет MX-запись или A-запись (для fallback).
    """
    if DNS_AVAILABLE:
        try:
            # Сначала проверяем MX-записи
            mx_records = dns.resolver.resolve(domain, 'MX')
            if mx_records:
                return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            pass
        except Exception:
            # Если произошла ошибка, переходим к проверке A-записи
            pass
        
        # Если MX-записей нет, проверяем A-запись (некоторые почтовые серверы используют A-запись)
        try:
            a_records = dns.resolver.resolve(domain, 'A')
            if a_records:
                return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            return False
        except Exception:
            # Fallback на socket
            try:
                socket.gethostbyname(domain)
                return True
            except socket.gaierror:
                return False
    else:
        # Если dnspython недоступен, используем только socket
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False
    
    return False


async def validate_with_mailtrap(email: str) -> Tuple[bool, Optional[str]]:
    """
    Проверка email через Mailtrap Email Validation API.
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not settings.MAILTRAP_API_TOKEN:
        return None, "Mailtrap API токен не настроен"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://mailtrap.io/api/v1/email_validation/check",
                params={"email": email},
                headers={"Authorization": f"Bearer {settings.MAILTRAP_API_TOKEN}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Mailtrap возвращает статус валидации
                # Обычно есть поля типа 'valid', 'deliverable', 'catch_all' и т.д.
                is_valid = data.get('valid', False) or data.get('deliverable', False)
                if not is_valid:
                    # Преобразуем технические причины в понятные сообщения
                    reason = data.get('reason', '')
                    user_friendly_reason = _format_mailtrap_reason(reason, email)
                    return False, user_friendly_reason
                return True, None
            elif response.status_code == 401:
                return None, "Неверный Mailtrap API токен"
            else:
                # Если API недоступно, возвращаем None для использования fallback
                return None, f"Mailtrap API вернул статус {response.status_code}"
                
    except httpx.TimeoutException:
        return None, "Таймаут при обращении к Mailtrap API"
    except Exception as e:
        # В случае любой ошибки возвращаем None для использования fallback
        return None, f"Ошибка при обращении к Mailtrap API: {str(e)}"


async def validate_email_fallback(email: str) -> Tuple[bool, str]:
    """
    Фолбэк-проверка email: синтаксис + MX-запись.
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    # Проверка синтаксиса
    if not validate_email_syntax(email):
        return False, "Пожалуйста, введите корректный email адрес. Пример: name@example.com"
    
    # Извлекаем домен
    try:
        domain = email.split('@')[1]
    except IndexError:
        return False, "Пожалуйста, введите корректный email адрес. Пример: name@example.com"
    
    # Проверка MX-записи
    if not validate_mx_record(domain):
        return False, f"Похоже, что домен {domain} не существует или не принимает почту. Проверьте правильность написания email адреса."
    
    return True, ""


async def validate_email(email: str) -> Tuple[bool, str]:
    """
    Основная функция проверки email.
    Сначала пытается использовать Mailtrap API, если токен настроен.
    Если Mailtrap недоступен или токен не настроен, использует фолбэк-проверку.
    
    Args:
        email: Email адрес для проверки
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
        
    Raises:
        HTTPException: Если email невалиден
    """
    # Сначала пробуем Mailtrap API, если токен настроен
    if settings.MAILTRAP_API_TOKEN:
        mailtrap_result, mailtrap_error = await validate_with_mailtrap(email)
        
        # Если получили результат от Mailtrap
        if mailtrap_result is not None:
            if mailtrap_result:
                return True, ""
            else:
                # mailtrap_error уже содержит понятное сообщение от _format_mailtrap_reason
                raise HTTPException(
                    status_code=400,
                    detail=mailtrap_error or "Email адрес недействителен. Пожалуйста, проверьте правильность написания."
                )
        # Если Mailtrap недоступен, используем fallback (продолжаем ниже)
    
    # Фолбэк-проверка: синтаксис + MX-запись
    is_valid, error_message = await validate_email_fallback(email)
    
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Email адрес не прошел проверку: {error_message}"
        )
    
    return True, ""

