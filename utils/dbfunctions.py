from typing import List, Optional
from fastapi import HTTPException

from api.schema.registros import Registro, RegistroCreate
from db.database import get_client
from passlib.hash import bcrypt

TABLE_NAME = "users"


def listar_registros() -> List[Registro]:
    """
    Função responsavel por listar todos os registros
    da tabela users
    não possui parametros de entrada, pois esta puxando tudo
    com o * em select

    Retorno: Lista de objetos Registro

    """
    supabase = get_client()
    response = supabase.table(TABLE_NAME).select("*").execute()
    registros = response.data if response.data else []
    return registros


def buscar_registro(
    registro_id: int,
) -> Optional[Registro]:
    """
    Busca um registro no banco pelo ID.

    Parametros:
        registro_id (int): Identificador único do registro a ser buscado.

    Returns:
        Optional[Registro]: Objeto `Registro` contendo id, nome e email, 
        ou `None` caso não seja encontrado

    """
    supabase = get_client()
    response = supabase.table(TABLE_NAME).select("*").eq("id", registro_id).execute()

    if response.data:
        return Registro(**response.data[0])
    return None


def inserir_registro(data: RegistroCreate) -> Registro:
    """
    Função responsável por inserir usuários na tabela.

    Parâmetro de entrada: objeto RegistroCreate contendo
    name, email, senha e role.

    Retorno: Objeto Registro criado
    """

    supabase = get_client()
    senha_truncada = data.senha[:72]
    print(f"Tamanho da senha (string): {len(senha_truncada)}")
    senha_bytes = senha_truncada.encode('utf-8')
    print(f"Tamanho da senha (bytes): {len(senha_bytes)}")
    senha_hash = bcrypt.hash(senha_truncada)
    # senha_hash = bcrypt.hash(data.senha)
    response = (
        supabase.table(TABLE_NAME)
        .insert({
            "name": data.name,
            "email": data.email,
            "senha_hash": senha_hash,
            "role": data.role,
            "ativo": True
        })
        .execute()
    )

    return Registro(**response.data[0])



def atualizar_registro(registro_id: int, name: str, email: str) -> Registro:
    """
    função para atualizar registro de usuarios ja existente pelo id.

    parametros: id, name, email.

    retorno : Objeto Registro atualizado

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


def deletar_registro(registro_id: int) -> None:
    """
    Função responsavel por deletar um usuario.

    parametros: id

    retorno: Objeto Registro deletado
    """
    supabase = get_client()
    response = supabase.table(TABLE_NAME).delete().eq("id", registro_id).execute()

    if not response.data:
        raise HTTPException(
            status_code=404, detail=f"Registro com id {registro_id} não encontrado"
        )

    return Registro(**response.data[0])


def buscar_por_email(email: str):
    supabase = get_client()
    response = supabase.table(TABLE_NAME).select("*").eq("email",email).execute()
    if response.data:
        return response.data[0]
    
    return None


