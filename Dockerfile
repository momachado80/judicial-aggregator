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
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Instalar Chrome usando o método novo (sem apt-key deprecated)
RUN wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y /tmp/google-chrome.deb \
    && rm /tmp/google-chrome.deb \
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
