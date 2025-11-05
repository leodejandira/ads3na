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
