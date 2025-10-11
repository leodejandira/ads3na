# tests/test_register_service.py

import pytest
from fastapi import HTTPException

# Importe a função que você quer testar e o modelo Pydantic
from app.api.schema.registros import Registro 
from app.api.services.register_service import listar_registros

# tests/test_register_service.py

def test_listar_registros_sucesso(mocker):
    # ...

    fake_db_data = [
        {
           "id": 1,
            "name": "felipe",
            "email": "felipe@gmail.com",
            "senha": "felipe123",
            "role": "usuario", 
            "ativo": False   
        },
        {
            "id": 2,
            "name": "frank",
            "email": "frank@gmail.com",
            "senha": "frank123",
            "role": "usuario", 
            "ativo": False   
        },
    ]
    # ... (o resto do teste continua igual)
    
    # Crie um mock para a resposta do Supabase
    mock_supabase_response = mocker.Mock()
    mock_supabase_response.data = fake_db_data # O Supabase retorna dados no atributo .data
    
    # Crie a cadeia de mocks para simular: get_client().table().select().execute()
    mock_get_client = mocker.patch(
        "app.api.services.register_service.get_client", # Caminho para a função a ser mockada
    )
    mock_get_client.return_value.table.return_value.select.return_value.execute.return_value = mock_supabase_response

    # --- 2. EXECUÇÃO ---
    
    # Chame a função que estamos testando. Ela usará nosso mock em vez do BD real.
    result = listar_registros()
    
    # --- 3. VERIFICAÇÃO (Asserts) ---
    
    # Verifique se o resultado é uma lista
    assert isinstance(result, list)
    # Verifique se a lista tem o tamanho correto
    assert len(result) == 2
    # Verifique se os objetos na lista são do tipo Pydantic `Registro`
    assert isinstance(result[0], Registro)
    # Verifique se os dados foram mapeados corretamente
    assert result[0].email == "felipe@gmail.com"
    assert result[1].name == "frank"


def test_listar_registros_erro_banco(mocker):
    """
    Teste do "caminho triste": simula um erro de conexão com o BD.
    """
    # --- 1. PREPARAÇÃO ---
    
    # Desta vez, vamos fazer o mock lançar uma exceção quando for chamado.
    mocker.patch(
        "app.api.services.register_service.get_client",
        side_effect=Exception("Falha de conexão simulada") # side_effect faz o mock lançar um erro
    )
    
    # --- 2. EXECUÇÃO E VERIFICAÇÃO ---
    
    # Use pytest.raises para verificar se a exceção correta foi lançada
    with pytest.raises(HTTPException) as exc_info:
        listar_registros()
        
    # Verifique os detalhes da exceção
    assert exc_info.value.status_code == 500
    assert "Falha de conexão simulada" in exc_info.value.detail