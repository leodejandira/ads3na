# Em tests/test_register_service.py

import pytest
from unittest.mock import MagicMock  # Adicione ou verifique este import
from fastapi import HTTPException
from app.api.services.register_service import listar_registros # Verifique o caminho do import
from app.api.schema.registros import Registro # Importe seu schema

# --- TESTE DE SUCESSO CORRIGIDO ---
def test_listar_registros_sucesso(): # Remova o 'mocker' se não for mais usado
    # 1. Crie um mock do banco de dados
    mock_db = MagicMock()
    fake_data = [{"id": 1, "name": "teste", "email": "teste@teste.com", "role": "usuario", "ativo": True}]
    mock_db.table.return_value.select.return_value.execute.return_value.data = fake_data

    # 2. CHAME A FUNÇÃO PASSANDO O MOCK
    resultado = listar_registros(db=mock_db)

    # 3. Verifique o resultado
    assert len(resultado) == 1
    assert resultado[0].name == "teste"


# --- TESTE DE ERRO CORRIGIDO ---
def test_listar_registros_erro_banco(): # Remova o 'mocker'
    # 1. Crie um mock "quebrado"
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.execute.side_effect = Exception("Erro simulado")

    # 2. Verifique se a exceção é levantada ao CHAMAR A FUNÇÃO COM O MOCK
    with pytest.raises(HTTPException):
        listar_registros(db=mock_db)