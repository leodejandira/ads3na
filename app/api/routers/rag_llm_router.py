import os
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.templating import Jinja2Templates

from app.services.auth_service import get_current_user
from app.services.rag_llm_service import generate_embedding_for_pdf, query_rag_system, process_pdf_embeddings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

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

    return process_pdf_embeddings(file_name)

@router.post("/pdfs/embed")
async def embed_pdf_route(
    body: dict = Body(...), user: dict = Depends(get_current_user)
):
    """
    Gera embeddings para um PDF processado.
    Recebe JSON: { "file_name": "exemplo.pdf" }
    """
    if user.get("role") != "gerente":
        raise HTTPException(
            status_code=403, detail="Apenas gerentes podem gerar embeddings."
        )

    file_name = body.get("file_name")
    if not file_name:
        raise HTTPException(
            status_code=400, detail="Campo 'file_name' é obrigatório no corpo JSON."
        )

    print(f"[DEBUG] Iniciando embeddings para '{file_name}' pelo usuário {user['email']}")
    result = generate_embedding_for_pdf(file_name)
    return result

@router.post("/pdfs/query")
async def query_pdf_route(
    body: dict = Body(...), user: dict = Depends(get_current_user)
):
    """
    Rota para realizar consultas RAG com base nos PDFs vetorizados.
    - Recebe o JSON: { "query": "texto da pergunta" }
    """
    # 🔒 Validação de permissão - AGORA PERMITE GERENTES E USUÁRIOS
    if user.get("role") not in ["gerente", "usuario"]:
        raise HTTPException(
            status_code=403, detail="Somente usuários autenticados podem consultar PDFs."
        )

    # 🔹 Captura e valida o campo da query
    query = body.get("query")
    if not query:
        raise HTTPException(
            status_code=400, detail="Campo 'query' é obrigatório no corpo JSON."
        )

    return query_rag_system(query)