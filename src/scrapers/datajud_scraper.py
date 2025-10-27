"""
Scraper para coletar TODOS os processos de Inventário e Divórcio
"""
import requests
import time
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.database import get_db
from src.models import Processo

class DataJudScraper:
    def __init__(self):
        self.tribunais_endpoints = {
            "TJSP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search",
            "TJBA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
        }
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
        })
    
    def calcular_relevancia(self, data_ajuizamento: str = None, tem_movimento_recente: bool = False) -> tuple:
        score = 0.5
        if data_ajuizamento:
            try:
                data = datetime.fromisoformat(data_ajuizamento.replace('Z', '+00:00'))
                dias = (datetime.now() - data.replace(tzinfo=None)).days
                if dias < 180:
                    score += 0.3
                elif dias < 365:
                    score += 0.2
                elif dias < 730:
                    score += 0.1
            except:
                pass
        if tem_movimento_recente:
            score += 0.2
        if score >= 0.7:
            return "Alta", score
        elif score >= 0.5:
            return "Média", score
        else:
            return "Baixa", score
    
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
                data_ajuizamento = datetime.fromisoformat(data_ajuizamento.replace('Z', '+00:00')).date()
            except:
                data_ajuizamento = None
        movimentos = source.get("movimentos", [])
        tem_movimento_recente = len(movimentos) > 0
        relevancia, score = self.calcular_relevancia(source.get("dataAjuizamento"), tem_movimento_recente)
        classe = source.get("classe", {}).get("nome", tipo_processo)
        return {
            "numero_cnj": numero_cnj,
            "tribunal": tribunal,
            "tipo_processo": tipo_processo,
            "classe": classe,
            "comarca": comarca,
            "valor_causa": None,
            "relevancia": relevancia,
            "score_relevancia": score,
            "data_ajuizamento": data_ajuizamento
        }
    
    def salvar_processos(self, processos: List[Dict], db: Session):
        novos = 0
        duplicados = 0
        
        for proc_data in processos:
            if not proc_data:
                continue
            try:
                existe = db.query(Processo).filter(
                    Processo.numero_processo == proc_data["numero_cnj"]
                ).first()
                if existe:
                    duplicados += 1
                    continue
                processo = Processo(
                    numero_processo=proc_data["numero_cnj"],
                    tribunal=proc_data["tribunal"],
                    tipo_processo=proc_data["tipo_processo"],
                    classe=proc_data["classe"],
                    comarca=proc_data["comarca"],
                    valor_causa=proc_data.get("valor_causa"),
                    relevancia=proc_data["relevancia"],
                    score_relevancia=proc_data["score_relevancia"],
                    data_ajuizamento=proc_data.get("data_ajuizamento")
                )
                db.add(processo)
                novos += 1
                
                # Commit individual para evitar rollback em batch
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                    duplicados += 1
                    novos -= 1
            except Exception as e:
                db.rollback()
        
        return novos, duplicados
    
    def coletar_todos(self, max_por_tipo: int = 5000):
        print("🚀 Coletando processos REAIS de Inventário e Divórcio!")
        print(f"📋 Limite: {max_por_tipo:,} processos por tipo/tribunal")
        print()
        db = next(get_db())
        total_novos = 0
        total_duplicados = 0
        classes = {"Inventário": "Inventário", "Divórcio": "Divórcio"}
        
        for tribunal in ["TJSP", "TJBA"]:
            for tipo, classe_nome in classes.items():
                print(f"🔍 Coletando {tipo} do {tribunal}...")
                resultado = self.buscar_processos(tribunal, classe_nome, 0, 1)
                total_disponiveis = resultado.get("hits", {}).get("total", {}).get("value", 0)
                print(f"   📊 Total disponível na API: {total_disponiveis:,}")
                if total_disponiveis == 0:
                    print(f"   ⚠️  Nenhum processo encontrado\n")
                    continue
                coletados = 0
                from_page = 0
                limite = min(max_por_tipo, total_disponiveis)
                while coletados < limite:
                    resultado = self.buscar_processos(tribunal, classe_nome, from_page, 100)
                    hits = resultado.get("hits", {}).get("hits", [])
                    if not hits:
                        break
                    processos = [self.processar_hit(hit, tribunal, tipo) for hit in hits]
                    processos = [p for p in processos if p]
                    if processos:
                        novos, duplicados = self.salvar_processos(processos, db)
                        total_novos += novos
                        total_duplicados += duplicados
                        coletados += len(hits)
                        progresso = min(100, coletados * 100 // limite)
                        print(f"   ✅ {coletados:,}/{limite:,} ({progresso}%) - +{novos} novos, {duplicados} duplicados")
                    from_page += 100
                    time.sleep(0.5)
                    if coletados >= limite:
                        break
                print(f"   🎉 Concluído: {coletados:,} processos\n")
        print("=" * 60)
        print(f"🎉 COLETA COMPLETA!")
        print(f"✨ Processos novos: {total_novos:,}")
        print(f"🔄 Duplicados: {total_duplicados:,}")
        print("=" * 60)
        return total_novos, total_duplicados

if __name__ == "__main__":
    scraper = DataJudScraper()
    scraper.coletar_todos(max_por_tipo=5000)
