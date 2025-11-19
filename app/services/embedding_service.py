import os
from datetime import datetime

from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from supabase import create_client

from app.core.config import EMBEDDING_MODEL_NAME, embedding_model


def generate_embedding_for_pdf(file_name: str):
    """
    Gera embeddings otimizados para um PDF.
    Agora:
    - Usa texto salvo no banco (não baixa PDF)
    - Reutiliza o modelo global
    - Salva vetores com pgvector
    """
    print(f"[DEBUG] Iniciando geração de embeddings para: {file_name}")

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY_ROLE")
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. Busca o PDF no banco
    record = (
        supabase_admin.table("pdf_uploads")
        .select("id, full_text, status")
        .eq("file_name", file_name)
        .single()
        .execute()
    )

    if not record.data:
        raise HTTPException(status_code=404, detail="PDF não encontrado.")

    pdf_data = record.data

    # 2. Pega o texto , espero que não de erro
    if pdf_data.get("full_text"):
        text = pdf_data["full_text"]
        print("[DEBUG] Texto carregado do banco.")
    else:
        raise HTTPException(status_code=400, detail="Texto não encontrado no banco.")

    # 3. Divide em chunks

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    print(f"[DEBUG] Texto dividido em {len(chunks)} chunks.")

    # 4. Gera embeddings (reutiliza o modelo global)
    try:
        embeddings = embedding_model.encode(chunks, show_progress_bar=True)
        print(f"[DEBUG] {len(embeddings)} embeddings gerados com sucesso.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar embeddings: {e}")

    # 5. Insere vetores no banco (pgvector)
    rows = [
        {
            "pdf_id": pdf_data["id"],
            "chunk_index": i,
            "chunk_text": chunk,
            "embedding": emb.tolist(),
            "embedding_model_used": EMBEDDING_MODEL_NAME,
            "created_at": datetime.utcnow().isoformat(),
        }
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]

    supabase_admin.table("pdf_vectors").insert(rows).execute()
    print(f"[DEBUG] {len(rows)} vetores inseridos no banco.")

    # 6. Atualiza status
    supabase_admin.table("pdf_uploads").update(
        {"status": "vetorizado", "processed_at": datetime.utcnow().isoformat()}
    ).eq("id", pdf_data["id"]).execute()

    return {
        "message": f"Embeddings gerados com sucesso para '{file_name}'.",
        "chunks": len(chunks),
        "model": EMBEDDING_MODEL_NAME,
    }
