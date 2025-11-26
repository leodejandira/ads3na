import os
from datetime import datetime

from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from supabase import create_client

from app.core.config import EMBEDDING_MODEL_NAME, embedding_model

import json
import os
import numpy as np
from openai import OpenAI
from supabase import create_client
from fastapi import HTTPException


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


def query_rag_system(query: str):
    """
    Executa toda a lógica RAG: embedding da pergunta, busca de similares, e geração de resposta.
    """
    print(f"[DEBUG] Iniciando consulta RAG para: {query}")

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # 1. Gera embedding da pergunta
    try:
        query_embedding = embedding_model.encode([query])[0].tolist()
        print(f"[DEBUG] Embedding da pergunta gerado com sucesso usando {EMBEDDING_MODEL_NAME}.")
    except Exception as e:
        print(f"[ERROR] Erro ao gerar embedding da consulta: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar embedding da pergunta.")

    # 2. Busca todos os vetores no banco
    try:
        vectors_res = (
            supabase_admin.table("pdf_vectors")
            .select("pdf_id, chunk_text, embedding")
            .execute()
        )
        all_vectors = vectors_res.data
        if not all_vectors:
            raise HTTPException(status_code=404, detail="Nenhum vetor encontrado.")
        print(f"[DEBUG] {len(all_vectors)} vetores carregados do banco.")
    except Exception as e:
        print(f"[ERROR] Erro ao buscar vetores: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar vetores: {str(e)}")

    # 3. Calcula similaridade entre a pergunta e os embeddings
    try:
        similarities = []
        for v in all_vectors:
            emb_data = v["embedding"]
            if isinstance(emb_data, str):
                emb_data = json.loads(emb_data)
            emb = np.array(emb_data, dtype=float)
            sim = np.dot(emb, query_embedding) / (
                np.linalg.norm(emb) * np.linalg.norm(query_embedding)
            )
            similarities.append((sim, v["chunk_text"]))

        similarities.sort(reverse=True, key=lambda x: x[0])
        top_matches = similarities[:5]  # top 5 trechos mais similares
        print(f"[DEBUG] {len(top_matches)} trechos mais similares selecionados.")
    except Exception as e:
        print(f"[ERROR] Erro ao calcular similaridades: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao calcular similaridades: {str(e)}")

    # 4. Monta o contexto consolidado
    context = "\n\n".join([t[1] for t in top_matches])

    prompt = f"""
Você é um assistente inteligente que responde
perguntas com base no contexto abaixo.
Use somente as informações fornecidas.
Se a resposta não estiver presente, diga:
"Não encontrei informações suficientes para responder."

Contexto:
{context}

Pergunta:
{query}
    """

    # 5. Configurações do modelo OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not OPENAI_API_KEY:
        print("[WARN] Nenhuma OPENAI_API_KEY configurada. Retornando apenas o prompt.")
        return {
            "query": query,
            "matches_used": len(top_matches),
            "response": "Chave da OpenAI não configurada — retornando somente o contexto.",
            "model": None,
        }

    try:
        # garante que a variável esteja no ambiente
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

        # instancia o client sem parâmetros
        client = OpenAI()

        print(f"[DEBUG] Cliente OpenAI inicializado. Usando modelo {OPENAI_MODEL}.")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente que responde com base em informações contextuais.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content.strip()
        print(f"[DEBUG] Resposta gerada com sucesso pelo modelo {OPENAI_MODEL}.")

    except Exception as e:
        print(f"[ERROR] Erro ao consultar OpenAI: {str(e)}")
        answer = (
            "✅ Consulta realizada com sucesso! Foram encontrados "
            f"{len(top_matches)} trechos relevantes nos PDFs. "
            "Resposta do modelo GPT temporariamente indisponível - "
            "aqui estão os trechos encontrados: "
            f"{' | '.join([t[1][:100] + '...' for t in top_matches])}"
        )

    # Retorno final da resposta RAG
    return {
        "query": query,
        "matches_used": len(top_matches),
        "response": answer,
        "model": OPENAI_MODEL,
    }


def process_pdf_embeddings(file_name: str):
    """
    Processa um PDF para gerar embeddings e atualizar status.
    """
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
        raise HTTPException(status_code=500, detail=f"Erro ao vetorizar PDF: {str(e)}")