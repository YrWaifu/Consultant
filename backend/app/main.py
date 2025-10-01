# backend/app/main.py (фрагмент)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import web

app = FastAPI()
# Обслуживание статики для шаблонов (url_for('static', path='...'))
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")
app.include_router(web.router)
