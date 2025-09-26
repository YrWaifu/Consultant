from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return request.app.state.templates.TemplateResponse("index.html", {"request": request})

@router.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    return request.app.state.templates.TemplateResponse("history.html", {"request": request})

@router.get("/laws", response_class=HTMLResponse)
async def laws(request: Request):
    return request.app.state.templates.TemplateResponse("laws.html", {"request": request})

@router.get("/account", response_class=HTMLResponse)
async def account(request: Request):
    return request.app.state.templates.TemplateResponse("account.html", {"request": request, "user": {"email": None}})

@router.get("/check/{check_id}", response_class=HTMLResponse)
async def check_detail(request: Request, check_id: int):
    # рыба данных, дальше возьмешь из БД
    ctx = {
        "request": request,
        "check": {"id": check_id, "created_at": "2025-09-26 14:45", "input_text": "самый лучший товар..."},
        "summary": "Найдены потенциальные несоответствия",
        "result": {"issues": [
            {"title": "Запрещенные превосходные формулировки", "level": "medium", "fix": "Уберите превосходную форму"}
        ]}
    }
    return request.app.state.templates.TemplateResponse("check_detail.html", ctx)

@router.get("/result-demo", response_class=HTMLResponse)
async def result_demo(request: Request):
    ctx = {
        "request": request,
        "issues": [
            {"title": "Несоответствие ФЗ «О рекламе»", "text": "Запрещены слова «лучший», «самый», «абсолютный» без доказательств", "fix": "Добавьте критерии оценки или уберите превосходные формы"},
            {"title": "Название менее серьёзного нарушения", "text": "Описание нарушения", "fix": "Обобщённые рекомендации"},
            {"title": "Название несерьёзного нарушения", "text": "Описание нарушения", "fix": "Обобщённые рекомендации"}
        ],
        "percent": 65,
        "check_id": 1
    }
    return request.app.state.templates.TemplateResponse("result_full.html", ctx)