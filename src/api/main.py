from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Judicial Aggregator API",
    description="API para buscar processos de Inventário e Divórcio do DJE TJSP",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api.routes import dje
app.include_router(dje.router)

@app.get("/")
def root():
    return {
        "message": "Judicial Aggregator API",
        "version": "2.0",
        "docs": "/docs",
        "stats": "/dje/stats/resumo"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "port": os.getenv("PORT", "8000")}
