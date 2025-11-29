import os
import json
import numpy as np
from datetime import datetime
from fastapi import HTTPException
from supabase import create_client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from app.core.config import EMBEDDING_MODEL_NAME, embedding_model


class RagLLMService:
    def __init__(self):
        """
        Inicializa variáveis básicas e evita repetir o código.
        """
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY_ROLE")
        self.supabase_admin = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)


    def generate_embedding_for_pdf(self, file_name: str):
        print(f"[DEBUG] Iniciando geração de embeddings para: {file_name}")

        record = (
            self.supabase_admin.table("pdf_uploads")
            .select("id, full_text, status")
            .eq("file_name", file_name)
            .single()
            .execute()
        )

        pdf_data = record.data

        if pdf_data.get("full_text"):
            text = pdf_data["full_text"]
            print("[DEBUG] Texto carregado do banco.")

        else:
            raise HTTPException(status_code=400, detail="Texto não encontrado no banco.")
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_text(text)
        print(f"[DEBUG] Texto dividido em {len(chunks)} chunks.")

        try:
            embeddings = embedding_model.encode(chunks, show_progress_bar=True)
            print(f"[DEBUG] {len(embeddings)} embeddings gerados com sucesso.")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar embeddings: {str(e)}",
            )
        
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

        self.supabase_admin.table("pdf_vectors").insert(rows).execute()
        print(f"[DEBUG] {len(rows)} vetores inseridos no banco.")

        self.supabase_admin.table("pdf_uploads").update(
            {"status": "vetorizado", "processed_at": datetime.utcnow().isoformat()}
        ).eq("id", pdf_data["id"]).execute()

        return {
            "message": f"Embeddings gerados com sucesso para '{file_name}'.",
            "chunks": len(chunks),
            "model": EMBEDDING_MODEL_NAME,
        }
    
    def query_rag_system(self, query: str):
        print (f"[DEBUG] Iniciando consulta RAG para: {query}")

        try:
            query_embedding = embedding_model.encode([query])[0].tolist()
            print(f"[DEBUG] Embedding da pergunta gerado com sucesso usando {EMBEDDING_MODEL_NAME}.")
        except Exception as e:
            print(f"[ERROR] Erro ao gerar embedding da pergunta: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar embedding da pergunta: {str(e)}",
            )
        
        try:
            vectors_res = (
                self.supabase_admin.table("pdf_vectors")
                .select("pdf_id, chunk_text, embedding")
                .execute()
            )
            all_vectors = vectors_res.data
            if not all_vectors:
                raise HTTPException(
                    status_code=404,
                    detail="Nenhum vetor encontrado no banco de dados.",
                )
            print(f"[DEBUG] {len(all_vectors)} vetores carregados do banco.")

        except Exception as e:
            print(f"[ERROR] Erro ao buscar vetores: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar vetores: {str(e)}",
            )
        
        try:
            similarities = []
            for v in all_vectors:
                emb_data = v["embedding"]
                if isinstance(emb_data, str):
                    try:
                        emb_list = json.loads(emb_data)
                    except:
                        emb_list = json.loads(emb_data.replace("'", '"'))
                else:
                    emb_list = emb_data

                emb = np.array(emb_list, dtype=float)
                sim = np.dot(emb, query_embedding) / (
                    np.linalg.norm(emb) * np.linalg.norm(query_embedding)
                )
                similarities.append((sim, v["chunk_text"]))
            similarities.sort(reverse=True, key=lambda x: x[0])
            top_matches = similarities[:5]

            print(f"[DEBUG] {len(top_matches)} chunks mais similares selecionados.")
        
        except Exception as e:
            print(f"[ERROR] Erro ao calcular similaridades: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao calcular similaridades: {str(e)}",
            )
        
        context = "\n\n".join([t[1] for t in top_matches])

        prompt = f"""
Você é um assistente inteligente que response
perguntas com base no contexto abaixo.
Use somente as informações fornecidas.
Se a resposta não estiver presente, diga:
"Não encontrei informações suficientes para responder."

Contexto:
{context}

Pergunta:
{query}
"""
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if not OPENAI_API_KEY:
            print("[WARN] OPENAI key ausente")
            return {
                "query": query,
                "matches_used": len(top_matches),
                "response": "Chave da OpenAI não configurada — retornando somente o contexto.",
                "model": None,
            }
        
        try:
            os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
            client = OpenAI()
            print(f"[DEBUG] Usando modelo {OPENAI_MODEL}")

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um assistente que responde com base em informações contextuais."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=1000,
            )

            answer = response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[ERROR] Erro ao consultar OpenAI: {e}")
            answer = (
                "Consulta realizada! Porém houve um erro ao chamar o GPT. "
                f"Aqui estão os trechos encontrados: {', '.join([t[1][:100] + '...' for t in top_matches])}"
            )

        return {
            "query": query,
            "matches_used": len(top_matches),
            "response": answer,
            "model": OPENAI_MODEL,
        }

    def process_pdf_embeddings(self, file_name: str):
        print(f"[DEBUG] Processando PDF para embeddings: {file_name}")

        try:
            embed_result = self.generate_embedding_for_pdf(file_name)

            update_res = (
                self.supabase_admin.table("pdf_uploads")
                .update({"status": "vetorizado"})
                .eq("file_name", file_name)
                .execute()
            )

            print(f"[DEBUG] Status atualizado: {update_res}")

            return {
                "message": f"PDF '{file_name}' vetorizado com sucesso!",
                "chunks_processed": embed_result.get("chunks", 0),
                "model_used": embed_result.get("model"),
            }
        
        except HTTPException as e:
            print(f"[ERROR] Erro na vetorização PDF: {e}")
            raise HTTPException(status_code=500,
                                detail=f"Erro ao vetorizar PDF: {str(e)}")
            
