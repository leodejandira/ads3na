from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routers import auth_router
from app.api.routers.auth_router import get_current_user

# Inicializa o aplicativo FastAPI
app = FastAPI(title="Sistema de Gestão", version="1.0.0")

# Configuração dos templates e arquivos estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------
# Rotas de páginas HTML
# -------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_home_page(request: Request):
    """Renderiza a nova página inicial (home.html)."""
    return templates.TemplateResponse(
        "home.html",
        {"request": request},
    )


@app.get("/login", response_class=HTMLResponse)
async def serve_login_page(request: Request):
    """Renderiza a página de login (login_index.html)."""
    return templates.TemplateResponse(
        "login_index.html",
        {"request": request},
    )


@app.get("/gerente", response_class=HTMLResponse)
async def serve_gerente_page(request: Request):
    """Renderiza a página do gerente (manager_home.html)."""
    return templates.TemplateResponse(
        "manager_home.html",
        {"request": request},
    )


@app.get("/usuario", response_class=HTMLResponse)
async def serve_usuario_page(request: Request):
    """Renderiza a página do usuário (user_home.html)."""
    return templates.TemplateResponse(
        "user_home.html",
        {"request": request},
    )


@app.get("/upload", response_class=HTMLResponse)
async def serve_upload_page(request: Request):
    """Renderiza a página de upload de PDF (upload.html)."""
    return templates.TemplateResponse(
        "upload.html",
        {"request": request},
    )


@app.get("/funcionarios", response_class=HTMLResponse)
async def serve_funcionarios_page(request: Request):
    """Renderiza a página de gerenciamento de funcionários (funcionarios.html)."""
    return templates.TemplateResponse(
        "funcionarios.html",
        {"request": request},
    )


# -------------------------------
# Rotas de API
# -------------------------------
app.include_router(auth_router.router, tags=["Autenticação"])

