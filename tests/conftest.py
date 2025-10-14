# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.db.database import get_client # O caminho para a sua dependência

@pytest.fixture
def mock_db_client():
    """
    Fixture que cria um "banco de dados falso" (um MagicMock) para cada teste.

    Este é o nosso "ator": um objeto em branco que se parece com o cliente do Supabase.
    Cada teste será responsável por ensinar a este ator como ele deve se comportar.
    """
    # 1. Cria o mock principal que simula o objeto 'supabase_client'
    mock_client = MagicMock()

    # 2. Prepara a cadeia de chamadas que seu código usa: table(...).select(...).execute()
    #    A chamada final a .execute() retorna um objeto de resposta simulado.
    mock_response_object = MagicMock()
    mock_client.table.return_value.select.return_value.execute.return_value = mock_response_object

    # 3. Retorna o cliente mockado. O teste que o usar poderá configurar
    #    o `mock_response_object` como quiser (ex: definindo .data ou .error).
    return mock_client

@pytest.fixture
def api_client(mock_db_client):
    """
    Fixture principal para os testes de endpoint. Ela faz três coisas essenciais:

    1.  SETUP: Substitui a dependência `get_client` real pelo nosso banco de dados falso.
    2.  EXECUÇÃO: Fornece um `TestClient` para fazer requisições à API.
    3.  TEARDOWN: Limpa a substituição após o teste, garantindo que os testes não interfiram uns nos outros.
    """
    # SETUP: Diz ao FastAPI para usar nosso mock em vez da função real
    app.dependency_overrides[get_client] = lambda: mock_db_client
    
    # EXECUÇÃO: Cria e fornece o cliente para o teste
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()