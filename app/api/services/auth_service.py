import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from passlib.hash import bcrypt

from utils.dbfunctions import buscar_por_email

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def gerar_token(user):
    """
    Gera um token JWT para autenticação de acesso às rotas de gerente ou usuário.

    O token contém informações do usuário (ID, e-mail e papel) e é válido por 60 minutos.

    Args:
        user (dict): Um dicionário contendo os dados do usuário. Espera-se que tenha as chaves:
            - "id": Identificador único do usuário.
            - "email": Endereço de e-mail do usuário.
            - "role": Papel do usuário no sistema (ex: 'gerente', 'usuario').

    Returns:
        str: Token JWT codificado como uma string.
    """
    try:
        payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.now(tz=timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
    
    except KeyError as e:
        raise HTTPException(
            status_code = 400,
            detail=f"Campo obrigatório ausente no usuário: {str(e)}"
        )


def login(email: str, senha: str):
    """
    Realiza o login de um usuário autenticando suas credenciais.

    Verifica se o e-mail existe, se a senha está correta e se o usuário está ativo.
    Em caso de sucesso, retorna um token JWT para autenticação.

    Parametros:
        email (str): Endereço de e-mail do usuário.
        senha (str): Senha em texto plano fornecida pelo usuário.

    Raises:
        HTTPException: 
            - 401 se as credenciais forem inválidas.
            - 403 se o usuário estiver inativo.

    Retorno:
        str: Token JWT válido por 60 minutos.
    """
    user = buscar_por_email(email)
    if not user or not bcrypt.verify(senha, user["senha_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    if not user["ativo"]:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    return gerar_token(user)
