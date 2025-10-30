FROM python:3.11-slim

WORKDIR /code

RUN apt-get update && apt-get install -y gcc postgresql-client && rm -rf /var/lib/apt/lists/*

# Copiar requirements do diretório raiz
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da API
COPY . /code

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
