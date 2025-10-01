# backend/app/routers/api_news.py
from fastapi import APIRouter, Query
from ..services.news_stub import list_news

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("/")
def api_list_news(q: str | None = Query(None)):
    return {"items": list_news(q)}
