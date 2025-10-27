# backend/app/main.py (фрагмент)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import web
from .init_articles import init_app

app = FastAPI()

# Инициализация приложения с проверкой статей
init_app()

# Обслуживание статики для шаблонов (url_for('static', path='...'))
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")
app.include_router(web.router)
