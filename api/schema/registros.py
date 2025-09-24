from pydantic import BaseModel


class RegistroCreate(BaseModel):
    valor: str


class Registro(BaseModel):
    id: int
    valor: str

    class Config:
        orm_mode = True
