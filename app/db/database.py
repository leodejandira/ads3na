import os

<<<<<<< HEAD
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

=======
from supabase import Client, create_client

>>>>>>> 57810807baa72815a6446bddd8cafcab8d7bcac8
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")


def get_client() -> Client:
<<<<<<< HEAD
    """
    Retorna o cliente Supabase configurado com as variáveis de ambiente.
    """
=======
>>>>>>> 57810807baa72815a6446bddd8cafcab8d7bcac8
    supabase: Client = create_client(url, key)
    print("✅ Conexão com o Supabase estabelecida com sucesso!")
    return supabase


def print_db():
<<<<<<< HEAD
    """
    Exibe os 10 primeiros registros da tabela 'users' para verificação.
    """
=======
>>>>>>> 57810807baa72815a6446bddd8cafcab8d7bcac8
    supabase = get_client()
    response = supabase.table("users").select("*").limit(10).execute()

    print("\n📌 Registros da tabela:")
    registros = response.data

<<<<<<< HEAD
    if registros:
=======
    if len(registros) > 0:
>>>>>>> 57810807baa72815a6446bddd8cafcab8d7bcac8
        for registro in registros:
            print(registro)
    else:
        print("⚠️ Nenhum registro encontrado na tabela.")


if __name__ == "__main__":
    print_db()
