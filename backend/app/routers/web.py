from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
import json
import os

from ..services.article_service import ArticleService
from ..services.article_file_loader import ArticleFileLoader
from ..services.laws_stub import get_law_index, get_article, search_laws
from ..services.account_stub import (
    get_account, update_account,
    get_subscription, start_subscription, cancel_subscription,
)
from ..services.history_stub import list_history
from ..services.stats_stub import get_stats
from ..services.pdf_generator import generate_pdf_report
from ..workers.queue import queue, process_ad_check_task

from babel.dates import format_date

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")
templates.env.globals['format_date'] = format_date

@router.get("/", response_class=HTMLResponse, name="web_v2_check")
async def index(request: Request):
    return templates.TemplateResponse("pages/check_v2.html", {"request": request})


@router.get("/v2/articles", response_class=HTMLResponse, name="web_v2_articles")
async def articles_page(request: Request):
    article_service = ArticleService()
    data = article_service.get_articles_homepage()
    return templates.TemplateResponse(
        "pages/articles_list_v2.html",
        {"request": request, **data}
    )


@router.get("/v2/articles/category/{category_slug}", response_class=HTMLResponse, name="web_v2_articles_category")
async def articles_category_page(request: Request, category_slug: str):
    article_service = ArticleService()
    data = article_service.get_category_articles(category_slug)
    if not data:
        return RedirectResponse(url="/v2/articles", status_code=303)
    return templates.TemplateResponse(
        "pages/articles_category_v2.html",
        {"request": request, **data}
    )


@router.get("/v2/articles/{article_slug}", response_class=HTMLResponse, name="web_v2_article_detail")
async def article_detail_page(request: Request, article_slug: str):
    article_service = ArticleService()
    data = article_service.get_article_detail(article_slug)
    if not data:
        return RedirectResponse(url="/v2/articles", status_code=303)
    return templates.TemplateResponse(
        "pages/article_detail_v2.html",
        {"request": request, **data}
    )


@router.get("/v2/search", response_class=HTMLResponse, name="web_v2_search")
async def search_page(request: Request, q: str | None = None):
    article_service = ArticleService()
    article_results = article_service.search_articles(q) if q else []
    law_results = search_laws(q) if q else []
    return templates.TemplateResponse(
        "pages/search_v2.html",
        {"request": request, "query": q, "article_results": article_results, "law_results": law_results}
    )


@router.get("/v2/check", response_class=HTMLResponse, name="web_v2_check")
async def check_page(request: Request):
    return templates.TemplateResponse("pages/check_v2.html", {"request": request})


@router.post("/v2/check", response_class=HTMLResponse, name="web_v2_check_submit")
async def check_submit(
    request: Request,
    text: str | None = Form(None),
    claims: list[str] | None = Form(None),
    file: UploadFile | None = File(None),
):
    # Если прикреплен файл, читаем его в байты
    audio_bytes = None
    audio_content_type = None

    if file and file.filename:
        audio_bytes = await file.read()
        audio_content_type = file.content_type

    # Создаем фоновую задачу для обработки ML модели
    job = queue.enqueue(process_ad_check_task, text, audio_bytes, audio_content_type)
    
    # Перенаправляем на страницу ожидания с ID задачи
    return RedirectResponse(url=f"/v2/check/status/{job.id}", status_code=303)


@router.get("/v2/check/status/{job_id}", response_class=HTMLResponse, name="web_v2_check_status")
async def check_status_page(request: Request, job_id: str):
    """Страница ожидания результата проверки"""
    return templates.TemplateResponse("pages/check_status_v2.html", {
        "request": request, 
        "job_id": job_id
    })


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
async def check_result_page(request: Request, job_id: str):
    """Страница с результатом проверки"""
    try:
        from rq.job import Job
        from ..workers.queue import redis
        
        job = Job.fetch(job_id, connection=redis)
        
        if job.is_finished:
            data = job.result
            data["job_id"] = job_id  # Передаем job_id в шаблон для PDF ссылки
            return templates.TemplateResponse("pages/check_report_v2.html", {"request": request, **data})
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


@router.get("/v2/account", response_class=HTMLResponse, name="web_v2_account")
async def account_page(request: Request):
    data = get_account()
    return templates.TemplateResponse(
        "pages/account_profile_v2.html",
        {"request": request, "active": "account", "tab": "profile", "account": data},
    )

