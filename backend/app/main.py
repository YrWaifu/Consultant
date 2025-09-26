from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routers import web, api_checks, api_search, api_auth

app = FastAPI(title="AdLaw Moderator")
app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")
app.state.templates = Jinja2Templates(directory="backend/app/templates")

app.include_router(web.router)
app.include_router(api_checks.router, prefix="/api/checks", tags=["checks"])
app.include_router(api_search.router, prefix="/api/search", tags=["search"])
app.include_router(api_auth.router,  prefix="/api/auth",   tags=["auth"])
