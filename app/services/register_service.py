import os
import uuid
from typing import List, Optional

from fastapi import HTTPException
from passlib.hash import bcrypt
from supabase import create_client

from app.api.schema.registros import Registro, RegistroCreate
from app.db.database import get_client

TABLE_NAME = "users"


def listar_registros() -> List[Registro]:
    """
    Retorna todos os registros da tabela de usuários.

    Raises:
        HTTPException: Caso ocorra erro ao acessar o banco de dados.

    Returns:
        List[Registro]: Lista de objetos "Registro".
    """
    try:
        supabase = get_client()
        response = supabase.table(TABLE_NAME).select("*").execute()
        registros = response.data if response.data else []
        return [Registro(**registro) for registro in registros]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar registros: {str(e)}",
        )


def buscar_registro(registro_id: int) -> Optional[Registro]:
    """
    Busca um registro no banco pelo ID.
    """
    try:
        supabase = get_client()
        response = (
            supabase.table(TABLE_NAME).select("*").eq("id", registro_id).execute()
        )

        if response.data:
            return Registro(**response.data[0])
        return None
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar registro: {str(e)}",
        )


def inserir_registro(data: RegistroCreate) -> Registro:
    """
    Insere um novo usuário na tabela de usuários.
    """
    try:
        supabase = get_client()

        # PASSO 1: Criar o usuário no Supabase Auth (para obter o UUID)
        # O Supabase Auth já verifica se o e-mail existe, então não precisamos
        # chamar buscar_por_email() primeiro.
        try:
            auth_response = supabase.auth.sign_up(
                {"email": data.email, "password": data.senha}
            )
        except Exception as auth_error:
            # Captura erros como "User already registered"
            raise HTTPException(
                status_code=400,
                detail=f"Erro no Supabase Auth: {str(auth_error)}",
            )

        # Garantir que o usuário foi criado e temos o UUID
        if not auth_response.user or not auth_response.user.id:
            raise HTTPException(
                status_code=500, detail="Falha ao criar usuário no Auth ou obter UUID."
            )

        # Este é o UUID da tabela auth.users
        auth_user_uuid = auth_response.user.id

        # PASSO 2: Salvar os dados na sua tabela 'users' (perfil)
        # Mantemos seu hash bcrypt original para o seu fluxo de login
        senha_truncada = data.senha[:72]
        senha_hash = bcrypt.hash(senha_truncada)

        response = (
            supabase.table(TABLE_NAME)
            .insert(
                {
                    "auth_user_id": auth_user_uuid,
                    "name": data.name,
                    "email": data.email,
                    "senha_hash": senha_hash,
                    "role": data.role,
                    "ativo": True,
                }
            )
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Falha ao inserir perfil no banco de dados.",
            )

        return Registro(**response.data[0])

    except HTTPException as http_e:
        # Repassa as exceções que já lançamos (ex: 400 do Auth)
        raise http_e
    except Exception as e:
        # Pega qualquer outro erro inesperado
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao inserir registro: {str(e)}",
        )


def atualizar_registro(registro_id: int, name: str, email: str) -> Registro:
    """
    Atualiza um registro existente pelo ID.
    """
    supabase = get_client()
    response = (
        supabase.table(TABLE_NAME)
        .update({"name": name, "email": email})
        .eq("id", registro_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail=f"Registro com id {registro_id} não encontrado.",
        )

    return Registro(**response.data[0])


def deletar_registro(registro_id: int) -> Registro:
    """
    Deleta um usuário existente pelo ID.
    """
    supabase = get_client()
    response = supabase.table(TABLE_NAME).delete().eq("id", registro_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail=f"Registro com id {registro_id} não encontrado.",
        )

    return Registro(**response.data[0])


def buscar_por_email(email: str):
    """
    Busca um usuário pelo e-mail no banco de dados.
    """
    supabase = get_client()
    response = supabase.table(TABLE_NAME).select("*").eq("email", email).execute()

    if response.data:
        return response.data[0]
    return None


def upload_pdf(
    file_path: str,
    bucket_name: str = "pdfs",
    display_name: str = None,
    expire_seconds: int = 3600,
    user_id: str = None,
):
    """
    Faz upload de um arquivo PDF para o Supabase Storage
    e registra no banco.

    parametros: File path do arquivo a ser enviado,
    nome do bucket(ja definido), nome de exibição,
    tempo de expiração da URL assinada e ID do usuário
    que está fazendo o upload.

    retorno: dicionário com nome do arquivo,
    nome de exibição e URL assinada.
    esse retorno é adicionado no banco de dados,
    na tabela 'pdf_uploads'.
    """
    # Cliente "anon" normal para upload no storage
    supabase = get_client()

    # Cliente admin para bypass RLS (usar a Service Role Key)
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Gera nome único do arquivo
    file_ext = os.path.splitext(file_path)[1] or ".pdf"
    file_name = f"{uuid.uuid4()}{file_ext}"

    if display_name is None:
        display_name = os.path.basename(file_path)

    print(f"[DEBUG] Iniciando upload do arquivo: {file_path}")
    print(f"[DEBUG] Nome final do arquivo no bucket: {file_name}")

    # Upload do arquivo
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            print(f"[DEBUG] Tamanho do arquivo lido: {len(file_bytes)} bytes")

            upload_res = supabase.storage.from_(bucket_name).upload(
                path=file_name,
                file=file_bytes,
                file_options={
                    "content_type": "application/pdf",
                    "cache_control": "3600",
                },
            )

            print(f"[DEBUG] Resposta do Supabase Storage: {upload_res}")

    except Exception as e:
        print(f"[ERROR] Erro ao ler/enviar arquivo: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao ler/enviar arquivo: {str(e)}"
        )

    # Gera URL assinada
    signed_url_res = supabase.storage.from_(bucket_name).create_signed_url(
        file_name, expire_seconds
    )
    print(f"[DEBUG] Resposta de URL assinada: {signed_url_res}")

    signed_url = (
        signed_url_res.get("signedURL") if isinstance(signed_url_res, dict) else None
    )
    if not signed_url:
        raise HTTPException(
            status_code=500, detail="Não foi possível gerar a URL assinada"
        )

    # Salva no banco usando cliente admin (bypass RLS)
    try:
        db_res = (
            supabase_admin.table("pdf_uploads")
            .insert(
                {
                    "user_id": str(user_id),
                    "file_name": str(display_name),
                    "file_path": str(file_name),
                    "status": "pendente",
                }
            )
            .execute()
        )

        print(f"[DEBUG] Resposta do banco: {db_res}")

        if hasattr(db_res, "error") and db_res.error:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao registrar PDF no banco: {db_res.error}",
            )

    except Exception as e:
        print(f"[ERROR] Erro ao salvar registro no banco: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao salvar registro no banco: {str(e)}"
        )

    return {
        "file_name": file_name,
        "display_name": display_name,
        "signed_url": signed_url,
    }
