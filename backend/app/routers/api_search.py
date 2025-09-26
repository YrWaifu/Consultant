from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.post("/", response_class=HTMLResponse)
async def search(request: Request, q: str = Form("")):
    # Псевдо-данные; позже подключишься к БД/файлу
    items = [
        {"law_code": "38-ФЗ", "title": "О рекламе — маркировка 18+", "snippet": "Требования к предупреждениям...", "url": "#"},
        {"law_code": "ФЗ о защите конкуренции", "title": "Запрет недобросовестной конкуренции", "snippet": "Запрещается...", "url": "#"}
    ] if q else []
    return request.app.state.templates.TemplateResponse("partials/laws_items.html", {"request": request, "items": items})