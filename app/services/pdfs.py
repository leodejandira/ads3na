import os
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Tuple

import fitz  # PyMuPDF 1.22.5
import requests  # 2.31.0
from fastapi import HTTPException
from supabase import create_client

from app.db.database import get_client


def upload_pdf(
    file_path: str,
    bucket_name: str = "pdfs",
    display_name: str = None,
    expire_seconds: int = 3600,
    user_id: str = None,
):
    """
    Faz upload de um arquivo PDF para o Supabase Storage
    e registra no banco.

    parametros: File path do arquivo a ser enviado,
    nome do bucket(ja definido), nome de exibição,
    tempo de expiração da URL assinada e ID do usuário
    que está fazendo o upload.

    retorno: dicionário com nome do arquivo,
    nome de exibição e URL assinada.
    esse retorno é adicionado no banco de dados,
    na tabela 'pdf_uploads'.
    """
    # Cliente "anon" normal para upload no storage
    supabase = get_client()

    # Cliente admin para bypass RLS (usar a Service Role Key)
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Gera nome único do arquivo
    file_ext = os.path.splitext(file_path)[1] or ".pdf"
    file_name = f"{uuid.uuid4()}{file_ext}"

    if display_name is None:
        display_name = os.path.basename(file_path)

    print(f"[DEBUG] Iniciando upload do arquivo: {file_path}")
    print(f"[DEBUG] Nome final do arquivo no bucket: {file_name}")

    # Upload do arquivo
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            print(f"[DEBUG] Tamanho do arquivo lido: {len(file_bytes)} bytes")

            upload_res = supabase.storage.from_(bucket_name).upload(
                path=file_name,
                file=file_bytes,
                file_options={
                    "content_type": "application/pdf",
                    "cache_control": "3600",
                },
            )

            print(f"[DEBUG] Resposta do Supabase Storage: {upload_res}")

    except Exception as e:
        print(f"[ERROR] Erro ao ler/enviar arquivo: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao ler/enviar arquivo: {str(e)}"
        )

    # Gera URL assinada
    signed_url_res = supabase.storage.from_(bucket_name).create_signed_url(
        file_name, expire_seconds
    )
    print(f"[DEBUG] Resposta de URL assinada: {signed_url_res}")

    signed_url = (
        signed_url_res.get("signedURL") if isinstance(signed_url_res, dict) else None
    )
    if not signed_url:
        raise HTTPException(
            status_code=500, detail="Não foi possível gerar a URL assinada"
        )

    # Salva no banco usando cliente admin (bypass RLS)
    try:
        db_res = (
            supabase_admin.table("pdf_uploads")
            .insert(
                {
                    "user_id": str(user_id),
                    "file_name": str(display_name),
                    "file_path": str(file_name),
                    "status": "pendente",
                }
            )
            .execute()
        )

        print(f"[DEBUG] Resposta do banco: {db_res}")

        if hasattr(db_res, "error") and db_res.error:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao registrar PDF no banco: {db_res.error}",
            )

    except Exception as e:
        print(f"[ERROR] Erro ao salvar registro no banco: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao salvar registro no banco: {str(e)}"
        )

    return {
        "file_name": file_name,
        "display_name": display_name,
        "signed_url": signed_url,
    }


def list_pdfs(user_id: str = None, bucket_name: str = "pdfs"):
    """
    Lista os PDFs enviados, filtrando opcionalmente por usuário.

    parâmetros:
        user_id: (opcional) ID do usuário para filtrar os uploads.
        bucket_name: nome do bucket onde os arquivos estão.

    retorno:
        Lista de dicionários contendo nome, caminho e status dos PDFs.
    """
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    try:
        query = supabase_admin.table("pdf_uploads").select("*")

        if user_id:
            query = query.eq("user_id", user_id)

        res = query.execute()
        print(f"[DEBUG] Listagem concluída: {len(res.data)} PDFs encontrados")

        if hasattr(res, "error") and res.error:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao listar PDFs: {res.error}",
            )

        return res.data

    except Exception as e:
        print(f"[ERROR] Erro ao listar PDFs: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar PDFs: {str(e)}")


def delete_pdf(display_name: str, bucket_name: str = "pdfs"):
    """
    Deleta um PDF do Supabase Storage e remove o registro no banco,
    usando o nome de exibição (display_name).

    parâmetros:
        display_name: nome visível do arquivo (coluna 'file_name' no banco).
        bucket_name: nome do bucket (padrão: 'pdfs').

    retorno:
        Mensagem de sucesso.
    """
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    try:
        # Busca o file_path no banco a partir do display_name
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

        # Remove o arquivo do Supabase Storage
        delete_res = supabase_admin.storage.from_(bucket_name).remove([file_path])
        print(f"[DEBUG] Resposta da exclusão no Storage: {delete_res}")

        # Remove o registro no banco
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


