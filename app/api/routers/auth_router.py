from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from app.services.auth_service import login, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/login")
def login_route(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        token = login(form_data.username, form_data.password)
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException as http_err:
        raise http_err
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao realizar login.",
        )

@router.get("/rota-gerente")
def rota_gerente(user: dict = Depends(get_current_user)):
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem acessar.",
        )
    return {"msg": f"Bem-vindo gerente {user['email']}"}

@router.get("/rota-usuario")
def rota_usuario(user: dict = Depends(get_current_user)):
    if user["role"] != "usuario":
        raise HTTPException(
            status_code=403,
            detail="Apenas usuários podem acessar.",
        )
    return {"msg": f"Bem-vindo usuário {user['email']}"}

@router.get("/upload")
def upload_page(request: Request, user: dict = Depends(get_current_user)):
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem acessar esta página.",
        )
    return templates.TemplateResponse("upload.html", {"request": request})