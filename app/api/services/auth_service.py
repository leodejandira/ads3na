import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from passlib.hash import bcrypt

from app.api.services.register_service import buscar_por_email

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def gerar_token(user):
    """
    Gera token JWT para autenticação de acesso às rotas de gerente ou usuário.

    O token contém informações do usuário (ID, e-mail e papel)
    e é válido por 60 minutos.

    Args:
        user (dict): Um dicionário contendo os dados do usuário.
        Espera-se que tenha as chaves:
            - "id": Identificador único do usuário.
            - "email": Endereço de e-mail do usuário.
            - "role": Papel do usuário no sistema (ex: 'gerente', 'usuario').

    Returns:
        str: Token JWT codificado como uma string.
    """
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.now(tz=timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def login(email: str, senha: str):
    user = buscar_por_email(email)
    if not user or not bcrypt.verify(senha, user["senha_hash"]):
        raise HTTPException(status_code=401,
                            detail="Credenciais inválidas")
    if not user["ativo"]:
        raise HTTPException(status_code=403,
                            detail="Usuário inativo")
    return gerar_token(user)
