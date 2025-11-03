import os
import tempfile
from typing import List
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.api.schema.registros import Registro, RegistroCreate
from app.services.auth_service import login
from app.services.register_service import (atualizar_registro, buscar_registro,
                                           deletar_registro, inserir_registro,
                                           listar_registros)
from app.services.register_service import upload_pdf as upload_pdf_service

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/register", response_model=Registro)
def register_route(novo_usuario: RegistroCreate):
    """
    Registra um novo usuário.

    Parâmetro de entrada: objeto RegistroCreate contendo
    name, email, senha e role.

    Raises:
        HTTPException:
            - 400: Se os dados fornecidos forem inválidos ou já existirem.
            - 500: Se ocorrer um erro inesperado no processo de registro.

    Retorno: Objeto Registro criado.
    """
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
def listar_usuarios_route():
    """
    Lista todos os usuários registrados.
    """
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
def buscar_usuario_route(registro_id: int):
    """
    Retorna um usuário específico pelo ID.
    """
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
def atualizar_usuario_route(registro_id: int, name: str, email: str):
    """
    Atualiza os dados de um usuário existente pelo ID.
    """
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
def deletar_usuario_route(registro_id: int):
    """
    Deleta um usuário existente pelo ID.
    """
    try:
        return deletar_registro(registro_id)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao deletar usuário.",
        )


@router.post("/upload_pdf")
async def upload_pdf_route(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),  # vem do token JWT
):
    """
    Rota para upload de PDF. Somente usuários 'gerente' podem enviar.
    """
    try:
        # Validação do role
        if user.get("role") != "gerente":
            raise HTTPException(
                status_code=403,
                detail="Acesso negado. Somente gerentes podem enviar PDFs.",
            )

        # Validar UUID do usuário
        try:
            user_uuid = UUID(str(user["sub"]))
        except ValueError:
            raise HTTPException(
                status_code=400, detail="ID do usuário no token não é UUID válido."
            )

        print(f"Current user (UUID): {user_uuid}")
        print(f"Arquivo recebido: {file.filename}")

        # Salva arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name

        print(f"Arquivo temporário criado em: {temp_file_path}")

        result = upload_pdf_service(
            file_path=temp_file_path,
            user_id=str(user_uuid),
            display_name=file.filename if file.filename else "" "arquivo_sem_nome.pdf",
        )

        # Remove arquivo temporário
        os.remove(temp_file_path)

        return result

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        print(f"Erro inesperado no upload_pdf_route: {e}")
        raise HTTPException(status_code=500, detail=str(e))
