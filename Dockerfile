# ========================================
# ESTÁGIO 1: Build do Frontend (Node.js)
# ========================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/web

# Copiar arquivos de dependências
COPY web/package.json web/package-lock.json ./

# Instalar dependências
RUN npm ci

# Copiar código fonte do frontend
COPY web/ .

# Build do Next.js (gera pasta 'out' devido ao output: 'export')
RUN npm run build

# ========================================
# ESTÁGIO 2: Backend (Python)
# ========================================
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    libpq5 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código do backend
COPY . .

# Copiar o build do frontend do estágio anterior
# O build estático do Next.js fica em /app/web/out
COPY --from=frontend-builder /app/web/out /app/web/out

# Expor porta
EXPOSE 8080

# Comando para iniciar
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
