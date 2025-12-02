from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Judicial Aggregator API",
    description="API para buscar processos de Inventário e Divórcio do DJE TJSP e DataJud",
    version="2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from src.api.routes import dje
from src.api.routers import buscar_processos

app.include_router(dje.router)
app.include_router(buscar_processos.router, prefix="/api", tags=["DataJud"])

@app.get("/")
def root():
    return {
        "message": "Judicial Aggregator API",
        "version": "2.1",
        "docs": "/docs",
        "endpoints": {
            "dje": "/api/dje/buscar-cache-instantaneo",
            "datajud": "/api/buscar-processos"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "port": os.getenv("PORT", "8000")}
# v2.1
