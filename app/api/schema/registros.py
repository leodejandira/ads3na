from pydantic import BaseModel, EmailStr


class RegistroCreate(BaseModel):
    name: str
    email: EmailStr
    senha: str
    role: str


class Registro(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    ativo: bool

    model_config = {"from_attributes": True}
