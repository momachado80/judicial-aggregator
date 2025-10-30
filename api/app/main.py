from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

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
from app.api import seed, scrape

app.include_router(seed.router, prefix="/api", tags=["seed"])
app.include_router(scrape.router, prefix="/api", tags=["scrape"])

@app.get("/")
def root():
    return {
        "message": "Judicial Aggregator API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
