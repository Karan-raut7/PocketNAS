import os
import shutil
from pathlib import Path
from fastapi import FastAPI, Request, Form, UploadFile, File, status
from fastapi.staticfiles import StaticFiles

from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.config import STORAGE_DIR
from app.database import get_db
from app.models.user import User
from app.utils.security import hash_password, verify_password
from app.core.templates import templates

from app.routes.auth import router as auth_router
from app.routes.files import router as file_router

app = FastAPI(title="Pocket Server")
app.include_router(auth_router)
app.include_router(file_router)


app.add_middleware(SessionMiddleware, secret_key="pocket-server-secret-key-change-this")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# Dashboard uploads live in the same storage root as API uploads,
# in one folder per user: <STORAGE_DIR>/users/<username>/
UPLOAD_DIR = STORAGE_DIR / "users"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def user_file_path(user: str, filename: str) -> Path:
    # Keep only the plain file name so nothing can escape the user's folder
    return UPLOAD_DIR / user / Path(filename).name


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
# Note: /uploads is no longer mounted publicly. Files are served through /media (login required).





# --- AUTH ROUTES ---

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request, "user": None}
    )

@app.post("/login")
async def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.scalar(
        select(User).where(User.username == username)
    )

    if not user or not verify_password(
        password,
        user.hashed_password
    ):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "error": "Invalid username or password"
            }
        )

    request.session["user"] = user.username

    return RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request, "user": request.session.get("user")}
    )

@app.post("/register")
async def register_action(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"request": request, "error": "Passwords do not match"}
        )

    if len(password) < 8 or len(username) < 3:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"request": request, "error": "Invalid username or password length"}
        )

    existing_user = db.scalar(
        select(User).where(
            or_(
                User.username == username,
                User.email == email
            )
        )
    )

    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"request": request, "error": "Username or email already exists"}
        )

    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


# --- DASHBOARD & MEDIA ROUTES ---
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Dedicated folder per user
    user_upload_dir = UPLOAD_DIR / user
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    media_list = []
    for filename in os.listdir(user_upload_dir):
        file_lower = filename.lower()
        is_video = file_lower.endswith((".mp4", ".webm", ".ogg", ".mov"))
        is_image = file_lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))

        if is_video or is_image:
            media_list.append({
                "name": filename,
                "url": f"/media/{filename}",
                "is_video": is_video
            })

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"request": request, "user": user, "files": media_list}
    )

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user_upload_dir = UPLOAD_DIR / user
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    if file.filename:
        destination_path = user_file_path(user, file.filename)
        with destination_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/delete/{filename}")
async def delete_file(request: Request, filename: str):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Only delete from the logged-in user's folder
    target = user_file_path(user, filename)
    if target.is_file():
        target.unlink()

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/view/{filename}", response_class=HTMLResponse)
async def view_media(request: Request, filename: str):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = user_file_path(user, filename)
    if not file_path.is_file():
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    is_video = filename.lower().endswith((".mp4", ".webm", ".ogg", ".mov"))
    file_data = {
        "name": file_path.name,
        "url": f"/media/{file_path.name}",
        "is_video": is_video
    }

    return templates.TemplateResponse(
        request=request,
        name="media_detail.html",
        context={"request": request, "user": user, "file": file_data}
    )

@app.get("/media/{filename}")
async def get_media(request: Request, filename: str):
    # Login-protected replacement for the old public /uploads mount
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    file_path = user_file_path(user, filename)
    if not file_path.is_file():
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    return FileResponse(path=file_path)