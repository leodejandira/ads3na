from pydantic import BaseModel, EmailStr
from enum import Enum

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
    name: str
    email: EmailStr
    role: UserRole
    ativo: bool

    model_config = {"from_attributes": True}
