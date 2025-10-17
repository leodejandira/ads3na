import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")


def get_client() -> Client:
    """
    Retorna o cliente Supabase configurado com as variáveis de ambiente.
    """
    supabase: Client = create_client(url, key)
    print("✅ Conexão com o Supabase estabelecida com sucesso!")
    return supabase


def print_db():
    """
    Exibe os 10 primeiros registros da tabela 'users' para verificação.
    """
    supabase = get_client()
    response = supabase.table("users").select("*").limit(10).execute()

    print("\n📌 Registros da tabela:")
    registros = response.data

    if registros:
        for registro in registros:
            print(registro)
    else:
        print("⚠️ Nenhum registro encontrado na tabela.")


if __name__ == "__main__":
    print_db()
