from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Judicial Aggregator API", version="2.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar routers
from src.api.routers.buscar_processos import router as buscar_router
from src.api.routers.imoveis import router as imoveis_router

# Rotas DJE (se existir)
try:
    from src.api.routes.dje import router as dje_router
    app.include_router(dje_router, prefix="/api/dje", tags=["DJE"])
except ImportError:
    pass

app.include_router(buscar_router, prefix="/api", tags=["DataJud"])
app.include_router(imoveis_router, prefix="/api", tags=["Imóveis"])


@app.get("/")
def root():
    return {
        "message": "Judicial Aggregator API",
        "version": "2.3",
        "docs": "/docs",
        "endpoints": {
            "datajud": "/api/buscar-processos",
            "imoveis": "/api/processos-com-imoveis",
            "estatisticas": "/api/estatisticas-imoveis",
            "comarcas": "/api/comarcas"
        }
    }
