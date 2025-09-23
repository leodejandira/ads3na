from flask import Flask, jsonify, request, render_template
import sqlite3
import os

app = Flask(__name__)

# Caminho do banco dentro do container
DB_PATH = "banco.db"

# Inicializa o banco
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                valor TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/registros", methods=["GET"])
def listar():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, valor FROM registros")
    dados = [{"id": row[0], "valor": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(dados)

@app.route("/api/registros/<int:registro_id>", methods=["GET"])
def buscar(registro_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, valor FROM registros WHERE id = ?", (registro_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return jsonify({"id": row[0], "valor": row[1]})
    return jsonify({"erro": "não encontrado"}), 404

@app.route("/api/registros", methods=["POST"])
def inserir():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO registros (valor) VALUES (?)", (data["valor"],))
    conn.commit()
    conn.close()
    return jsonify({"mensagem": "inserido com sucesso"}), 201

@app.route("/api/registros/<int:registro_id>", methods=["DELETE"])
def deletar(registro_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registros WHERE id = ?", (registro_id,))
    conn.commit()
    conn.close()
    return jsonify({"mensagem": "deletado com sucesso"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
