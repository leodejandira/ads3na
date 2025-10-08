import jwt
from api.schema.registros import RegistroCreate
from api.services.auth_service import login
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from utils.dbfunctions import inserir_registro

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/register")
def register_route(novo_usuario: RegistroCreate):
    return inserir_registro(novo_usuario)


@router.post("/login")
def login_route(form_data: OAuth2PasswordRequestForm = Depends()):
    token = login(form_data.username, form_data.password)
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, "sua_chave_super_secreta", algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.get("/rota-gerente")
def rota_gerente(user: dict = Depends(get_current_user)):
    if user["role"] != "gerente":
        raise HTTPException(status_code=403, detail="Apenas gerentes podem acessar")
    return {"msg": f"Bem-vindo gerente {user['email']}"}


@router.get("/rota-usuario")
def rota_usuario(user: dict = Depends(get_current_user)):
    if user["role"] != "usuario":
        raise HTTPException(status_code=403, detail="Apenas usuários podem acessar")
    return {"msg": f"Bem-vindo usuário {user['email']}"}
