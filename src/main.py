from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import processes
from src.api import health
from src.database import engine, Base
from src.models.processo import Processo

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

# Endpoints para scraping
from fastapi import BackgroundTasks, Depends
from sqlalchemy.orm import Session
from src.database import get_db
from src.scrapers.datajud_scraper import DataJudScraper

@app.post("/api/scrape")
async def scrape_processos(max_por_tipo: int = 5000, db: Session = Depends(get_db)):
    """Coletar processos reais da API do DataJud"""
    scraper = DataJudScraper()
    novos, duplicados = scraper.coletar_todos(max_por_tipo)
    return {
        "message": "Scraping concluído!",
        "processos_novos": novos,
        "processos_duplicados": duplicados
    }

# ========================================
# ENDPOINT DE ATUALIZAÇÃO DE COMARCAS V2
# ========================================
@app.post("/api/atualizar-comarcas-massa")
async def atualizar_comarcas_massa(db: Session = Depends(get_db)):
    """Atualiza comarca de TODOS os processos usando mapeamento completo"""
    try:
        from src.utils.comarcas_data import COMARCAS_TJSP, COMARCAS_TJBA
        
        processos = db.query(Processo).all()
        atualizados = 0
        
        for p in processos:
            numero_limpo = ''.join(c for c in p.numero_processo if c.isdigit())
            
            if len(numero_limpo) >= 20:
                codigo = numero_limpo[-4:]
                
                mapa = COMARCAS_TJSP if p.tribunal == "TJSP" else COMARCAS_TJBA
                comarca_nova = mapa.get(codigo, f"Comarca {codigo}")
                
                if comarca_nova != p.comarca:
                    p.comarca = comarca_nova
                    atualizados += 1
        
        db.commit()
        
        return {
            "success": True,
            "total_processos": len(processos),
            "comarcas_atualizadas": atualizados,
            "message": f"✅ {atualizados} comarcas atualizadas!"
        }
    
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}

