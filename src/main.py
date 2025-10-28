from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import processes
from src.api import health
from src.database import engine, Base

app = FastAPI(
    title="Judicial Aggregator API",
    description="API para agregação de processos judiciais",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(processes.router, prefix="/processes", tags=["Processes"])

@app.get("/")
def root():
    return {
        "message": "Judicial Aggregator API",
        "version": "1.0.0",
        "docs": "/docs"
    }
