# Usar uma imagem base com Python
FROM python:3.9

# Definir o diretório de trabalho
WORKDIR /app

# Copiar o arquivo de dependências
COPY requirements.txt .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do projeto para dentro do container
COPY . .

# Expôr a porta em que a API irá rodar
EXPOSE 8000

# Comando para rodar a API
CMD ["uvicorn", "api.services.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Usar Python 3.13
FROM python:3.13-slim

# Diretório de trabalho no container
WORKDIR /app

# Copiar arquivos para o container
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expor porta do Flask
EXPOSE 8000

# Rodar o app
CMD ["python", "miqueiasdev.py"]
