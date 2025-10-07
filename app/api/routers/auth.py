from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "supersecretkey"  # ideal pegar do .env
ALGORITHM = "HS256"

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Usuários simulados
fake_users_db = {
    "funcionario": {"username": "funcionario", "password": "123", "role": "A"},
    "cliente": {"username": "cliente", "password": "123", "role": "B"},
}

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + expires_delta})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = fake_users_db.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos")

    token = create_access_token({"sub": user["username"], "role": user["role"]})

    if user["role"] == "A":
        response = RedirectResponse(url="/rota-a", status_code=302)
    else:
        response = RedirectResponse(url="/rota-b", status_code=302)

    response.set_cookie(key="token", value=token, httponly=True)
    return response
