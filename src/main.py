"""
FastAPI main application
CORRIGIDO: Não conecta ao DB durante import
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Criar app ANTES de qualquer conexão DB
app = FastAPI(title="Judicial Aggregator API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers DEPOIS de criar app
from src.api.routers import processes, buscar_processos

app.include_router(processes.router, tags=["processes"])
app.include_router(buscar_processos.router, tags=["buscar"])


@app.get("/")
async def root():
    return {
        "message": "Judicial Aggregator API",
        "status": "online",
        "endpoints": {
            "processes": "/processes",
            "search": "/api/buscar-processos",
            "comarcas": "/api/comarcas/{tribunal}"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Inicializar DB apenas quando app é chamado
@app.on_event("startup")
async def startup_event():
    """Conecta ao DB apenas no startup, não no import"""
    try:
        from src.database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Database init failed (will retry): {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
