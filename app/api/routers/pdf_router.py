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

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/upload_pdf")
async def upload_pdf_route(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Rota para upload de PDF. Somente usuários 'gerente' podem enviar.
    Agora processa automaticamente: extrai texto e gera embeddings.
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

        file_display_name = file.filename if file.filename else ""
        "arquivo_sem_nome.pdf"

        supabase = get_client()

        # Validação de duplicata
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

        # 1. Faz upload do PDF
        result = upload_pdf_service(
            file_path=temp_file_path,
            user_id=str(user_uuid),
            display_name=file_display_name,
        )

        # Limpa arquivo temporário
        os.remove(temp_file_path)

        # 2. Processa o PDF (extrai texto e salva no banco)
        print(
            "[DEBUG] Iniciando processamento automático do PDF: " f"{file_display_name}"
        )

        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        # Busca o registro recém-criado
        record = (
            supabase_admin.table("pdf_uploads")
            .select("id, file_path, status")
            .eq("file_name", file_display_name)
            .limit(1)
            .execute()
        )

        if not record.data:
            raise HTTPException(
                status_code=404, detail="PDF não encontrado após upload."
            )

        pdf_data = record.data[0]
        file_path = pdf_data.get("file_path")

        # Extrai texto do PDF
        full_text, meta = download_pdf_and_extract_text(
            file_path=file_path,
            bucket_name="pdfs",
            expire_seconds=3600,
            save_temp=False,
        )

        # Atualiza o registro com o texto extraído
        update_payload = {
            "status": "processado",
            "full_text": full_text,
            "processed_at": meta.get("downloaded_at"),
        }

        update_res = (
            supabase_admin.table("pdf_uploads")
            .update(update_payload)
            .eq("file_path", file_path)
            .execute()
        )

        print(f"[DEBUG] Texto extraído e salvo ({meta.get('pages')} páginas).")

        # 3. Gera embeddings
        print("[DEBUG] Iniciando geração de embeddings...")
        embed_result = generate_embedding_for_pdf(file_display_name)
        print(f"[DEBUG] Embeddings gerados: {embed_result}")

        return {
            **result,
            "processing": {
                "text_extraction": "sucesso",
                "embedding_generation": "sucesso",
                "chunks_processed": embed_result.get("chunks", 0),
                "pages": meta.get("pages", 0),
                "model_used": embed_result.get("model"),
            },
        }

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
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        query = supabase_admin.table("pdf_uploads").select("*")

        # Se quiser que apenas o gerente veja tudo, e outros só os seus:
        if user.get("role") != "gerente":
            query = query.eq("user_id", user["sub"])

        db_res = query.execute()

        if not db_res.data:
            return {"message": "Nenhum PDF encontrado.", "pdfs": []}

        return {"pdfs": db_res.data}

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
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        # Busca o registro correspondente ao display_name
        record = (
            supabase_admin.table("pdf_uploads")
            .select("id, file_path")
            .eq("file_name", display_name)
            .single()
            .execute()
        )

        if not record.data:
            raise HTTPException(status_code=404, detail="PDF não encontrado.")

        file_path = record.data["file_path"]

        # Remove do Storage
        delete_res = supabase_admin.storage.from_("pdfs").remove([file_path])
        print(f"[DEBUG] Resposta da exclusão no Storage: {delete_res}")

        # Remove do banco
        db_res = (
            supabase_admin.table("pdf_uploads")
            .delete()
            .eq("id", record.data["id"])
            .execute()
        )
        print(f"[DEBUG] Resposta da exclusão no banco: {db_res}")

        return {"message": f"PDF '{display_name}' removido com sucesso."}

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
    - Recebe JSON: { "file_name": "exemplo.pdf" }
    - Busca o registro pelo nome de exibição (file_name)
    - Baixa o PDF do Supabase Storage
    - Extrai o texto com PyMuPDF
    - Atualiza o status para 'processado'
    - Armazena o texto extraído na coluna 'full_text'
    - Retorna metadados e preview do texto extraído

    Somente gerentes podem processar PDFs.
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

    print(
        "[DEBUG] Iniciando processamento do PDF: "
        f"{file_name} pelo usuário {user['email']}"
    )

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    try:
        record = (
            supabase_admin.table("pdf_uploads")
            .select("id, file_path, status")
            .eq("file_name", file_name)
            .limit(1)
            .execute()
        )

        data = record.data
        if not data:
            print(f"[ERROR] PDF não encontrado no banco: {file_name}")
            raise HTTPException(status_code=404, detail="PDF não encontrado.")

        pdf_data = data[0]
        file_path = pdf_data.get("file_path")

        print(
            "[DEBUG] Registro encontrado: "
            f"id={pdf_data.get('id')} file_path={file_path}"
        )

    except Exception as e:
        print(f"[ERROR] Erro ao consultar pdf_uploads: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao consultar registro: {str(e)}"
        )

    try:
        full_text, meta = download_pdf_and_extract_text(
            file_path=file_path,
            bucket_name="pdfs",
            expire_seconds=3600,
            save_temp=False,
        )
        print(
            "[DEBUG] Extração concluída: "
            f"{meta.get('pages')} páginas, {meta.get('bytes')} bytes"
        )
    except Exception as e:
        print(f"[ERROR] Erro na extração do PDF: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao extrair texto do PDF: {str(e)}"
        )

    try:
        update_payload = {
            "status": "processado",
            "full_text": full_text,
            "processed_at": meta.get("downloaded_at"),
        }

        update_res = (
            supabase_admin.table("pdf_uploads")
            .update(update_payload)
            .eq("file_path", file_path)
            .execute()
        )
        print("[DEBUG] Retorno do update:", update_res)

        print(
            "[DEBUG] Registro atualizado "
            f"(id={pdf_data.get('id')}, status=processado)."
        )

    except Exception as e:
        print(f"[ERROR] Erro ao atualizar registro no banco: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao atualizar registro: {str(e)}"
        )

    return {
        "message": f"PDF '{file_name}' processado com sucesso.",
        "metadata": meta,
        "text_preview": (
            full_text[:800] + "" "..." if len(full_text) > 800 else full_text
        ),
    }
