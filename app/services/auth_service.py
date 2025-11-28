import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import bcrypt

from app.services.user_menager_service import buscar_por_email

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Adicionar o OAuth2 scheme aqui
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

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
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

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

    auth_uuid = user.get("auth_user_id")

    if not auth_uuid:
        print(
            (
                f"ERRO DE TOKEN: Usuário {user.get('email')} "
                "não possui 'auth_user_id' associado."
            )
        )

        raise HTTPException(
            status_code=500,
            detail="Erro interno de autenticação:"
            "ID de usuário (UUID) não encontrado.",
        )

    payload = {
        "sub": str(auth_uuid),
        "email": user["email"],
        "role": user["role"],
        "exp": datetime.now(tz=timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def login(email: str, senha: str):
    """
    Função de login que valida o usuário e retorna o token.
    """
    user = buscar_por_email(email)

    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not bcrypt.verify(senha, user["senha_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not user.get("ativo", True):
        raise HTTPException(status_code=403, detail="Usuário inativo")

    return gerar_token(user)