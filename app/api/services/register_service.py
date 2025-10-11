from typing import List, Optional

from app.api.schema.registros import Registro, RegistroCreate
from db.database import get_client
from fastapi import HTTPException
from passlib.hash import bcrypt

TABLE_NAME = "users"


def listar_registros() -> List[Registro]:
    """
    Retorna todos os registros da tabela de usuários.

    Não possui parametros de entrada, pois retorna todos os registros.

    Raises:
        HTTPException: Caso ocorra erro ao acessar o banco de dados.

    Returns:
        List[Registro]: Lista de objetos "Registro".
        Retorna lista vazia caso não tenha registros.

    """
    try:
        supabase = get_client()
        response = supabase.table(TABLE_NAME).select("*").execute()
         # Solução 
        # user_list = [Registro(**user_data) for user_data in response.data]
        # return user_list
        registros = response.data if response.data else []
        return registros

       
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao listar registros: {str(e)}"
        )


def buscar_registro(
    registro_id: int,
) -> Optional[Registro]:
    """
    Busca um registro no banco pelo ID.

    Parametros:
        registro_id (int): Identificador único do registro a ser buscado.

    Raises:
        HTTPException: Caso ocorra erro ao acessar o banco de dados.

    Retorno:
        Optional[Registro]: Objeto "Registro" contendo os dados do registro,
        ou "None" caso não seja encontrado.
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
            status_code=500, detail=f"Erro ao buscar registro: {str(e)}"
        )


def inserir_registro(data: RegistroCreate) -> Registro:
    """
    Função responsável por inserir usuários na tabela.

    A senha fornecida é truncada em 72 caracteres, codificada em UTF-8 e
    armazenada como um hash seguro.

    Parâmetro:
       data (RegistroCreate): Objeto contendo os dados do usuário a ser criado,
            incluindo name, email, senha e role.

    Raises:
        HTTPException: Caso ocorra algum erro ao inserir o registro no banco.
            - 400: Caso exista e-mail duplicado no banco.

    Retorno:
        Objeto Registro criado

    Notes:
        - A senha é truncada para evitar problemas com o limite do bcrypt
        (72 bytes).
    """
    try:
        supabase = get_client()

        existing_user = buscar_por_email(data.email)
        if existing_user is not None:
            raise HTTPException(
                status_code=400,
                detail="Já existe um usuário cadastrado com esse e-mail",
            )
        senha_truncada = data.senha[:72]
        senha_hash = bcrypt.hash(senha_truncada)
        response = (
            supabase.table(TABLE_NAME)
            .insert(
                {
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
                status_code=500, detail="Falha ao inserir registro no banco de dados"
            )

        return Registro(**response.data[0])

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao inserir registro: {str(e)}"
        )


def atualizar_registro(registro_id: int, name: str, email: str) -> Registro:
    """
    função para atualizar registro de usuarios ja existente pelo id.

    parametros:
        registro_id (int): Identificado unico do registro a ser atualizado
        name (str): Novo nome do usuário
        email (str): Novo e-mail do usuário.

    Raises:
        HTTPException: Se o registro com o ID informado não for encontrado.

    retorno:
        Objeto Registro atualizado

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
            status_code=404, detail=f"Registro com id {registro_id} não encontrado"
        )

    return Registro(**response.data[0])


def deletar_registro(registro_id: int) -> Registro:
    """
    Função responsavel por deletar um usuario.

    parametros:
       registro_id (int): Identificado unico do registro a ser deletado

    Raises:
        HTTPException: Se o registro com o ID informado não for encontrado.

    retorno:
        Objeto Registro deletado
    """
    supabase = get_client()
    response = supabase.table(TABLE_NAME).delete().eq("id", registro_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=404, detail=f"Registro com id {registro_id} não encontrado"
        )

    return Registro(**response.data[0])


def buscar_por_email(email: str):
    """
    Busca um usuário pelo e-mail no banco de dados usando Supabase.

    Parametros:
        email (str): O endereço de e-mail do usuário a ser buscado.

    Retorno:
        dict | None: Dicionário com os dados do usuário caso encontrado,
        ou None se não exister
    """
    supabase = get_client()
    response = supabase.table(TABLE_NAME).select("*").eq("email", email).execute()
    if response.data:
        return response.data[0]

    return None
