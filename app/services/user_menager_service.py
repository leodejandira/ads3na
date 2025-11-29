from typing import List, Optional
from fastapi import HTTPException
from passlib.hash import bcrypt
from app.api.schema.registros import Registro, RegistroCreate
from app.db.database import get_client

TABLE_NAME = "users"

class UserManagerService:
    """
    Classe responsável por operações de CRUD de usuários.
    """

    def __init__(self):
        self.supabase = get_client()

    def listar_registros(self) -> List[Registro]:
        try:
            response = self.supabase.table(TABLE_NAME).select("*").execute()
            registros = response.data if response.data else []
            return [Registro(**registro) for registro in registros]
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao listar registros: {str(e)}",
            )
        
    def buscar_registro(self, registro_id: int) -> Optional[Registro]:
        try:
            response = (
                self.supabase.table(TABLE_NAME)
                .select("*")
                .eq("id", registro_id)
                .execute()
            )

            if response.data:
                return Registro(**response.data[0])
            return None
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar registro: {str(e)}",
            )
        
    def inserir_registro(self, data: RegistroCreate) -> Registro:
        try:

            try:
                auth_response = self.supabase.auth.sign_up(
                    {"email": data.email, "password": data.senha}
                )
            except Exception as auth_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Erro no Supabase Auth: {str(auth_error)}",
                )
            
            if not auth_response.user or not auth_response.user.id:
                raise HTTPException(
                    status_code=500,
                    detail="Falha ao criar usuário no Auth ou obter UUID"
                )
            
            auth_user_uuid = auth_response.user.id
            senha_truncada = data.senha[:72]
            senha_hash = bcrypt.hash(senha_truncada)

            response = (
                self.supabase.table(TABLE_NAME)
                .insert(
                    {
                        "auth_user_id": auth_user_uuid,
                        "name": data.name,
                        "email": data.email,
                        "senha_hash": senha_hash,
                        "role": data.role,
                        "ativo": True,
                    }
                )
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao inserir perfil no banco de dados.",
                )
            
            return Registro(**response.data[0])
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao inserir registro: {str(e)}",
            )

    
    def atualizar_registro(self, registro_id: int, name: str, email: str) -> Registro:
        response = (
            self.supabase.table(TABLE_NAME)
            .update({"name": name, "email": email})
            .eq("id", registro_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Registro com id {registro_id} não encontrado.",
            )
        
        return Registro(**response.data[0])
    
    def deletar_registro(self, registro_id: int) -> Registro:
        response = (
            self.supabase.table(TABLE_NAME)
            .delete()
            .eq("id", registro_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Registro com id {registro_id} não encontrado.",
            )
        
        return Registro(**response.data[0])
    

    def buscar_por_email(self, email: str):
        response = (
            self.supabase.table(TABLE_NAME)
            .select("*")
            .eq("email", email)
            .execute()
        )

        if response.data:
            return response.data[0]
        
        return None
