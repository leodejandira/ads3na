import os
import tempfile
from typing import List
from uuid import UUID
import json
import jwt
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Request
from fastapi.templating import Jinja2Templates
from supabase import create_client

from app.db.database import get_client
from app.api.schema.registros import Registro, RegistroCreate
from app.services.auth_service import login
from app.services.register_service import (atualizar_registro, buscar_registro,
                                           deletar_registro, inserir_registro,
                                           listar_registros)
from app.services.pdfs import upload_pdf as upload_pdf_service
from datetime import datetime
from app.services.pdfs import download_pdf_and_extract_text
from app.services.pdfs import generate_embedding_for_pdf
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from fastapi import Body
from app.core.config import embedding_model, EMBEDDING_MODEL_NAME


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
templates = Jinja2Templates(directory="templates")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodifica o token JWT e retorna os dados do usuário atual.

    Raises:
        HTTPException:
            - 401: Se o token estiver expirado ou for inválido.

    Retorno:
        dict: Payload decodificado do token JWT.
    """
    try:
        payload = jwt.decode(
            token,
            "sua_chave_super_secreta",
            algorithms=["HS256"],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/register", response_model=Registro)
def register_route(novo_usuario: RegistroCreate, user: dict = Depends(get_current_user)):
    """
    Registra um novo usuário. Apenas gerentes podem registrar novos usuários.

    Parâmetro de entrada: objeto RegistroCreate contendo
    name, email, senha e role.

    Raises:
        HTTPException:
            - 400: Se os dados fornecidos forem inválidos ou já existirem.
            - 403: Apenas gerentes podem registrar usuários.
            - 500: Se ocorrer um erro inesperado no processo de registro.

    Retorno: Objeto Registro criado.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem registrar novos usuários.",
        )
    return inserir_registro(novo_usuario)


@router.post("/login")
def login_route(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Autentica um usuário no sistema.

    Valida as credenciais e retorna um token JWT em caso de sucesso.

    Raises:
        HTTPException:
            - 401: Credenciais inválidas.
            - 403: Usuário inativo.
            - 500: Erro inesperado durante o login.

    Retorno:
        dict: Contém o token de acesso e o tipo do token.
    """
    try:
        token = login(form_data.username, form_data.password)
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException as http_err:
        raise http_err
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao realizar login.",
        )


@router.get("/rota-gerente")
def rota_gerente(user: dict = Depends(get_current_user)):
    """
    Endpoint acessível apenas por usuários com o papel 'gerente'.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem acessar.",
        )
    return {"msg": f"Bem-vindo gerente {user['email']}"}


@router.get("/rota-usuario")
def rota_usuario(user: dict = Depends(get_current_user)):
    """
    Endpoint acessível apenas por usuários com o papel 'usuario'.
    """
    if user["role"] != "usuario":
        raise HTTPException(
            status_code=403,
            detail="Apenas usuários podem acessar.",
        )
    return {"msg": f"Bem-vindo usuário {user['email']}"}


@router.get("/usuarios", response_model=List[Registro], tags=["Autenticação"])
def listar_usuarios_route(user: dict = Depends(get_current_user)):
    """
    Lista todos os usuários registrados. Apenas gerentes podem listar usuários.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem listar usuários.",
        )
    try:
        return listar_registros()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/usuarios/{registro_id}",
    response_model=Registro,
    tags=["Autenticação"],
)
def buscar_usuario_route(registro_id: int, user: dict = Depends(get_current_user)):
    """
    Retorna um usuário específico pelo ID. Apenas gerentes podem buscar usuários.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem buscar usuários.",
        )
    try:
        usuario = buscar_registro(registro_id)
        if not usuario:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado.",
            )
        return usuario
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao buscar usuário.",
        )


