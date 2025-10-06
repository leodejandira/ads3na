import os

from dotenv import load_dotenv
from supabase import Client, create_client

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
