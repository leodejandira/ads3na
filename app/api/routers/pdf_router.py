import os
import tempfile
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from fastapi.templating import Jinja2Templates
from supabase import create_client

from app.db.database import get_client
from app.services.auth_service import get_current_user  # ← MUDANÇA AQUI
from app.services.embedding_service import generate_embedding_for_pdf
from app.services.pdfs import download_pdf_and_extract_text
from app.services.pdfs import upload_pdf as upload_pdf_service
from app.services.pdfs import (
    download_pdf_and_extract_text, 
    upload_pdf as upload_pdf_service,
    list_pdfs,  # ← Adicionar
    delete_pdf,
    upload_and_extract_text   # ← Adicionar
)
from app.services.embedding_service import generate_embedding_for_pdf

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/upload_pdf")
async def upload_pdf_route(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Rota para upload de PDF. Somente usuários 'gerente' podem enviar.
    AGORA: Apenas chama o service que faz upload + extração de texto.
    """
    try:
        # Validação do role
        if user.get("role") != "gerente":
            raise HTTPException(
                status_code=403,
                detail="Acesso negado. Somente gerentes podem enviar PDFs.",
            )

        # Validar UUID do usuário
        try:
            user_uuid = UUID(str(user["sub"]))
        except ValueError:
            raise HTTPException(
                status_code=400, detail="ID do usuário no token não é UUID válido."
            )

        file_display_name = file.filename if file.filename else "arquivo_sem_nome.pdf"

        supabase = get_client()

        # Validação de duplicata (mantida na rota por ser regra de negócio)
        exists = (
            supabase.table("pdf_uploads")
            .select("id")
            .eq("file_name", file_display_name)
            .execute()
        )

        if exists.data:
            raise HTTPException(
                status_code=409, detail="Já existe um PDF com esse nome."
            )

        print(f"Current user (UUID): {user_uuid}")
        print(f"Arquivo recebido: {file.filename}")

        # Salva arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name

        print(f"Arquivo temporário criado em: {temp_file_path}")

        # 1. Chama o service que faz upload + extração de texto
        result = upload_and_extract_text(
            file_path=temp_file_path,
            display_name=file_display_name,
            user_id=str(user_uuid),
        )

        # Limpa arquivo temporário
        os.remove(temp_file_path)

        print("[DEBUG] Upload e extração concluídos. Embeddings serão gerados via rota RAG.")

        return result

    except HTTPException as http_e:
        # Limpa arquivo temporário em caso de erro
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise http_e
    except Exception as e:
        # Limpa arquivo temporário em caso de erro
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        print(f"Erro inesperado no upload_pdf_route: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdfs")
async def list_pdfs_route(user: dict = Depends(get_current_user)):
    """
    Lista todos os PDFs cadastrados no Supabase.
    - Gerentes veem todos os PDFs.
    - Outros usuários (se existir essa regra) veem apenas os próprios.
    """
    try:
        # Se não for gerente, filtra pelo user_id
        user_id = None if user.get("role") == "gerente" else user["sub"]
        pdfs = list_pdfs(user_id=user_id)
        return {"pdfs": pdfs}
    except Exception as e:
        print(f"[ERROR] Erro ao listar PDFs: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar PDFs: {str(e)}")


@router.delete("/pdfs/{display_name}")
async def delete_pdf_route(display_name: str, user: dict = Depends(get_current_user)):
    """
    Deleta um PDF pelo nome de exibição (display_name).
    Somente gerentes podem excluir.
    """
    if user.get("role") != "gerente":
        raise HTTPException(
            status_code=403, detail="Apenas gerentes podem deletar PDFs."
        )

    try:
        result = delete_pdf(display_name)
        return result
    except Exception as e:
        print(f"[ERROR] Erro ao deletar PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao deletar PDF: {str(e)}")


@router.post("/pdfs/process")
async def process_pdf_route(
    body: dict = Body(...),
    user: dict = Depends(get_current_user),
):
    """
    Processa um PDF já enviado ao Supabase:
    - Gera embeddings (vetorização)
    - Atualiza o status para 'vetorizado'
    """
    if user.get("role") != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Somente gerentes podem processar PDFs.",
        )

    file_name = body.get("file_name")
    if not file_name:
        raise HTTPException(
            status_code=400, detail="Campo 'file_name' é obrigatório no corpo JSON."
        )

    print(f"[DEBUG] Iniciando vetorização do PDF: {file_name}")

    try:
        # 1. Gera embeddings (vetorização)
        print("[DEBUG] Iniciando geração de embeddings...")
        embed_result = generate_embedding_for_pdf(file_name)
        print(f"[DEBUG] Embeddings gerados: {embed_result}")

        # 2. Atualiza o status para 'vetorizado'
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        update_res = (
            supabase_admin.table("pdf_uploads")
            .update({"status": "vetorizado"})
            .eq("file_name", file_name)
            .execute()
        )

        print(f"[DEBUG] Status atualizado para vetorizado: {update_res}")

        return {
            "message": f"PDF '{file_name}' vetorizado com sucesso!",
            "chunks_processed": embed_result.get("chunks", 0),
            "model_used": embed_result.get("model"),
        }

    except Exception as e:
        print(f"[ERROR] Erro na vetorização do PDF: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao vetorizar PDF: {str(e)}"
        )