from pydantic import BaseModel


class RegistroCreate(BaseModel):
    name: str
    email: str


class Registro(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}
