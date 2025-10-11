import jwt
from api.schema.registros import RegistroCreate
from api.services.auth_service import login
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.api.services.register_service import inserir_registro

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@router.post("/register")
def register_route(novo_usuario: RegistroCreate):
    """
    Registra um novo usuário.

    Parâmetro de entrada: objeto RegistroCreate contendo
    name, email, senha e role.

    Raises:
        HTTPException:
            - 400: Se os dados fornecidos forem inválidos ou ja existirem.
            - 500: Se ocorrer um erro inesperado no processo de registro.

    Retorno: Objeto Registro criado
    """
    try:
        return inserir_registro(novo_usuario)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao registrar o usuário."
        )


@router.post("/login")
def login_route(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    função responsável por autenticar um usuário no sistema.

    Valida as credenciais (e-mail e senha) e retorna um token JWT
    em caso de sucesso. Caso as credenciais sejam inválidas ou o
    usuário esteja inativo, uma exceção HTTP sera lançada.

    Parametros:
        form_data(OAuth2PasswordRequestForm): Objeto contendo os dados do login
            - username: o e-mail do usuário.
            - password: a senha em texto plano.

    Raises:
        HTTPException:
            - 401: Credenciais inválidas
            - 403: Usuário inativo
            - 500: Erro inesperado durante o login

    Retorno:
        dict: Um dicionário contendo o token de acesso e o tipo do token.
            {
                "acess_token": "<token_jwt>",
                "token_type": "bearer"
            }
    """
    try:
        token = login(form_data.username, form_data.password)
        return {"access_token": token, "token_type": "bearer"}

    except HTTPException as http_err:
        raise http_err

    except Exception:
        raise HTTPException(status_code=500,
                            detail="Erro interno ao realizar login.")


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodifica o token JWT e retorna os dados do usuário atual.

    Parametros:
        token (str): Token JWT extraído do cabeçalho Authorization.

    Raises:
        HTTPException:
            -401: Se o token estiver expirado ou for invalido.

    Retorno:
        dict: Payload decodificado do token JWT,
        contendo informações do usuário.
    """
    try:
        payload = jwt.decode(
            token, "sua_chave_super_secreta",
            algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.get("/rota-gerente")
def rota_gerente(user: dict = Depends(get_current_user)):
    """
    Endpoint acessível apenas por usuários com o papel "gerente"

    Parametros:
        user (dict): Dados do usuário extraidos do token JWT.

    Raises:
        HTTPException:
            - 403: Se o usuário não for gerente.

    Retorno:
        dict: Mensagem de boas-vindas personalizada para o gerente.
    """
    if user["role"] != "gerente":
        raise HTTPException(status_code=403,
                            detail="Apenas gerentes podem acessar")
    return {"msg": f"Bem-vindo gerente {user['email']}"}


@router.get("/rota-usuario")
def rota_usuario(user: dict = Depends(get_current_user)):
    """
    Endpoint acessivel apenas por usuários com o papel "usuario".

    Parametros:
        user (dict): Dados do usuário extraidos do token JWT.

    Raises:
        HTTPException:
            - 403: Se o usuário não for usuário comum.

    Retorno:
        dict: Mensagem de boas-vindas personalizada para o usuário.
    """
    if user["role"] != "usuario":
        raise HTTPException(status_code=403,
                            detail="Apenas usuários podem acessar")
    return {"msg": f"Bem-vindo usuário {user['email']}"}
