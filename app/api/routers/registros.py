# # api/routers/registros.py
# from typing import List

# from api.schema.registros import Registro, RegistroCreate
# from fastapi import APIRouter, HTTPException

# from app.services import registros as service

# router = APIRouter(prefix="/api/registros", tags=["Registros"])


# @router.get("/", response_model=List[Registro])
# def listar():
#     return service.listar_registros()


# @router.get("/{registro_id}", response_model=Registro)
# def buscar(registro_id: int):
#     registro = service.buscar_registro(registro_id)
#     if not registro:
#         raise HTTPException(status_code=404, detail="Registro não encontrado")
#     return registro


# @router.post("/", status_code=201)
# def inserir(data: RegistroCreate):
#     service.inserir_registro(data)
#     return {"mensagem": "inserido com sucesso"}


# @router.delete("/{registro_id}", status_code=200)
# def deletar(registro_id: int):
#     service.deletar_registro(registro_id)
#     return {"mensagem": "deletado com sucesso"}
