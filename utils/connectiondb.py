from supabase import create_client, Client

url: str = "https://hdgcquzcfbbwqufznatb.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkZ2NxdXpjZmJid3F1ZnpuYXRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MjY2NDMsImV4cCI6MjA3NDIwMjY0M30.7r9RNPhoGT4UJdolJFsDmaftbApKTg61DKgOcchkRWY"
supabase: Client = create_client(url, key)

# login do usuário
auth_response = supabase.auth.sign_in_with_password({
    "email": "frank.miranda12@hotmail.com",
    "password": "host8899"
})

print(auth_response)

#registrando usuario novo
signup_response = supabase.auth.sign_up({
    "email": "novo@exemplo.com",
    "password": "senha123"
})

print(signup_response)

#token para acessar tabelas protegidas
session = auth_response.session
access_token = session.access_token

print("Token JWT:", access_token)