"""
Сервис для проверки валидности email адресов.
Поддерживает Mailtrap Email Validation API и фолбэк-проверку (синтаксис + MX-запись).
"""
import re
import socket
from typing import Tuple, Optional
import httpx
from fastapi import HTTPException
import asyncio

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

from ..settings import settings

# Кэш для результатов проверки доменов (TTL ~5 минут)
_domain_cache = {}


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


async def validate_mx_record(domain: str) -> bool:
    """
    Быстрая проверка наличия MX-записи для домена.
    Использует короткие таймауты и кэширование для ускорения.
    Возвращает True, если домен имеет MX-запись или A-запись (для fallback).
    """
    # Проверяем кэш
    if domain in _domain_cache:
        return _domain_cache[domain]
    
    # Устанавливаем короткие таймауты для DNS (0.5 секунды вместо дефолтных 5-10)
    if DNS_AVAILABLE:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 0.5  # 500ms вместо дефолтных 5-10 секунд
        resolver.lifetime = 0.5
        
        # Параллельно проверяем MX и A записи (оборачиваем синхронные DNS-запросы в executor)
        loop = asyncio.get_event_loop()
        
        async def check_mx():
            try:
                mx_records = await loop.run_in_executor(
                    None, 
                    lambda: resolver.resolve(domain, 'MX', raise_on_no_answer=False)
                )
                return bool(mx_records)
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
                return False
            except Exception:
                return False
        
        async def check_a():
            try:
                a_records = await loop.run_in_executor(
                    None,
                    lambda: resolver.resolve(domain, 'A', raise_on_no_answer=False)
                )
                return bool(a_records)
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
                return False
            except Exception:
                return False
        
        async def check_socket():
            try:
                # Используем socket с коротким таймаутом
                def _check():
                    old_timeout = socket.getdefaulttimeout()
                    socket.setdefaulttimeout(0.5)
                    try:
                        socket.gethostbyname(domain)
                        return True
                    finally:
                        socket.setdefaulttimeout(old_timeout)
                return await loop.run_in_executor(None, _check)
            except (socket.gaierror, socket.timeout, OSError):
                return False
        
        # Выполняем проверки параллельно и берем первый успешный результат
        try:
            # Запускаем все проверки параллельно с общим таймаутом 0.8 секунды
            results = await asyncio.wait_for(
                asyncio.gather(
                    check_mx(),
                    check_a(),
                    check_socket(),
                    return_exceptions=True
                ),
                timeout=0.8
            )
            
            # Если хотя бы одна проверка успешна - домен валиден
            is_valid = any(r is True for r in results if not isinstance(r, Exception))
            _domain_cache[domain] = is_valid
            return is_valid
        except asyncio.TimeoutError:
            # При таймауте считаем домен невалидным
            _domain_cache[domain] = False
            return False
    else:
        # Если dnspython недоступен, используем только socket с коротким таймаутом
        try:
            socket.setdefaulttimeout(0.5)
            socket.gethostbyname(domain)
            _domain_cache[domain] = True
            return True
        except (socket.gaierror, socket.timeout):
            _domain_cache[domain] = False
            return False
        finally:
            socket.setdefaulttimeout(None)
    
    return False


async def validate_with_mailtrap(email: str) -> Tuple[bool, Optional[str]]:
    """
    Проверка email через Mailtrap Email Validation API.
    Оптимизирована с коротким таймаутом.
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not settings.MAILTRAP_API_TOKEN:
        return None, "Mailtrap API токен не настроен"
    
    try:
        # Уменьшаем таймаут с 10 до 2 секунд для ускорения
        async with httpx.AsyncClient(timeout=2.0) as client:
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
    Оптимизирована для быстрой работы.
    
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
    
    # Проверка MX-записи (теперь асинхронная)
    if not await validate_mx_record(domain):
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