@router.put(
    "/usuarios/{registro_id}",
    response_model=Registro,
    tags=["Autenticação"],
)
def atualizar_usuario_route(registro_id: int, name: str, email: str, user: dict = Depends(get_current_user)):
    """
    Atualiza os dados de um usuário existente pelo ID. Apenas gerentes podem atualizar usuários.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem atualizar usuários.",
        )
    try:
        return atualizar_registro(registro_id, name, email)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar usuário.",
        )


@router.delete(
    "/usuarios/{registro_id}",
    response_model=Registro,
    tags=["Autenticação"],
)
def deletar_usuario_route(registro_id: int, user: dict = Depends(get_current_user)):
    """
    Deleta um usuário existente pelo ID. Apenas gerentes podem deletar usuários.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem deletar usuários.",
        )
    try:
        return deletar_registro(registro_id)
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro ao deletar usuário.",
        )


@router.get("/upload")
def upload_page(request: Request, user: dict = Depends(get_current_user)):
    """
    Serve a página de upload para gerentes.
    """
    if user["role"] != "gerente":
        raise HTTPException(
            status_code=403,
            detail="Apenas gerentes podem acessar esta página.",
        )
    return templates.TemplateResponse("upload.html", {"request": request})


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

        file_display_name = file.filename if file.filename else "arquivo_sem_nome.pdf"

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
        print(f"[DEBUG] Iniciando processamento automático do PDF: {file_display_name}")
        
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
            raise HTTPException(status_code=404, detail="PDF não encontrado após upload.")

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
        print(f"[DEBUG] Iniciando geração de embeddings...")
        embed_result = generate_embedding_for_pdf(file_display_name)
        print(f"[DEBUG] Embeddings gerados: {embed_result}")

        return {
            **result,
            "processing": {
                "text_extraction": "sucesso",
                "embedding_generation": "sucesso", 
                "chunks_processed": embed_result.get("chunks", 0),
                "pages": meta.get("pages", 0),
                "model_used": embed_result.get("model")
            }
        }

    except HTTPException as http_e:
        # Limpa arquivo temporário em caso de erro
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise http_e
    except Exception as e:
        # Limpa arquivo temporário em caso de erro
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
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
        raise HTTPException(status_code=403, detail="Apenas gerentes podem deletar PDFs.")

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
        raise HTTPException(status_code=400, detail="Campo 'file_name' é obrigatório no corpo JSON.")

    print(f"[DEBUG] Iniciando processamento do PDF: {file_name} pelo usuário {user['email']}")

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

        print(f"[DEBUG] Registro encontrado: id={pdf_data.get('id')} file_path={file_path}")

    except Exception as e:
        print(f"[ERROR] Erro ao consultar pdf_uploads: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar registro: {str(e)}")

    try:
        full_text, meta = download_pdf_and_extract_text(
            file_path=file_path,
            bucket_name="pdfs",
            expire_seconds=3600,
            save_temp=False,
        )
        print(f"[DEBUG] Extração concluída: {meta.get('pages')} páginas, {meta.get('bytes')} bytes")
    except Exception as e:
        print(f"[ERROR] Erro na extração do PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao extrair texto do PDF: {str(e)}")

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

        print(f"[DEBUG] Registro atualizado (id={pdf_data.get('id')}, status=processado).")

    except Exception as e:
        print(f"[ERROR] Erro ao atualizar registro no banco: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar registro: {str(e)}")

    return {
        "message": f"PDF '{file_name}' processado com sucesso.",
        "metadata": meta,
        "text_preview": full_text[:800] + "..." if len(full_text) > 800 else full_text,
    }

@router.post("/pdfs/embed")
async def embed_pdf_route(
    body: dict = Body(...),
    user: dict = Depends(get_current_user)
):
    """
    Gera embeddings para um PDF processado.
    Recebe JSON: { "file_name": "exemplo.pdf" }
    """
    if user.get("role") != "gerente":
        raise HTTPException(status_code=403, detail="Apenas gerentes podem gerar embeddings.")

    file_name = body.get("file_name")
    if not file_name:
        raise HTTPException(status_code=400, detail="Campo 'file_name' é obrigatório no corpo JSON.")

    print(f"[DEBUG] Iniciando embeddings para '{file_name}' pelo usuário {user['email']}")
    result = generate_embedding_for_pdf(file_name)
    return result


