# Usar imagem base com Python
FROM python:3.9

# Definir diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Expor a porta usada pelo Uvicorn
EXPOSE 8000

# Rodar a aplicação FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]