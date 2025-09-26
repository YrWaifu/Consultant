from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from ..services.rules import rule_based_check
from ..services.ml_core import run_ml

router = APIRouter()

@router.post("/", response_class=HTMLResponse)
async def create_check_full(request: Request, text: str = Form(None)):
    issues_rb = rule_based_check(text or "")
    ml = run_ml(text, None)

    # Собираем карточки под макет
    issues = []
    for it in issues_rb:
        issues.append({
            "title": "Несоответствие ФЗ «О рекламе»" if it["code"].startswith("claim") else it.get("title", "Нарушение"),
            "text": "В соответствии с нормами ФЗ «О рекламе» запрещены превосходные формулировки без подтверждения.",
            "fix": it.get("fix", "Смягчить формулировку или указать критерии/источник оценки")
        })

    # Заглушка процента соответствия (65 как в макете)
    percent = 65

    return request.app.state.templates.TemplateResponse(
        "result_full.html",
        {"request": request, "issues": issues or [{"title":"Название менее серьёзного нарушения","text":"Описание","fix":"Обобщённые рекомендации"}], "percent": percent, "check_id": 0},
    )