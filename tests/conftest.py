# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock # Usaremos um mock mais poderoso

# Importe sua aplicação FastAPI e a dependência que vamos substituir
from app.main import app
from app.db.database import get_client

# Crie um mock reutilizável para o cliente do Supabase
mock_supabase_client = MagicMock()

# Função que retorna nosso mock em vez do cliente real
def get_supabase_client_override():
    return mock_supabase_client

# Substitui a dependência real pela nossa versão de teste
app.dependency_overrides[get_client] = get_supabase_client_override

@pytest.fixture
def client(mocker):
    """
    Fixture que fornece um TestClient para fazer requisições à API.
    Ela também reseta os mocks antes de cada teste.
    """
    # Reseta o estado do mock antes de cada teste para que eles sejam independentes
    mocker.resetall()
    
    with TestClient(app) as test_client:
        yield test_client