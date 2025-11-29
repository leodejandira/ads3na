import os
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Tuple

import fitz  # PyMuPDF
import requests
from fastapi import HTTPException
from supabase import create_client

from app.db.database import get_client


class PDFService:
    """
    Classe responsável por todas as operações relacionadas a PDFs:
    upload, listagem, exclusão, download e extração de texto.
    Mantém exatamente o mesmo comportamento das funções originais.
    """

    def __init__(self):
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY_ROLE")
        self.supabase_admin = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)

    def upload_pdf(
        self,
        file_path: str,
        bucket_name: str = "pdfs",
        display_name: str = None,
        expire_seconds: int = 3600,
        user_id: str = None,
    ):
        """
        Faz upload de um arquivo PDF para o Supabase Storage
        e registra no banco.

        parâmetros:
            file_path: caminho do arquivo a ser enviado.
            bucket_name: nome do bucket (padrão: "pdfs").
            display_name: nome de exibição.
            expire_seconds: validade da URL assinada.
            user_id: ID do usuário que está fazendo o upload.

        retorno:
            dict contendo file_name, display_name e signed_url.
        """

        supabase = get_client()

        file_ext = os.path.splitext(file_path)[1] or ".pdf"
        random_name = f"{uuid.uuid4()}{file_ext}"

        if display_name is None:
            display_name = os.path.basename(file_path)

        print(f"[DEBUG] Iniciando upload: {file_path} → {random_name}")

        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            upload_res = supabase.storage.from_(bucket_name).upload(
                path=random_name,
                file=file_bytes,
                file_options={
                    "content_type": "application/pdf",
                    "cache_control": "3600",
                },
            )

        except Exception as e:
            print(f"[ERROR] Erro ao enviar arquivo: {e}")
            raise HTTPException(
                status_code=500, detail=f"Erro ao enviar arquivo: {str(e)}"
            )

        signed_url_res = supabase.storage.from_(bucket_name).create_signed_url(
            random_name, expire_seconds
        )

        signed_url = (
            signed_url_res.get("signedURL") if isinstance(signed_url_res, dict) else None
        )

        if not signed_url:
            raise HTTPException(
                status_code=500,
                detail="Não foi possível gerar a URL assinada",
            )

        try:
            self.supabase_admin.table("pdf_uploads").insert(
                {
                    "user_id": str(user_id),
                    "file_name": str(display_name),
                    "file_path": str(random_name),
                    "status": "pendente",
                }
            ).execute()

        except Exception as e:
            print(f"[ERROR] Erro ao registrar PDF no banco: {e}")
            raise HTTPException(
                status_code=500, detail=f"Erro ao registrar PDF no banco: {str(e)}"
            )

        return {
            "file_name": random_name,
            "display_name": display_name,
            "signed_url": signed_url,
        }

    def list_pdfs(self, user_id: str = None, bucket_name: str = "pdfs"):
        """
        Lista os PDFs enviados, filtrando opcionalmente por usuário.

        parâmetros:
            user_id: ID do usuário (opcional).
            bucket_name: nome do bucket.

        retorno:
            lista com PDFs armazenados.
        """
        try:
            query = self.supabase_admin.table("pdf_uploads").select("*")
            if user_id:
                query = query.eq("user_id", user_id)

            res = query.execute()
            print(f"[DEBUG] {len(res.data)} PDFs encontrados")
            return res.data

        except Exception as e:
            print(f"[ERROR] Erro ao listar PDFs: {e}")
            raise HTTPException(
                status_code=500, detail=f"Erro ao listar PDFs: {str(e)}"
            )

    def delete_pdf(self, display_name: str, bucket_name: str = "pdfs"):
        """
        Deleta um PDF do Supabase Storage e remove o registro no banco.

        parâmetros:
            display_name: nome visível (coluna file_name).
            bucket_name: bucket de armazenamento.

        retorno:
            mensagem de sucesso.
        """
        try:
            record = (
                self.supabase_admin.table("pdf_uploads")
                .select("id, file_path")
                .eq("file_name", display_name)
                .single()
                .execute()
            )

            if not record.data:
                raise HTTPException(status_code=404, detail="PDF não encontrado.")

            file_path = record.data["file_path"]

            self.supabase_admin.storage.from_(bucket_name).remove([file_path])

            self.supabase_admin.table("pdf_uploads").delete().eq(
                "id", record.data["id"]
            ).execute()

            return {"message": f"PDF '{display_name}' removido com sucesso."}

        except Exception as e:
            print(f"[ERROR] Erro ao deletar PDF: {e}")
            raise HTTPException(
                status_code=500, detail=f"Erro ao deletar PDF: {str(e)}"
            )

    def download_pdf_and_extract_text(
        self,
        file_path: str,
        bucket_name: str = "pdfs",
        expire_seconds: int = 3600,
        save_temp: bool = False,
    ) -> Tuple[str, Dict]:
        """
        Baixa um PDF via URL assinada e extrai seu texto com PyMuPDF.

        parâmetros:
            file_path: caminho do arquivo no bucket.
            bucket_name: bucket de armazenamento.
            expire_seconds: tempo de expiração da URL.
            save_temp: manter ou não o arquivo temporário.

        retorno:
            full_text extraído e metadata.
        """

        print(f"[DEBUG] Iniciando download e extração: {file_path}")

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
                    detail="Não foi possível gerar URL assinada",
                )

        except Exception as e:
            print(f"[ERROR] Falha ao gerar signed URL: {e}")
            raise HTTPException(
                status_code=500, detail=f"Erro ao gerar URL assinada: {str(e)}"
            )

        temp_file = tempfile.NamedTemporaryFile(delete=not save_temp, suffix=".pdf")
        temp_path = temp_file.name
        total_bytes = 0

        try:
            print("[DEBUG] Baixando PDF...")

            with requests.get(signed_url, stream=True, timeout=60) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        total_bytes += len(chunk)

            temp_file.flush()

        except Exception as e:
            print(f"[ERROR] Falha ao baixar PDF: {e}")
            raise HTTPException(status_code=500, detail=f"Erro ao baixar PDF: {str(e)}")

        try:
            print("[DEBUG] Extraindo texto...")

            with fitz.open(temp_path) as doc:
                pages = doc.page_count
                text_parts = [
                    page.get_text("text").replace("\r", "").strip()
                    for page in doc
                    if page.get_text("text").strip()
                ]

            full_text = "\n\n".join(text_parts)

        except Exception as e:
            print(f"[ERROR] Falha ao extrair texto: {e}")
            raise HTTPException(
                status_code=500, detail=f"Erro ao extrair texto: {str(e)}"
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
        self,
        file_path: str,
        display_name: str,
        user_id: str,
        bucket_name: str = "pdfs",
    ):
        """
        Faz upload do PDF, baixa, extrai o texto e atualiza no banco.

        fluxo:
            - upload_pdf
            - download_pdf_and_extract_text
            - atualização da tabela pdf_uploads

        retorno:
            detalhes do processamento.
        """

        try:
            print(f"[DEBUG] Upload + Extração: {display_name}")

            upload_result = self.upload_pdf(
                file_path=file_path,
                display_name=display_name,
                user_id=user_id,
                bucket_name=bucket_name,
            )

            file_path_in_bucket = upload_result["file_name"]

            full_text, meta = self.download_pdf_and_extract_text(
                file_path=file_path_in_bucket,
                bucket_name=bucket_name,
                expire_seconds=3600,
                save_temp=False,
            )

            update_payload = {
                "status": "processado",
                "full_text": full_text,
                "processed_at": meta.get("downloaded_at"),
            }

            self.supabase_admin.table("pdf_uploads").update(update_payload).eq(
                "file_path", file_path_in_bucket
            ).execute()

            return {
                **upload_result,
                "processing": {
                    "text_extraction": "sucesso",
                    "pages": meta.get("pages", 0),
                    "embedding_generation": "pendente",
                },
            }

        except Exception as e:
            print(f"[ERROR] Erro no upload + extração: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro no upload + extração: {str(e)}",
            )
