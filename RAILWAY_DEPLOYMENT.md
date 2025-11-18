# 🚂 Deployment no Railway.app

**URL de Produção:** https://virtuous-communication-production.up.railway.app

---

## ⚙️ Configuração Atual

### Arquivos de Configuração

1. **Procfile** (usado pelo Railway)
```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

2. **nixpacks.toml** (configuração do Nix)
```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT"
```

---

## 📦 Dependências

### Básicas (funcionam no Railway)
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic

### DJE System (requerem configuração adicional)
- ⚠️ **pdfplumber** - OK no Railway
- ⚠️ **playwright** - REQUER browsers instalados
- ⚠️ **chromium** - Não disponível por padrão

---

## 🔧 Ajustes para Produção Railway

### Opção 1: Modo Somente Leitura (RECOMENDADO)

**Usar apenas parsing de PDFs**, sem download automático:

1. PDFs são baixados localmente ou por outro serviço
2. Upload manual ou via S3/Cloud Storage
3. Railway processa PDFs já existentes

**Vantagens:**
- ✅ Funciona sem Playwright
- ✅ Mais leve e rápido
- ✅ Sem dependência de browsers

**Implementação:**
```python
# Endpoint para processar PDFs já existentes
POST /api/dje/processar-pdf
{
  "pdf_url": "https://storage.com/dje_15-11-2025_cad12.pdf"
  # ou
  "pdf_base64": "..."
}
```

### Opção 2: Playwright no Railway (COMPLEXO)

Requer configuração adicional no Railway:

1. **Adicionar buildpacks Playwright:**
```bash
# No Railway, adicionar:
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
PLAYWRIGHT_BROWSERS_PATH=/app/.playwright
```

2. **Instalar Chromium:**
```toml
# nixpacks.toml
[phases.setup]
nixPkgs = ["python311", "chromium"]

[phases.install]
cmds = [
  "pip install -r requirements.txt",
  "playwright install --with-deps chromium"
]
```

3. **Aumentar memória no Railway:**
- Minimum: 512MB → 1GB
- Chromium precisa de memória

**Desvantagens:**
- ⚠️ Consome mais recursos
- ⚠️ Deploy mais lento
- ⚠️ Custo maior

### Opção 3: Serviço Separado para Downloads

**Arquitetura:**
```
[Railway - API FastAPI]
    ↓ consulta
[Railway - Worker Celery] ← Download de PDFs
    ↓ salva
[Cloud Storage - S3/R2]
    ↓ lê
[Railway - API FastAPI] ← Processa PDFs
```

---

## 🚀 Deploy Atual (Recomendação Imediata)

### Passo 1: Ajustar endpoint DJE para modo Railway

Criar endpoint alternativo que não depende de download:

```python
# src/api/routers/dje_buscar.py

@router.post("/processar-pdfs-existentes")
async def processar_pdfs_existentes(request: ProcessarPDFsRequest):
    """
    Processa PDFs que já estão no diretório data/dje_pdfs/
    Funciona perfeitamente no Railway sem Playwright
    """
    pdf_dir = "data/dje_pdfs"
    pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

    # Processar cada PDF
    for pdf_filename in pdfs:
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        processos = extrair_processos_dje(
            pdf_path,
            filtrar_imoveis=True,
            filtrar_ativos=True,
            comarcas_filtro=request.comarcas,
            valor_min=request.valor_min,
            valor_max=request.valor_max
        )

    return processos
```

### Passo 2: Fazer Deploy

```bash
# 1. Commit mudanças
git add -A
git commit -m "fix: Corrigir Procfile para Railway deployment"
git push origin main

# 2. Railway fará auto-deploy
# Aguardar ~2-3 minutos
```

### Passo 3: Testar Produção

```bash
# Verificar health
curl https://virtuous-communication-production.up.railway.app/health

# Testar API
curl https://virtuous-communication-production.up.railway.app/docs
```

---

## 📊 Status Atual dos Endpoints

### ✅ Funcionam no Railway (SEM modificação)
- `GET /health`
- `GET /`
- `GET /api/processes`
- `POST /api/processes`
- `GET /api/processes/stats`

### ⚠️ Funcionam PARCIALMENTE (sem Playwright)
- `POST /api/dje/buscar` - Funciona se PDFs já existirem
- `GET /api/dje/status` - Funciona

### ❌ NÃO funcionam sem configuração adicional
- Download automático de DJE (precisa Playwright)

---

## 🎯 Solução Recomendada AGORA

**Modo Híbrido:**

1. **Desenvolvimento Local:**
   - Sistema DJE completo com download + parsing
   - Playwright funciona perfeitamente

2. **Produção Railway:**
   - Apenas parsing de PDFs (sem download)
   - PDFs podem ser:
     - Baixados localmente e commitados no repo (para demo)
     - Enviados via API (upload)
     - Armazenados em S3 e processados sob demanda

**Implementação:** Adicionar flag de ambiente

```python
# src/scrapers/dje_downloader.py

RAILWAY_MODE = os.getenv("RAILWAY_DEPLOY", "false") == "true"

def baixar_dje_tjsp(...):
    if RAILWAY_MODE:
        raise NotImplementedError(
            "Download de DJE não disponível em produção. "
            "Use /api/dje/processar-pdfs-existentes"
        )
    # ... código normal
```

---

## 🔑 Variáveis de Ambiente Railway

Configurar no Railway Dashboard:

```bash
# Banco de dados (já configurado automaticamente)
DATABASE_URL=postgresql://...

# Modo Railway
RAILWAY_DEPLOY=true

# Playwright (se optar por instalar)
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
PLAYWRIGHT_BROWSERS_PATH=/app/.playwright

# Python
PYTHONUNBUFFERED=1
```

---

## 📈 Próximos Passos

### Curto Prazo (Esta Semana)
1. ✅ Corrigir Procfile (FEITO)
2. ⏳ Fazer deploy e testar health endpoint
3. ⏳ Verificar logs no Railway
4. ⏳ Testar endpoints básicos

### Médio Prazo (Próximas 2 Semanas)
1. Implementar endpoint de upload de PDF
2. Configurar S3/R2 para armazenamento
3. Criar worker separado para downloads (opcional)

### Longo Prazo (1 Mês)
1. CI/CD automático
2. Testes automatizados no deploy
3. Monitoring (Sentry)
4. Backup automático

---

## 🐛 Troubleshooting Railway

### Erro: "Access denied"
- Verificar se o deployment finalizou
- Checar logs: `railway logs`
- Verificar variáveis de ambiente

### Erro: "Module not found"
- Verificar requirements.txt
- Fazer redeploy: `railway up`

### Erro: "Database connection failed"
- Verificar DATABASE_URL
- Checar PostgreSQL service no Railway

### Erro: "Playwright browser not found"
- Não usar download de DJE em produção
- Usar apenas parsing de PDFs existentes

---

**Última atualização:** 18/11/2025
**Status:** ✅ Procfile corrigido, pronto para deploy
