from fastapi import APIRouter, Request, Form, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..services.news_stub import list_news, get_news_detail
from ..services.laws_stub import get_law_index, get_article, search_laws
from ..services.account_stub import (
    get_account,
    get_subscription, start_subscription, cancel_subscription,
)
from ..repositories import SubscriptionRepository, CheckRepository
from ..services.history_stub import list_history
from ..services.stats_stub import get_stats
from ..services.pdf_generator import generate_pdf_report
from ..workers.queue import queue, process_ad_check_task
from ..services.auth_service import (
    authenticate_user, register_user, get_current_user_from_cookie,
    set_auth_cookie, clear_auth_cookie
)
from ..schemas import UserRegister, UserLogin
from ..db import SessionLocal

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")


# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper функция для добавления current_user в контекст
def get_template_context(request: Request, db: Session, **kwargs):
    """Получает базовый контекст для всех шаблонов с информацией о текущем пользователе"""
    current_user = get_current_user_from_cookie(request, db)
    return {
        "request": request,
        "current_user": current_user,
        **kwargs
    }


@router.get("/", response_class=HTMLResponse, name="web_v2_check")
async def index(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)

    # Проверяем подписку
    if not current_user:
        # Гость не может делать проверки
        return templates.TemplateResponse("pages/check_no_access_v2.html", get_template_context(request, db))

    subscription_repo = SubscriptionRepository(db)
    subscription = subscription_repo.get_by_user_id(current_user.id)

    if not subscription or not subscription_repo.is_active(subscription):
        # Подписка истекла или отсутствует
        return templates.TemplateResponse("pages/check_no_access_v2.html", get_template_context(request, db))

    # Передаем информацию о квоте
    return templates.TemplateResponse("pages/check_v2.html",
        get_template_context(request, db,
            checks_used=subscription.checks_used,
            checks_quota=subscription.checks_quota,
            checks_remaining=subscription.checks_quota - subscription.checks_used
        )
    )


