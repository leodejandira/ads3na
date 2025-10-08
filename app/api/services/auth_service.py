from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException
from passlib.hash import bcrypt

from utils.dbfunctions import buscar_por_email

SECRET_KEY = "sua_chave_super_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def gerar_token(user):
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
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    if not user["ativo"]:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    return gerar_token(user)
