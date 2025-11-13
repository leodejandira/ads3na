FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/app

EXPOSE 8000

ENV SECRET_KEY="sua_chave_super_secreta"
ENV ALGORITHM="HS256"
ENV SUPABASE_URL="https://hdgcquzcfbbwqufznatb.supabase.co"
ENV SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkZ2NxdXpjZmJid3F1ZnpuYXRiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MjY2NDMsImV4cCI6MjA3NDIwMjY0M30.7r9RNPhoGT4UJdolJFsDmaftbApKTg61DKgOcchkRWY"
ENV SUPABASE_KEY_ROLE="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhkZ2NxdXpjZmJid3F1ZnpuYXRiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODYyNjY0MywiZXhwIjoyMDc0MjAyNjQzfQ.d9qv3hbp1gWUD9HZGTQaQsLnVE8AZjECoQ-to9abnsM"
ENV OPENAI_API_KEY=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
ENV OPENAI_MODEL=gpt-4o-mini

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

