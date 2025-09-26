from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from ..services.rules import rule_based_check
from ..services.ml_core import run_ml

router = APIRouter()

@router.post("/", response_class=HTMLResponse)
async def create_check_htmx(request: Request, text: str = Form(None)):
    issues = rule_based_check(text or "")
    ml = run_ml(text, None)
    result = {"issues": issues, "ml": ml}
    return request.app.state.templates.TemplateResponse(
        "partials/result.html",
        {"request": request, "summary": "Найдены потенциальные несоответствия" if issues else "Чисто", "result": result},
    )