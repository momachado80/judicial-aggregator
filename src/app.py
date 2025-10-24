from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import health, processes, stats, export
from src.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Judicial Aggregator API",
    description="API para agregação de processos judiciais",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(processes.router, prefix="/processes", tags=["Processes"])
app.include_router(stats.router, tags=["Statistics"])
app.include_router(export.router, tags=["Export"])

@app.get("/")
def root():
    return {
        "message": "Judicial Aggregator API v2.0",
        "docs": "/docs",
        "health": "/health"
    }
