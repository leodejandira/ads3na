from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routers import auth_router

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_home_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def serve_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/gerente", response_class=HTMLResponse)
async def serve_gerente_page(request: Request):
    return templates.TemplateResponse("manager_home.html", {"request": request})


@app.get("/usuario", response_class=HTMLResponse)
async def serve_usuario_page(request: Request):
    return templates.TemplateResponse("user_home.html", {"request": request})


@app.get("/upload", response_class=HTMLResponse)
async def serve_upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/funcionarios", response_class=HTMLResponse)
async def serve_funcionarios_page(request: Request):
    return templates.TemplateResponse("funcionarios.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def serve_chat_page(request: Request):
    return templates.TemplateResponse("minddesk.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def serve_settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})


app.include_router(auth_router.router, tags=["Autenticação"])
