from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
import requests
import time
from datetime import datetime
from typing import Dict
from sqlalchemy.exc import IntegrityError

router = APIRouter()

class DataJudScraper:
    def __init__(self, db: Session):
        self.db = db
        self.tribunais_endpoints = {
            "TJSP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search",
            "TJBA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
        }
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
        })
    
    def buscar_processos(self, tribunal: str, classe_nome: str, from_page: int = 0, size: int = 100) -> Dict:
        url = self.tribunais_endpoints.get(tribunal)
        if not url:
            return {"hits": {"hits": [], "total": {"value": 0}}}
        payload = {
            "query": {"match": {"classe.nome": classe_nome}},
            "size": size,
            "from": from_page
        }
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro: {e}")
            return {"hits": {"hits": [], "total": {"value": 0}}}
    
    def processar_hit(self, hit: Dict, tribunal: str, tipo_processo: str) -> Dict:
        source = hit.get("_source", {})
        numero_cnj = source.get("numeroProcesso", "")
        if not numero_cnj:
            return None
        
        orgao = source.get("orgaoJulgador", {})
        comarca = orgao.get("nomeOrgao", "Não informado")
        
        data_ajuizamento = source.get("dataAjuizamento")
        if data_ajuizamento:
            try:
                data_ajuizamento = datetime.fromisoformat(data_ajuizamento.replace('Z', '+00:00'))
            except:
                data_ajuizamento = None
        
        movimentos = source.get("movimentos", [])
        score = 0.5
        if data_ajuizamento:
            dias = (datetime.now() - data_ajuizamento.replace(tzinfo=None)).days
            if dias < 180:
                score += 0.3
            elif dias < 365:
                score += 0.2
        
        if len(movimentos) > 0:
            score += 0.2
        
        relevancia = "Alta" if score >= 0.7 else "Média" if score >= 0.5 else "Baixa"
        
        return {
            "numero_processo": numero_cnj,
            "tribunal": tribunal,
            "tipo_processo": tipo_processo,
            "classe": source.get("classe", {}).get("nome", tipo_processo),
            "comarca": comarca,
            "relevancia": relevancia,
            "score_relevancia": score,
            "data_ajuizamento": data_ajuizamento
        }
    
    def coletar(self, max_por_tipo: int = 5000):
        from app.models import Process
        
        total_novos = 0
        total_duplicados = 0
        
        classes = {"Inventário": "Inventário", "Divórcio": "Divórcio"}
        
        for tribunal in ["TJSP", "TJBA"]:
            for tipo, classe_nome in classes.items():
                resultado = self.buscar_processos(tribunal, classe_nome, 0, 1)
                total_disponiveis = resultado.get("hits", {}).get("total", {}).get("value", 0)
                
                if total_disponiveis == 0:
                    continue
                
                coletados = 0
                from_page = 0
                limite = min(max_por_tipo, total_disponiveis)
                
                while coletados < limite:
                    resultado = self.buscar_processos(tribunal, classe_nome, from_page, 100)
                    hits = resultado.get("hits", {}).get("hits", [])
                    
                    if not hits:
                        break
                    
                    for hit in hits:
                        proc_data = self.processar_hit(hit, tribunal, tipo)
                        if not proc_data:
                            continue
                        
                        try:
                            existe = self.db.query(Process).filter(
                                Process.number == proc_data["numero_processo"]
                            ).first()
                            
                            if existe:
                                total_duplicados += 1
                                continue
                            
                            processo = Process(
                                number=proc_data["numero_processo"],
                                tribunal=proc_data["tribunal"],
                                type=proc_data["tipo_processo"],
                                filing_date=proc_data.get("data_ajuizamento"),
                                subject=proc_data["classe"],
                                status="Em andamento"
                            )
                            
                            self.db.add(processo)
                            self.db.commit()
                            total_novos += 1
                            
                        except IntegrityError:
                            self.db.rollback()
                            total_duplicados += 1
                        except Exception as e:
                            self.db.rollback()
                            print(f"Erro: {e}")
                    
                    coletados += len(hits)
                    from_page += 100
                    time.sleep(0.5)
                    
                    if coletados >= limite:
                        break
        
        return {"novos": total_novos, "duplicados": total_duplicados}

@router.post("/scrape")
async def scrape_processos(
    max_por_tipo: int = 5000,
    db: Session = Depends(get_db)
):
    """Coletar processos reais da API do DataJud"""
    scraper = DataJudScraper(db)
    resultado = scraper.coletar(max_por_tipo)
    return {
        "message": "Scraping concluído!",
        "processos_novos": resultado["novos"],
        "processos_duplicados": resultado["duplicados"]
    }