@router.post("/v2/account", response_class=HTMLResponse, name="web_v2_account_submit")
async def account_submit(
    request: Request,
    last_name: str = Form(""),
    first_name: str = Form(""),
    email: str = Form(""),
    avatar: UploadFile | None = File(None),
):
    # файл никуда не сохраняем — просто делаем вид, что у нас есть url
    avatar_url = None
    if avatar and avatar.filename:
        avatar_url = f"/static/img/avatars/{avatar.filename}"
    update_account(
        {"last_name": last_name, "first_name": first_name, "email": email, "avatar_url": avatar_url}
    )
    return RedirectResponse(request.url_for("web_v2_account"), status_code=303)

@router.get("/v2/laws", response_class=HTMLResponse, name="web_v2_laws")
async def laws_index(request: Request):
    data = get_law_index()
    return templates.TemplateResponse(
        "pages/laws_index_v2.html",
        {"request": request, **data}
    )

@router.get("/v2/laws/article/{article_id}", response_class=HTMLResponse, name="web_v2_law_article")
async def laws_article(request: Request, article_id: str):
    data = get_article(article_id)
    return templates.TemplateResponse(
        "pages/laws_detail_v2.html",
        {"request": request, **data}
    )

@router.get("/v2/account/subscription", response_class=HTMLResponse, name="web_v2_account_subscription")
def account_subscription(request: Request, state: str = "none"):
    account = get_account()
    sub = get_subscription() if state != "none" else None
    return templates.TemplateResponse(
        "pages/account_subscription_v2.html",
        {"request": request, "tab": "subscription", "account": account, "sub": sub},
    )

@router.post("/v2/account/subscription/subscribe", name="web_v2_subscribe_start")
async def subscribe_start(request: Request):
    start_subscription()  # включаем заглушку
    url = str(request.url_for("web_v2_account_subscription")) + "?state=active"
    return RedirectResponse(url=url, status_code=303)


@router.get("/v2/account/history", response_class=HTMLResponse, name="web_v2_account_history")
async def account_history(request: Request):
    account = get_account()
    items = list_history()
    return templates.TemplateResponse(
        "pages/account_history_v2.html",
        {"request": request, "tab": "history", "account": account, "items": items},
    )


@router.get("/v2/account/stats", response_class=HTMLResponse, name="web_v2_account_stats")
async def account_stats(request: Request):
    account = get_account()
    stats = get_stats()
    return templates.TemplateResponse(
        "pages/account_stats_v2.html",
        {"request": request, "tab": "stats", "account": account, "stats": stats},
    )

@router.post("/v2/account/subscription/cancel", name="web_v2_subscribe_cancel")
async def subscribe_cancel_route(request: Request):
    cancel_subscription()
    url = str(request.url_for("web_v2_account_subscription")) + "?state=none"
    return RedirectResponse(url=url, status_code=303)


# ============ МАРШРУТЫ ДЛЯ ЗАГРУЗКИ СТАТЕЙ ============

@router.post("/admin/articles/upload-json", name="admin_upload_articles_json")
async def upload_articles_json(file: UploadFile = File(...)):
    """Загрузка статей из JSON файла"""
    if not file.filename.endswith('.json'):
        return JSONResponse({"error": "Файл должен быть в формате JSON"}, status_code=400)
    
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        # Сохраняем временный файл
        temp_path = f"temp_{file.filename}"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Загружаем статьи
        loader = ArticleFileLoader()
        result = loader.load_from_json(temp_path)
        
        # Удаляем временный файл
        os.remove(temp_path)
        
        return JSONResponse(result)
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/admin/articles/load-from-dir", name="admin_load_articles_from_dir")
async def load_articles_from_directory(directory_path: str):
    """Загрузка статей из директории с Markdown файлами"""
    try:
        loader = ArticleFileLoader()
        result = loader.load_from_markdown_directory(directory_path)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/admin/articles", response_class=HTMLResponse, name="admin_articles")
async def admin_articles_page(request: Request):
    """Админ-панель для загрузки статей"""
    return templates.TemplateResponse(
        "pages/admin_articles_v2.html",
        {"request": request}
    )
