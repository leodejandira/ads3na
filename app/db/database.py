import os
import os
from dotenv import load_dotenv
from supabase import Client, create_client


url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")


def get_client() -> Client:
    supabase: Client = create_client(url, key)
    print("✅ Conexão com o Supabase estabelecida com sucesso!")
    return supabase


def print_db():
    supabase = get_client()
    response = supabase.table("users").select("*").limit(10).execute()

    print("\n📌 Registros da tabela:")
    registros = response.data

    if len(registros) > 0:
        for registro in registros:
            print(registro)
    else:
        print("⚠️ Nenhum registro encontrado na tabela.")


if __name__ == "__main__":
    print_db()

