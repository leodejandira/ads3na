import os
import tempfile
from typing import List
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request
from fastapi.templating import Jinja2Templates
from supabase import create_client

from app.db.database import get_client
from app.api.schema.registros import Registro, RegistroCreate
from app.services.auth_service import login
from app.services.register_service import (atualizar_registro, buscar_registro,
                                           deletar_registro, inserir_registro,
                                           listar_registros)
from app.services.pdfs import upload_pdf as upload_pdf_service

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
def register_route(novo_usuario: RegistroCreate, user: dict = Depends(get_current_user)):
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
    Retorna um usuário específico pelo ID. Apenas gerentes podem buscar usuários.
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
def atualizar_usuario_route(registro_id: int, name: str, email: str, user: dict = Depends(get_current_user)):
    """
    Atualiza os dados de um usuário existente pelo ID. Apenas gerentes podem atualizar usuários.
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
    Deleta um usuário existente pelo ID. Apenas gerentes podem deletar usuários.
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


@router.post("/upload_pdf")
async def upload_pdf_route(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
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

        file_display_name = file.filename if file.filename else "arquivo_sem_nome.pdf"

        supabase = get_client()

        # *** VALIDAÇÃO AQUI ***
        exists = (
            supabase.table("pdf_uploads")
            .select("id")
            .eq("file_name", file_display_name)
            .execute()
        )

        if exists.data:
            raise HTTPException(
                status_code=409, detail="Já existe um PDF com esse nome."
            )

        print(f"Current user (UUID): {user_uuid}")
        print(f"Arquivo recebido: {file.filename}")

        # Salva arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name

        print(f"Arquivo temporário criado em: {temp_file_path}")

        # chama seu service
        result = upload_pdf_service(
            file_path=temp_file_path,
            user_id=str(user_uuid),
            display_name=file_display_name,
        )

        os.remove(temp_file_path)

        return result

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        print(f"Erro inesperado no upload_pdf_route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdfs")
async def list_pdfs_route(user: dict = Depends(get_current_user)):
    """
    Lista todos os PDFs cadastrados no Supabase.
    - Gerentes veem todos os PDFs.
    - Outros usuários (se existir essa regra) veem apenas os próprios.
    """
    try:
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        query = supabase_admin.table("pdf_uploads").select("*")

        # Se quiser que apenas o gerente veja tudo, e outros só os seus:
        if user.get("role") != "gerente":
            query = query.eq("user_id", user["sub"])

        db_res = query.execute()

        if not db_res.data:
            return {"message": "Nenhum PDF encontrado.", "pdfs": []}

        return {"pdfs": db_res.data}

    except Exception as e:
        print(f"[ERROR] Erro ao listar PDFs: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar PDFs: {str(e)}")

@router.delete("/pdfs/{display_name}")
async def delete_pdf_route(display_name: str, user: dict = Depends(get_current_user)):
    """
    Deleta um PDF pelo nome de exibição (display_name).
    Somente gerentes podem excluir.
    """
    if user.get("role") != "gerente":
        raise HTTPException(status_code=403, detail="Apenas gerentes podem deletar PDFs.")

    try:
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        # Busca o registro correspondente ao display_name
        record = (
            supabase_admin.table("pdf_uploads")
            .select("id, file_path")
            .eq("file_name", display_name)
            .single()
            .execute()
        )

        if not record.data:
            raise HTTPException(status_code=404, detail="PDF não encontrado.")

        file_path = record.data["file_path"]

        # Remove do Storage
        delete_res = supabase_admin.storage.from_("pdfs").remove([file_path])
        print(f"[DEBUG] Resposta da exclusão no Storage: {delete_res}")

        # Remove do banco
        db_res = (
            supabase_admin.table("pdf_uploads")
            .delete()
            .eq("id", record.data["id"])
            .execute()
        )
        print(f"[DEBUG] Resposta da exclusão no banco: {db_res}")

        return {"message": f"PDF '{display_name}' removido com sucesso."}

    except Exception as e:
        print(f"[ERROR] Erro ao deletar PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao deletar PDF: {str(e)}")
