# Em tests/test_endpoints.py

def test_get_all_users_success(api_client, mock_db_client):
    # --- 1. ARRANGE (Preparação) ---
    fake_users_data = [
        {"id": 1, "name": "felipe", "email": "felipe@gmail.com", "role": "usuario", "ativo": True},
        {"id": 2, "name": "frank", "email": "frank@gmail.com", "role": "usuario", "ativo": False}
    ]
    mock_db_client.table.return_value.select.return_value.execute.return_value.data = fake_users_data

    # --- 2. ACT (Execução) ---
    response = api_client.get("/usuarios")

    # --- 3. ASSERT (Verificação) ---

    # !! ADICIONE ESTE BLOCO DE CÓDIGO !!
    # Se o teste falhar, isso nos dirá o porquê.
    if response.status_code != 200:
        print("\n\n--- CORPO DO ERRO DA API ---")
        print(response.json())
        print("--------------------------\n\n")

    assert response.status_code == 200
    assert response.json() == fake_users_data