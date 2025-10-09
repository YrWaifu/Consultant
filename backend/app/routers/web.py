from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from ..services.news_stub import list_news, get_news_detail
from ..services.report_stub import make_report_from_input, make_report_pdf_bytes
from ..services.laws_stub import get_law_index, get_article, search_laws
from ..services.account_stub import (
    get_account, update_account,
    get_subscription, start_subscription, cancel_subscription,
)
from ..services.history_stub import list_history
from ..services.stats_stub import get_stats

router = APIRouter()
templates = Jinja2Templates(directory="backend/app/templates")

@router.get("/", response_class=HTMLResponse, name="web_v2_check")
async def index(request: Request):
    return templates.TemplateResponse("pages/check_v2.html", {"request": request})


@router.get("/v2/news", response_class=HTMLResponse, name="web_v2_news")
async def news_page(request: Request, q: str | None = None):
    items = list_news(q)
    return templates.TemplateResponse(
        "pages/news_list_v2.html",
        {"request": request, "items": items}
    )


@router.get("/v2/news/{news_id}", response_class=HTMLResponse, name="web_v2_news_detail")
async def news_detail_page(request: Request, news_id: int):
    news = get_news_detail(news_id)
    if not news:
        return RedirectResponse(url="/v2/news", status_code=303)
    return templates.TemplateResponse(
        "pages/news_detail_v2.html",
        {"request": request, "news": news}
    )


@router.get("/v2/search", response_class=HTMLResponse, name="web_v2_search")
async def search_page(request: Request, q: str | None = None):
    news_results = list_news(q) if q else []
    law_results = search_laws(q) if q else []
    return templates.TemplateResponse(
        "pages/search_v2.html",
        {"request": request, "query": q, "news_results": news_results, "law_results": law_results}
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
    data = make_report_from_input(text=text, claims=claims, media_path=None)
    return templates.TemplateResponse("pages/check_report_v2.html", {"request": request, **data})


@router.get("/v2/report", response_class=HTMLResponse, name="web_v2_report")
async def report_page(request: Request, case: str | None = None):
    data = make_report(case or "bad")
    return templates.TemplateResponse(
        "pages/check_report_v2.html",
        {"request": request, **data}
    )


@router.get("/v2/report.pdf", name="web_v2_report_pdf")
async def report_pdf_download(case: str | None = None):
    pdf_bytes = make_report_pdf_bytes(case or "bad")
    headers = {
        "Content-Disposition": "attachment; filename=report.pdf",
        "Content-Type": "application/pdf",
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


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
