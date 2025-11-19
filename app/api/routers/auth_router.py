from typing import List

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from app.api.schema.registros import Registro, RegistroCreate
from app.services.auth_service import login
from app.services.register_service import (atualizar_registro, buscar_registro,
                                           deletar_registro, inserir_registro,
                                           listar_registros)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
templates = Jinja2Templates(directory="templates")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodifica o token JWT e retorna os dados do usuário atual.

    Raises:
        HTTPException:
            - 401: Se o token estiver expirado ou for inválido.

    Retorno:
        dict: Payload decodificado do token JWT.
    """
    try:
        payload = jwt.decode(
            token,
            "sua_chave_super_secreta",
            algorithms=["HS256"],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/register", response_model=Registro)
def register_route(
    novo_usuario: RegistroCreate, user: dict = Depends(get_current_user)
):
    """
    Registra um novo usuário. Apenas gerentes podem registrar novos usuários.

    Parâmetro de entrada: objeto RegistroCreate contendo
    name, email, senha e role.

    Raises:
        HTTPException:
            - 400: Se os dados fornecidos forem inválidos ou já existirem.
            - 403: Apenas gerentes podem registrar usuários.
            - 500: Se ocorrer um erro inesperado no processo de registro.

    Retorno: Objeto Registro criado.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem registrar novos usuários.",
        )
    return inserir_registro(novo_usuario)


@router.post("/login")
def login_route(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Autentica um usuário no sistema.

    Valida as credenciais e retorna um token JWT em caso de sucesso.

    Raises:
        HTTPException:
            - 401: Credenciais inválidas.
            - 403: Usuário inativo.
            - 500: Erro inesperado durante o login.

    Retorno:
        dict: Contém o token de acesso e o tipo do token.
    """
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
    """
    Endpoint acessível apenas por usuários com o papel 'gerente'.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem acessar.",
        )
    return {"msg": f"Bem-vindo gerente {user['email']}"}


@router.get("/rota-usuario")
def rota_usuario(user: dict = Depends(get_current_user)):
    """
    Endpoint acessível apenas por usuários com o papel 'usuario'.
    """
    if user["role"] != "usuario":
        raise HTTPException(
            status_code=403,
            detail="Apenas usuários podem acessar.",
        )
    return {"msg": f"Bem-vindo usuário {user['email']}"}


@router.get("/usuarios", response_model=List[Registro], tags=["Autenticação"])
def listar_usuarios_route(user: dict = Depends(get_current_user)):
    """
    Lista todos os usuários registrados. Apenas gerentes podem listar usuários.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem listar usuários.",
        )
    try:
        return listar_registros()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/usuarios/{registro_id}",
    response_model=Registro,
    tags=["Autenticação"],
)
def buscar_usuario_route(registro_id: int, user: dict = Depends(get_current_user)):
    """
    Retorna um usuário específico pelo ID.
    Apenas gerentes podem buscar usuários.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem buscar usuários.",
        )
    try:
        usuario = buscar_registro(registro_id)
        if not usuario:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado.",
            )
        return usuario
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao buscar usuário.",
        )


@router.put(
    "/usuarios/{registro_id}",
    response_model=Registro,
    tags=["Autenticação"],
)
def atualizar_usuario_route(
    registro_id: int, name: str, email: str, user: dict = Depends(get_current_user)
):
    """
    Atualiza os dados de um usuário existente pelo ID.
    Apenas gerentes podem atualizar usuários.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem atualizar usuários.",
        )
    try:
        return atualizar_registro(registro_id, name, email)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar usuário.",
        )


@router.delete(
    "/usuarios/{registro_id}",
    response_model=Registro,
    tags=["Autenticação"],
)
def deletar_usuario_route(registro_id: int, user: dict = Depends(get_current_user)):
    """
    Deleta um usuário existente pelo ID.
    Apenas gerentes podem deletar usuários.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem deletar usuários.",
        )
    try:
        return deletar_registro(registro_id)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao deletar usuário.",
        )


@router.get("/upload")
def upload_page(request: Request, user: dict = Depends(get_current_user)):
    """
    Serve a página de upload para gerentes.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem acessar esta página.",
        )
    return templates.TemplateResponse("upload.html", {"request": request})
