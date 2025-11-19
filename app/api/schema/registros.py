from enum import Enum
<<<<<<< HEAD
from uuid import UUID
=======
>>>>>>> 57810807baa72815a6446bddd8cafcab8d7bcac8

from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    USUARIO = "usuario"
    GERENTE = "gerente"


class RegistroCreate(BaseModel):
    name: str
    email: EmailStr
    senha: str
    role: UserRole


class Registro(BaseModel):
    id: int
<<<<<<< HEAD
    auth_user_id: UUID
=======
>>>>>>> 57810807baa72815a6446bddd8cafcab8d7bcac8
    name: str
    email: EmailStr
    role: UserRole
    ativo: bool

    model_config = {"from_attributes": True}
