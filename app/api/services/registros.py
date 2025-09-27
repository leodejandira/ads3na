# api/services/registros.py
import sqlite3
from pathlib import Path
from typing import List, Optional

from api.schema.registros import Registro, RegistroCreate

DB_PATH = Path("banco.db")


def init_db():
    if not DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                valor TEXT NOT NULL
            )
        """
        )
        conn.commit()
        conn.close()


def listar_registros() -> List[Registro]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, valor FROM registros")
    rows = cursor.fetchall()
    conn.close()
    return [Registro(id=row[0], valor=row[1]) for row in rows]


def buscar_registro(registro_id: int) -> Optional[Registro]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, valor FROM registros WHERE id = ?", (registro_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Registro(id=row[0], valor=row[1])
    return None


def inserir_registro(data: RegistroCreate) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO registros (valor) VALUES (?)", (data.valor,))
    conn.commit()
    conn.close()


def deletar_registro(registro_id: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
    conn.commit()
    conn.close()
