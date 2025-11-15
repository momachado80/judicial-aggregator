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

from src.api.routers import processes, buscar_processos

# Adicionar prefix /api para todos os routers
app.include_router(processes.router, prefix="/api", tags=["processes"])
app.include_router(buscar_processos.router, prefix="/api", tags=["buscar"])


@app.get("/")
async def root():
    return {
        "message": "Judicial Aggregator API",
        "status": "online"
    }


@app.get("/health")
async def health():
    return {"status":"healthy"}


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
