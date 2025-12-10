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
# ESTÁGIO 2: Backend (Python) com Chrome
# ========================================
FROM python:3.11-slim

# Instalar dependências do sistema + Chrome
RUN apt-get update && apt-get install -y \
    libpq5 \
    libpq-dev \
    gcc \
    wget \
    gnupg \
    unzip \
    curl \
    # Dependências do Chrome
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código do backend
COPY . .

# Copiar o build do frontend do estágio anterior
COPY --from=frontend-builder /app/web/out /app/web/out

# Expor porta
EXPOSE 8080

# Comando para iniciar
CMD uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
