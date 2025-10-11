# tests/test_endpoints.py

# A fixture 'client' vem do conftest.py
# A fixture 'mocker' vem do pytest-mock

def test_get_all_users_success(client, mocker):
    """
    Testa o endpoint GET /users no cenário de sucesso.
    """
    # --- 1. ARRANGE (Preparação) ---
    # Defina os dados que o mock do Supabase deve retornar
    fake_db_data = [
        {"id": 1, "name": "felipe", "email": "felipe@gmail.com", "role": "usuario", "ativo": True},
        {"id": 2, "name": "frank", "email": "frank@gmail.com", "role": "usuario", "ativo": False}
    ]
    
    # Configure a cadeia de chamadas do mock para retornar os dados falsos
    # mock_supabase_client foi definido no conftest.py
    from tests.conftest import mock_supabase_client
    mock_supabase_client.table.return_value.select.return_value.execute.return_value.data = fake_db_data

    # --- 2. ACT (Execução) ---
    # Use o TestClient para fazer uma requisição GET ao endpoint
    response = client.get("/users")

    # --- 3. ASSERT (Verificação) ---
    # Verifique se o status code da resposta é 200 OK
    assert response.status_code == 200
    
    # Verifique se o corpo da resposta (JSON) corresponde aos dados que esperamos
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["name"] == "felipe"
    assert response_data[1]["email"] == "frank@gmail.com"


def test_get_all_users_database_error(client, mocker):
    """
    Testa o endpoint GET /users quando o serviço lança uma exceção.
    """
    # --- 1. ARRANGE ---
    # Configure o mock para lançar um erro quando `execute()` for chamado
    from tests.conftest import mock_supabase_client
    mock_supabase_client.table.return_value.select.return_value.execute.side_effect = Exception("Erro de conexão com o BD")

    # --- 2. ACT ---
    response = client.get("/users")

    # --- 3. ASSERT ---
    # A sua função `listar_registros` captura a exceção e levanta uma HTTPException.
    # O FastAPI converte isso em um status code 500.
    assert response.status_code == 500
    
    # Verifique a mensagem de erro no corpo da resposta
    assert "Erro ao listar registros" in response.json()["detail"]