@router.get("/v2/news", response_class=HTMLResponse, name="web_v2_news")
async def news_page(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    items = list_news(q)
    return templates.TemplateResponse(
        "pages/news_list_v2.html",
        get_template_context(request, db, items=items)
    )


@router.get("/v2/news/{news_id}", response_class=HTMLResponse, name="web_v2_news_detail")
async def news_detail_page(request: Request, news_id: int, db: Session = Depends(get_db)):
    news = get_news_detail(news_id)
    if not news:
        return RedirectResponse(url="/v2/news", status_code=303)
    return templates.TemplateResponse(
        "pages/news_detail_v2.html",
        get_template_context(request, db, news=news)
    )


@router.get("/v2/search", response_class=HTMLResponse, name="web_v2_search")
async def search_page(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    news_results = list_news(q) if q else []
    law_results = search_laws(q) if q else []
    return templates.TemplateResponse(
        "pages/search_v2.html",
        get_template_context(request, db, query=q, news_results=news_results, law_results=law_results)
    )


@router.get("/v2/check", response_class=HTMLResponse, name="web_v2_check")
async def check_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)

    # Проверяем подписку
    if not current_user:
        # Гость не может делать проверки
        return templates.TemplateResponse("pages/check_no_access_v2.html", get_template_context(request, db))

    subscription_repo = SubscriptionRepository(db)
    subscription = subscription_repo.get_by_user_id(current_user.id)

    if not subscription or not subscription_repo.is_active(subscription):
        # Подписка истекла или отсутствует
        return templates.TemplateResponse("pages/check_no_access_v2.html", get_template_context(request, db))

    # Передаем информацию о квоте
    return templates.TemplateResponse("pages/check_v2.html",
        get_template_context(request, db,
            checks_used=subscription.checks_used,
            checks_quota=subscription.checks_quota,
            checks_remaining=subscription.checks_quota - subscription.checks_used
        )
    )


@router.post("/v2/check", response_class=HTMLResponse, name="web_v2_check_submit")
async def check_submit(
    request: Request,
    text: str | None = Form(None),
    claims: list[str] | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    # Если прикреплен файл, читаем его в байты
    audio_bytes = None
    audio_content_type = None

    if file and file.filename:
        audio_bytes = await file.read()
        audio_content_type = file.content_type

    current_user = get_current_user_from_cookie(request, db)

    # Проверяем авторизацию и подписку
    if not current_user:
        return RedirectResponse(url="/v2/auth/login", status_code=303)

    subscription_repo = SubscriptionRepository(db)
    subscription = subscription_repo.get_by_user_id(current_user.id)

    if not subscription or not subscription_repo.is_active(subscription):
        return RedirectResponse(url="/v2/account/subscription", status_code=303)

    # Проверяем доступные проверки
    if not subscription_repo.has_checks_available(subscription):
        # Лимит исчерпан - перенаправляем на страницу подписки
        return templates.TemplateResponse(
            "pages/check_limit_reached_v2.html",
            get_template_context(request, db, subscription=subscription)
        )

    # Увеличиваем счетчик использованных проверок
    subscription_repo.increment_checks(subscription)

    # Создаем запись о проверке в БД
    check_repo = CheckRepository(db)
    check = check_repo.create(
        user_id=current_user.id,
        input_text=text,
        input_media_path=None,  # TODO: обработка файлов
        status="queued"
    )

    # Создаем фоновую задачу для обработки ML модели
    # Передаем check_id для сохранения результата в БД
    job = queue.enqueue(process_ad_check_task, text, audio_bytes, audio_content_type, check.id)

    # Перенаправляем на страницу ожидания с ID задачи
    return RedirectResponse(url=f"/v2/check/status/{job.id}", status_code=303)


@router.get("/v2/check/status/{job_id}", response_class=HTMLResponse, name="web_v2_check_status")
async def check_status_page(request: Request, job_id: str, db: Session = Depends(get_db)):
    """Страница ожидания результата проверки"""
    return templates.TemplateResponse("pages/check_status_v2.html",
        get_template_context(request, db, job_id=job_id)
    )


@router.get("/api/v2/check/status/{job_id}", name="api_v2_check_status")
async def check_status_api(job_id: str):
    """API для проверки статуса задачи"""
    try:
        from rq.job import Job
        from ..workers.queue import redis
        
        print(f"🔍 Проверяем статус задачи: {job_id}")
        
        job = Job.fetch(job_id, connection=redis)
        print(f"📝 Статус задачи: {job.get_status()}")
        
        if job.is_finished:
            print("✅ Задача завершена успешно")
            
            # Дополнительная защита: преобразуем любые datetime объекты в строки
            result = job.result
            if isinstance(result, dict):
                def serialize_dates(obj):
                    if isinstance(obj, dict):
                        return {k: serialize_dates(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [serialize_dates(item) for item in obj]
                    elif hasattr(obj, 'isoformat'):  # datetime, date объекты
                        return obj.isoformat()
                    else:
                        return obj
                
                result = serialize_dates(result)
            
            return JSONResponse({
                "status": "completed",
                "result": result
            })
        elif job.is_failed:
            print(f"❌ Задача провалилась: {job.exc_info}")
            return JSONResponse({
                "status": "failed", 
                "error": str(job.exc_info)
            })
        else:
            print("⏳ Задача еще выполняется")
            return JSONResponse({
                "status": "processing"
            })
            
    except Exception as e:
        print(f"🚨 Ошибка при проверке статуса: {e}")
        return JSONResponse({
            "status": "error",
            "error": f"Задача не найдена: {str(e)}"
        }, status_code=200)  # Изменяем на 200, чтобы JS мог обработать ответ


@router.get("/v2/check/result/{job_id}", response_class=HTMLResponse, name="web_v2_check_result")
async def check_result_page(request: Request, job_id: str, db: Session = Depends(get_db)):
    """Страница с результатом проверки"""
    try:
        from rq.job import Job
        from ..workers.queue import redis
        
        job = Job.fetch(job_id, connection=redis)
        
        if job.is_finished:
            data = job.result
            data["job_id"] = job_id  # Передаем job_id в шаблон для PDF ссылки
            return templates.TemplateResponse("pages/check_report_v2.html",
                get_template_context(request, db, **data))
        else:
            # Если задача еще не завершена, перенаправляем на страницу ожидания
            return RedirectResponse(url=f"/v2/check/status/{job_id}", status_code=303)
            
    except Exception:
        # Если задача не найдена, перенаправляем на главную
        return RedirectResponse(url="/v2/check", status_code=303)


@router.get("/v2/check/result/{job_id}/pdf", name="web_v2_check_result_pdf")
async def check_result_pdf(job_id: str):
    """Скачивание PDF отчета"""
    try:
        from rq.job import Job
        from ..workers.queue import redis
        
        job = Job.fetch(job_id, connection=redis)
        
        if job.is_finished:
            data = job.result
            pdf_bytes = generate_pdf_report(data)
            
            headers = {
                "Content-Disposition": f"attachment; filename=report_{job_id[:8]}.pdf",
                "Content-Type": "application/pdf",
            }
            return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
        else:
            # Если задача еще не завершена, перенаправляем на страницу ожидания
            return RedirectResponse(url=f"/v2/check/status/{job_id}", status_code=303)
            
    except Exception:
        # Если задача не найдена, перенаправляем на главную
        return RedirectResponse(url="/v2/check", status_code=303)


# Страница профиля удалена: используем email как отображаемое имя, 
# и перенаправляем пользователей на подписку/историю/статистику.

@router.get("/v2/laws", response_class=HTMLResponse, name="web_v2_laws")
async def laws_index(request: Request, db: Session = Depends(get_db)):
    data = get_law_index()
    return templates.TemplateResponse(
        "pages/laws_index_v2.html",
        get_template_context(request, db, **data)
    )

@router.get("/v2/laws/article/{article_id}", response_class=HTMLResponse, name="web_v2_law_article")
async def laws_article(request: Request, article_id: str, db: Session = Depends(get_db)):
    data = get_article(article_id)
    return templates.TemplateResponse(
        "pages/laws_detail_v2.html",
        get_template_context(request, db, **data)
    )

@router.get("/v2/account/subscription", response_class=HTMLResponse, name="web_v2_account_subscription")
def account_subscription(request: Request, state: str = "none", db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    account = get_account(current_user)

    # Получаем реальную подписку пользователя
    sub = None
    if current_user:
        sub = get_subscription(current_user.id, db)

    return templates.TemplateResponse(
        "pages/account_subscription_v2.html",
        get_template_context(request, db, tab="subscription", account=account, sub=sub),
    )

@router.post("/v2/account/subscription/subscribe", name="web_v2_subscribe_start")
async def subscribe_start(request: Request):
    start_subscription()  # включаем заглушку
    url = str(request.url_for("web_v2_account_subscription")) + "?state=active"
    return RedirectResponse(url=url, status_code=303)


@router.get("/v2/account/history", response_class=HTMLResponse, name="web_v2_account_history")
async def account_history(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)

    # Проверяем подписку
    if not current_user:
        return RedirectResponse(url="/v2/auth/login", status_code=303)

    subscription_repo = SubscriptionRepository(db)
    subscription = subscription_repo.get_by_user_id(current_user.id)

    if not subscription or not subscription_repo.is_active(subscription):
        # Подписка истекла - показываем сообщение
        account = get_account(current_user)
        return templates.TemplateResponse(
            "pages/account_history_v2.html",
            get_template_context(request, db, tab="history", account=account, items=[], no_subscription=True),
        )

    account = get_account(current_user)
    items = list_history(current_user.id, db)
    return templates.TemplateResponse(
        "pages/account_history_v2.html",
        get_template_context(request, db, tab="history", account=account, items=items),
    )


@router.get("/v2/account/stats", response_class=HTMLResponse, name="web_v2_account_stats")
async def account_stats(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)

    # Проверяем подписку
    if not current_user:
        return RedirectResponse(url="/v2/auth/login", status_code=303)

    subscription_repo = SubscriptionRepository(db)
    subscription = subscription_repo.get_by_user_id(current_user.id)

    if not subscription or not subscription_repo.is_active(subscription):
        # Подписка истекла - показываем сообщение
        account = get_account(current_user)
        return templates.TemplateResponse(
            "pages/account_stats_v2.html",
            get_template_context(request, db, tab="stats", account=account, stats=None, no_subscription=True),
        )

    account = get_account(current_user)
    stats = get_stats(current_user.id, db)
    return templates.TemplateResponse(
        "pages/account_stats_v2.html",
        get_template_context(request, db, tab="stats", account=account, stats=stats),
    )

@router.post("/v2/account/subscription/cancel", name="web_v2_subscribe_cancel")
async def subscribe_cancel_route(request: Request):
    cancel_subscription()
    url = str(request.url_for("web_v2_account_subscription")) + "?state=none"
    return RedirectResponse(url=url, status_code=303)


@router.post("/v2/buy-checks", name="web_v2_buy_checks")
async def buy_checks(request: Request, db: Session = Depends(get_db)):
    """Докупка дополнительных проверок"""
    current_user = get_current_user_from_cookie(request, db)

    if not current_user:
        return RedirectResponse(url="/v2/auth/login", status_code=303)

    subscription_repo = SubscriptionRepository(db)
    subscription = subscription_repo.get_by_user_id(current_user.id)

    if not subscription:
        return RedirectResponse(url="/v2/account/subscription", status_code=303)

    # Добавляем 30 проверок
    # TODO: В будущем здесь будет интеграция с платежной системой
    subscription_repo.add_checks(subscription, amount=30)

    # Перенаправляем на страницу подписки с сообщением об успехе
    return RedirectResponse(url="/v2/account/subscription?purchased=1", status_code=303)


@router.get("/v2/check/history/{check_id}/pdf", name="web_v2_history_pdf")
async def history_check_pdf(check_id: int, request: Request, db: Session = Depends(get_db)):
    """Скачивание PDF из истории проверок"""
    current_user = get_current_user_from_cookie(request, db)

    if not current_user:
        return RedirectResponse(url="/v2/auth/login", status_code=303)

    # Получаем проверку из БД
    check_repo = CheckRepository(db)
    check = check_repo.get_by_id(check_id)

    # Проверяем что проверка принадлежит пользователю
    if not check or check.user_id != current_user.id:
        return RedirectResponse(url="/v2/account/history", status_code=303)

    # Проверяем что есть результаты
    if not check.result:
        return RedirectResponse(url="/v2/account/history", status_code=303)

    # Генерируем PDF из сохраненного результата
    pdf_bytes = generate_pdf_report(check.result)

    headers = {
        "Content-Disposition": f"attachment; filename=check_{check_id}.pdf",
        "Content-Type": "application/pdf",
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


# ============ AUTH ROUTES ============

@router.get("/v2/auth/register", response_class=HTMLResponse, name="web_v2_register")
async def register_page(request: Request, db: Session = Depends(get_db)):
    """Страница регистрации"""
    return templates.TemplateResponse("pages/register_v2.html", get_template_context(request, db))


@router.post("/v2/auth/register", name="web_v2_register_submit")
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка регистрации"""
    try:
        user_data = UserRegister(email=email, password=password)
        user = register_user(db, user_data)

        # Создаем response с редиректом
        response = RedirectResponse(url="/v2/auth/login?registered=1", status_code=303)

        return response
    except Exception as e:
        # В случае ошибки возвращаемся на страницу регистрации с сообщением
        return templates.TemplateResponse(
            "pages/register_v2.html",
            get_template_context(request, db, error=str(e)),
            status_code=400
        )


@router.get("/v2/auth/login", response_class=HTMLResponse, name="web_v2_login")
async def login_page(request: Request, registered: int = 0, db: Session = Depends(get_db)):
    """Страница входа"""
    success_message = "Регистрация успешна! Теперь можете войти." if registered else None
    return templates.TemplateResponse(
        "pages/login_v2.html",
        get_template_context(request, db, success_message=success_message)
    )


@router.post("/v2/auth/login", name="web_v2_login_submit")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка входа"""
    user = authenticate_user(db, email, password)

    if not user:
        return templates.TemplateResponse(
            "pages/login_v2.html",
            get_template_context(request, db, error="Неверный email или пароль"),
            status_code=401
        )

    # Создаем response с редиректом и устанавливаем cookie
    response = RedirectResponse(url="/", status_code=303)
    set_auth_cookie(response, user.id)

    return response


@router.get("/v2/auth/logout", name="web_v2_logout")
async def logout(request: Request):
    """Выход из системы"""
    response = RedirectResponse(url="/", status_code=303)
    clear_auth_cookie(response)
    return response