def download_pdf_and_extract_text(
    file_path: str,
    bucket_name: str = "pdfs",
    expire_seconds: int = 3600,
    save_temp: bool = False,
) -> Tuple[str, Dict]:
    """
    Baixa um PDF do Supabase Storage usando uma
    URL assinada e extrai o texto usando PyMuPDF.
    parâmetros:
        file_path: caminho do arquivo no bucket.
        bucket_name: nome do bucket (padrão: 'pdfs').
        expire_seconds: tempo de expiração da
        URL assinada (padrão: 3600 segundos).
        save_temp: se True, salva o PDF em um
        arquivo temporário.

    Retorna:
        Texto extraido, metadata
    """

    print(f"[DEBUG] Iniciando download e extração do PDF: {file_path}")

    supabase = get_client()

    try:
        signed_resp = supabase.storage.from_(bucket_name).create_signed_url(
            file_path, expire_seconds
        )
        signed_url = (
            signed_resp.get("signedURL")
            or signed_resp.get("signed_url")
            or signed_resp.get("url")
        )

        if not signed_url:
            raise HTTPException(
                status_code=500,
                detail="Não foi possivel gerar a " f"URL assinada para {file_path}",
            )

        print("[DEBUG] URL assinada gerada com sucesso.")
    except Exception as e:
        print(f"[ERROR] Falha ao gerar signed URL: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar URL assinada: {str(e)}",
        )

    temp_file = tempfile.NamedTemporaryFile(delete=not save_temp, suffix=".pdf")
    temp_path = temp_file.name
    total_bytes = 0

    try:
        print("[DEBUG] Baixando o PDF da URL assinada...")
        with requests.get(signed_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
                    total_bytes += len(chunk)
        temp_file.flush()
        print(f"[DEBUG] Download concluido ({total_bytes} bytes).")
    except Exception as e:
        print(f"[ERROR] Falha ao baixar PDF: {e}")

        try:
            if not save_temp and os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail=f"Erro ao baixar o PDF: {str(e)}")

    try:
        print("[DEBUG] Iniciando extração do texto com PyMuPDF...")
        with fitz.open(temp_path) as doc:
            pages = doc.page_count
            text_parts = []
            for page in doc:
                page_text = page.get_text("text").replace("\r", "").strip()
                if page_text:
                    text_parts.append(page_text)
            full_text = "\n\n".join(text_parts)
        print(f"[DEBUG] Extração concluida com sucesso ({pages} páginas).")
    except Exception as e:
        print(f"[ERROR] Falha ao extrair texto do PDF: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao extrair texto do PDF: {str(e)}"
        )

    finally:
        if not save_temp:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    metadata = {
        "pages": pages,
        "bytes": total_bytes,
        "downloaded_at": datetime.utcnow().isoformat() + "Z",
        "file_path": file_path,
    }
    if save_temp:
        metadata["local_path"] = temp_path

    return full_text, metadata


def upload_and_extract_text(
    file_path: str,
    display_name: str,
    user_id: str,
    bucket_name: str = "pdfs"
):
    """
    Faz upload do PDF e extrai o texto, atualizando o banco com o texto extraído.
    Combina upload_pdf + download_pdf_and_extract_text em uma operação.
    """
    try:
        print(f"[DEBUG] Iniciando upload e extração para: {display_name}")
        
        # 1. Faz upload do PDF
        upload_result = upload_pdf(
            file_path=file_path,
            display_name=display_name,
            user_id=user_id,
            bucket_name=bucket_name
        )

        # 2. Extrai texto do PDF recém-enviado
        file_path_in_bucket = upload_result["file_name"]
        
        print(f"[DEBUG] Iniciando extração de texto do PDF: {display_name}")
        full_text, meta = download_pdf_and_extract_text(
            file_path=file_path_in_bucket,
            bucket_name=bucket_name,
            expire_seconds=3600,
            save_temp=False,
        )

        # 3. Atualiza o registro com o texto extraído
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        update_payload = {
            "status": "processado",
            "full_text": full_text,
            "processed_at": meta.get("downloaded_at"),
        }

        update_res = (
            supabase_admin.table("pdf_uploads")
            .update(update_payload)
            .eq("file_path", file_path_in_bucket)
            .execute()
        )

        print(f"[DEBUG] Texto extraído e salvo ({meta.get('pages')} páginas).")

        return {
            **upload_result,
            "processing": {
                "text_extraction": "sucesso",
                "pages": meta.get("pages", 0),
                "embedding_generation": "pendente",
            },
        }

    except Exception as e:
        print(f"[ERROR] Erro no upload_and_extract_text: {e}")
        raise