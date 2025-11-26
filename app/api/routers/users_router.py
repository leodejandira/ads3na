from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.api.schema.registros import Registro, RegistroCreate
from app.services.auth_service import get_current_user
from app.services.register_service import (
    atualizar_registro, buscar_registro, deletar_registro, 
    inserir_registro, listar_registros
)

router = APIRouter()

@router.post("/register", response_model=Registro)
def register_route(novo_usuario: RegistroCreate, user: dict = Depends(get_current_user)):
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem registrar novos usuários.",
        )
    return inserir_registro(novo_usuario)

@router.get("/usuarios", response_model=List[Registro])
def listar_usuarios_route(user: dict = Depends(get_current_user)):
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem listar usuários.",
        )
    try:
        return listar_registros()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usuarios/{registro_id}", response_model=Registro)
def buscar_usuario_route(registro_id: int, user: dict = Depends(get_current_user)):
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem buscar usuários.",
        )
    try:
        usuario = buscar_registro(registro_id)
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        return usuario
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao buscar usuário.")

@router.put("/usuarios/{registro_id}", response_model=Registro)
def atualizar_usuario_route(registro_id: int, name: str, email: str, user: dict = Depends(get_current_user)):
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem atualizar usuários.",
        )
    try:
        return atualizar_registro(registro_id, name, email)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao atualizar usuário.")

@router.delete("/usuarios/{registro_id}", response_model=Registro)
def deletar_usuario_route(registro_id: int, user: dict = Depends(get_current_user)):
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem deletar usuários.",
        )
    try:
        return deletar_registro(registro_id)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao deletar usuário.")