@router.post("/pdfs/query")
async def query_pdf_route(
    body: dict = Body(...),
    # user: dict = Depends(get_current_user)
):
    """
    Rota para realizar consultas RAG com base nos PDFs vetorizados.
    - Recebe o JSON: { "query": "texto da pergunta" }
    - Gera embedding da pergunta
    - Busca embeddings mais similares no Supabase
    - Monta prompt com contexto
    - Chama o modelo GPT configurado (OpenAI)
    """

    # 🔒 Validação de permissão
    # if user.get("role") != "gerente":
    #     raise HTTPException(status_code=403, detail="Somente gerentes podem consultar PDFs.")

    # 🔹 Captura e valida o campo da query
    query = body.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Campo 'query' é obrigatório no corpo JSON.")

    print(f"[DEBUG] Iniciando consulta RAG para: {query}")

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_KEY_ROLE")
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # 🔹 Gera embedding da pergunta
    try:
        query_embedding = embedding_model.encode([query])[0].tolist()
        print(f"[DEBUG] Embedding da pergunta gerado com sucesso usando {EMBEDDING_MODEL_NAME}.")
    except Exception as e:
        print(f"[ERROR] Erro ao gerar embedding da consulta: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar embedding da pergunta.")

    # 🔹 Busca todos os vetores no banco
    try:
        vectors_res = supabase_admin.table("pdf_vectors").select("pdf_id, chunk_text, embedding").execute()
        all_vectors = vectors_res.data
        if not all_vectors:
            raise HTTPException(status_code=404, detail="Nenhum vetor encontrado.")
        print(f"[DEBUG] {len(all_vectors)} vetores carregados do banco.")
    except Exception as e:
        print(f"[ERROR] Erro ao buscar vetores: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar vetores: {str(e)}")

    # 🔹 Calcula similaridade entre a pergunta e os embeddings
    try:
        similarities = []
        for v in all_vectors:
            emb_data = v["embedding"]
            if isinstance(emb_data, str):
                emb_data = json.loads(emb_data)
            emb = np.array(emb_data, dtype=float)
            sim = np.dot(emb, query_embedding) / (np.linalg.norm(emb) * np.linalg.norm(query_embedding))
            similarities.append((sim, v["chunk_text"]))

        similarities.sort(reverse=True, key=lambda x: x[0])
        top_matches = similarities[:5]  # top 5 trechos mais similares
        print(f"[DEBUG] {len(top_matches)} trechos mais similares selecionados.")
    except Exception as e:
        print(f"[ERROR] Erro ao calcular similaridades: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao calcular similaridades: {str(e)}")

    # 🔹 Monta o contexto consolidado
    context = "\n\n".join([t[1] for t in top_matches])

    prompt = f"""
Você é um assistente inteligente que responde perguntas com base no contexto abaixo.
Use somente as informações fornecidas.
Se a resposta não estiver presente, diga: "Não encontrei informações suficientes para responder."

Contexto:
{context}

Pergunta:
{query}
    """

    # 🔹 Configurações do modelo OpenAI
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

    # 🔹 Cliente OpenAI (forma correta com SDK 1.51.0)
    try:
        # garante que a variável esteja no ambiente
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

        # instancia o client sem parâmetros
        client = OpenAI()

        print(f"[DEBUG] Cliente OpenAI inicializado. Usando modelo {OPENAI_MODEL}.")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente que responde com base em informações contextuais."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=1000
        )

        answer = response.choices[0].message.content.strip()
        print(f"[DEBUG] Resposta gerada com sucesso pelo modelo {OPENAI_MODEL}.")

    except Exception as e:
        print(f"[ERROR] Erro ao consultar OpenAI: {str(e)}")
        answer = (
            f"✅ Consulta realizada com sucesso! Foram encontrados {len(top_matches)} trechos relevantes nos PDFs. "
            f"Resposta do modelo GPT temporariamente indisponível - aqui estão os trechos encontrados: "
            f"{' | '.join([t[1][:100] + '...' for t in top_matches])}"
        )

    # 🔹 Retorno final da resposta RAG
    return {
        "query": query,
        "matches_used": len(top_matches),
        "response": answer,
        "model": OPENAI_MODEL,
    }