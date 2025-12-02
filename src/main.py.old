"""
FastAPI main application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Judicial Aggregator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api.routers import processes, buscar_processos, dje_buscar

# Adicionar prefix /api para todos os routers
app.include_router(processes.router, prefix="/api/processes", tags=["processes"])
app.include_router(buscar_processos.router, prefix="/api/buscar", tags=["buscar"])
app.include_router(dje_buscar.router, prefix="/api/dje", tags=["dje"])


@app.get("/")
async def root():
    return {
        "message": "Judicial Aggregator API",
        "status": "online"
    }


@app.get("/health")
async def health():
    return {"status":"healthy"}


@app.get("/test-railway-deploy")
async def test_railway_deploy():
    """Endpoint de teste para verificar se o código mais recente está deployado"""
    import os
    return {
        "status": "success",
        "message": "Railway está com o código MAIS RECENTE - commit 8938a55",
        "pdfs_directory_exists": os.path.exists("data/dje_pdfs"),
        "endpoint_teste_simples_exists": True
    }


@app.on_event("startup")
async def startup_event():
    try:
        from src.database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database init failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/debug/test-comarca")
async def test_comarca():
    from src.utils.comarcas import extrair_codigo_comarca, get_nome_comarca
    
    testes = [
        "1003711-15.2025.8.26.0650",
        "1004602-24.2025.8.26.0266",
        "1007829-84.2025.8.26.0019"
    ]
    
    resultados = []
    for num in testes:
        codigo = extrair_codigo_comarca(num)
        nome = get_nome_comarca(codigo, "TJSP")
        resultados.append({
            "numero": num,
            "codigo": codigo,
            "comarca": nome
        })
    
    return resultados

@app.get("/debug/listar-comarcas")
async def listar_comarcas():
    """Lista todos os códigos de comarca encontrados na API"""
    import requests
    from src.utils.comarcas import extrair_codigo_comarca, get_nome_comarca
    
    url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
    }
    
    query = {
        "query": {"bool": {"must": [{"term": {"classe.codigo": "289"}}]}},
        "size": 1000
    }
    
    response = requests.post(url, headers=headers, json=query, timeout=30)
    data = response.json()
    hits = data.get("hits", {}).get("hits", [])
    
    codigos = {}
    for hit in hits:
        numero = hit.get("_source", {}).get("numeroProcesso", "")
        if numero:
            codigo = extrair_codigo_comarca(numero)
            nome = get_nome_comarca(codigo, "TJSP")
            if codigo not in codigos:
                codigos[codigo] = {"nome": nome, "count": 0}
            codigos[codigo]["count"] += 1
    
    sorted_codigos = sorted(codigos.items(), key=lambda x: x[1]["count"], reverse=True)
    
    return {
        "total_codigos": len(codigos),
        "top_50": [
            {"codigo": k, "nome": v["nome"], "processos": v["count"]}
            for k, v in sorted_codigos[:50]
        ]
    }

# ========================================
# SERVIR FRONTEND (STATIC FILES)
# ========================================
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Verificar se a pasta do build existe (produção)
frontend_path = "web/out"
if os.path.exists(frontend_path):
    # Montar arquivos estáticos (JS, CSS, imagens)
    app.mount("/_next", StaticFiles(directory=f"{frontend_path}/_next"), name="next")
    
    # Rota catch-all para servir o index.html (SPA)
    # Importante: deve ser a última rota definida
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Se for rota de API, retornar 404 em vez do frontend
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")

        # Se for arquivo estático que não está em _next (ex: favicon.ico), tentar servir
        file_path = os.path.join(frontend_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # Caso contrário, servir index.html para o React lidar com a rota
        return FileResponse(os.path.join(frontend_path, "index.html"))
