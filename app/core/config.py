import os

from dotenv import load_dotenv
from supabase import Client, create_client

"""
Demonstração de autenticação no Supabase.

Este script inicializa o cliente Supabase usando variáveis de ambiente e
executa dois métodos principais de autenticação: login (sign_in_with_password)
e cadastro (sign_up). Ele também extrai e exibe o Token JWT da sessão de login.
"""

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

auth_response = supabase.auth.sign_in_with_password(
    {"email": "frank.miranda12@hotmail.com", "password": "host8899"}
)

print(auth_response)

signup_response = supabase.auth.sign_up(
    {"email": "novo@exemplo.com", "password": "senha123"}
)

print(signup_response)

session = auth_response.session
access_token = session.access_token

print("Token JWT:", access_token)
