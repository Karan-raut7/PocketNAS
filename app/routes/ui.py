from fastapi import APIRouter, Request

from app.core.templates import templates



ui_router = APIRouter()

@ui_router.get("/", include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@ui_router.get("/files", include_in_schema=False)
async def files_page(request: Request):
    return templates.TemplateResponse("files.html", {"request": request})

@ui_router.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@ui_router.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
