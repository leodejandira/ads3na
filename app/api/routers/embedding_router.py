import json
import os

import jwt
import numpy as np
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from supabase import create_client

from app.core.config import EMBEDDING_MODEL_NAME, embedding_model
from app.services.embedding_service import generate_embedding_for_pdf
from app.services.auth_service import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")



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

    print(
        "[DEBUG] Iniciando embeddings para "
        f"'{file_name}' pelo usuário {user['email']}"
    )
    result = generate_embedding_for_pdf(file_name)
    return result


@router.post("/pdfs/query")
async def query_pdf_route(
    body: dict = Body(...), user: dict = Depends(get_current_user)
):
    """
    Rota para realizar consultas RAG com base nos PDFs vetorizados.
    - Recebe o JSON: { "query": "texto da pergunta" }
    - Gera embedding da pergunta
    - Busca embeddings mais similares no Supabase
    - Monta prompt com contexto
    - Chama o modelo GPT configurado (OpenAI)
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

    print(f"[DEBUG] Iniciando consulta RAG para: {query}")

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    #  Gera embedding da pergunta
    try:
        query_embedding = embedding_model.encode([query])[0].tolist()
        print(
            "[DEBUG] Embedding da pergunta gerado "
            f"com sucesso usando {EMBEDDING_MODEL_NAME}."
        )
    except Exception as e:
        print(f"[ERROR] Erro ao gerar embedding da consulta: {e}")
        raise HTTPException(
            status_code=500, detail="Erro ao gerar embedding da pergunta."
        )

    #  Busca todos os vetores no banco
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

    #  Calcula similaridade entre a pergunta e os embeddings
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
        print(f"[DEBUG] {len(top_matches)} trechos mais " "similares selecionados.")
    except Exception as e:
        print(f"[ERROR] Erro ao calcular similaridades: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao calcular similaridades: {str(e)}"
        )

    # Monta o contexto consolidado
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

    # Configurações do modelo OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not OPENAI_API_KEY:
        print(
            "[WARN] Nenhuma OPENAI_API_KEY configurada. " "Retornando apenas o prompt."
        )
        return {
            "query": query,
            "matches_used": len(top_matches),
            "response": "Chave da OpenAI não configurada — "
            "retornando somente o contexto.",
            "model": None,
        }

    try:
        # garante que a variável esteja no ambiente
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

        # instancia o client sem parâmetros
        client = OpenAI()

        print("[DEBUG] Cliente OpenAI inicializado. " f"Usando modelo {OPENAI_MODEL}.")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente que "
                    "responde com base em informações contextuais.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content.strip()
        print("[DEBUG] Resposta gerada com sucesso " f"pelo modelo {OPENAI_MODEL}.")

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
