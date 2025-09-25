import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

def get_client() -> Client:
    '''
    '''
    supabase: Client = create_client(url, key)
    print("✅ Conexão com o Supabase estabelecida com sucesso!")
    return supabase

def print_tabelinha():
    supabase = get_client()
    
    # Buscar todos os registros da tabela 'tabelinha'
    # Adicionando a linha '.limit(10)' para garantir que ele busque algo
    response = supabase.table("tabelinha").select("*").limit(10).execute()
    
    print("\n📌 Registros na tabela 'tabelinha':")
    
    # Acessa a lista de dados
    registros = response.data
    
    # Verifica se a lista de registros não está vazia
    if len(registros) > 0:
        for registro in registros:
            print(registro)
    else:
        print("⚠️ Nenhum registro encontrado na tabela.")

if __name__ == "__main__":
    print_tabelinha()