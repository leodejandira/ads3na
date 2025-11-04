from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routers import auth_router
from app.api.routers.auth_router import get_current_user

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_home_page(request: Request):
    """
    Renderiza a nova página inicial (home.html).
    """
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={},
    )


@app.get("/login", response_class=HTMLResponse)
async def serve_login_page(request: Request):
    """
    Renderiza a página de login (login_index.html).
    """
    return templates.TemplateResponse(
        request=request,
        name="login_index.html",
        context={},
    )


@app.get("/gerente", response_class=HTMLResponse)
async def serve_gerente_page(request: Request):
    """
    Serve o template que fará a verificação de segurança no lado do cliente.
    """
    return templates.TemplateResponse(
        request=request,
        name="manager_home.html",
        context={},
    )


@app.get("/usuario", response_class=HTMLResponse)
async def serve_usuario_page(request: Request):
    """
    Serve o template que fará a verificação de segurança no lado do cliente.
    """
    return templates.TemplateResponse(
        request=request,
        name="user_home.html",
        context={},
    )


@app.get("/upload", response_class=HTMLResponse)
async def serve_upload_page(request: Request):
    """
    Serve a página de upload de PDF para gerentes.
    A proteção é feita no frontend (assim como /gerente).
    """
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={},
    )

@app.get("/funcionarios", response_class=HTMLResponse)
async def serve_funcionarios_page(request: Request):
    """
    Serve a página de gerenciamento de funcionários para gerentes.
    """
    return templates.TemplateResponse(
        request=request,
        name="funcionarios.html",
        context={},
    )

app.include_router(auth_router.router, tags=["Autenticação"])