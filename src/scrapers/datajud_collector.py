"""
Coletor de processos REAIS da API DataJud com formatação CNJ correta
"""
import requests
import time
from datetime import datetime
from typing import Dict
from sqlalchemy.exc import IntegrityError
from src.database import SessionLocal
from src.models.processo import Processo

class DataJudCollector:
    def __init__(self):
        self.api_key = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
        self.endpoints = {
            "TJSP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search",
            "TJBA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
        }
    
    def formatar_numero_cnj(self, numero_sem_formato: str) -> str:
        """
        Converte: 00567233219978050001
        Para:     0056723-32.1997.8.05.0001
        """
        if not numero_sem_formato or len(numero_sem_formato) != 20:
            return numero_sem_formato
        
        try:
            sequencial = numero_sem_formato[0:7]
            dv = numero_sem_formato[7:9]
            ano = numero_sem_formato[9:13]
            justica = numero_sem_formato[13:14]
            tribunal = numero_sem_formato[14:16]
            origem = numero_sem_formato[16:20]
            
            return f"{sequencial}-{dv}.{ano}.{justica}.{tribunal}.{origem}"
        except:
            return numero_sem_formato
    
    def buscar_api(self, tribunal: str, classe: str, from_idx: int = 0, size: int = 100) -> Dict:
        """Busca processos na API DataJud"""
        url = self.endpoints.get(tribunal)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"APIKey {self.api_key}"
        }
        
        payload = {
            "query": {"match": {"classe.nome": classe}},
            "size": size,
            "from": from_idx
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro na API: {e}")
            return {"hits": {"hits": [], "total": {"value": 0}}}
    
    def coletar_e_salvar(self, tribunal: str, tipo_processo: str, max_processos: int = 5000):
        """Coleta e salva processos de um tribunal/tipo específico"""
        db = SessionLocal()
        
        try:
            print(f"\n📊 Coletando {tipo_processo} do {tribunal}...")
            
            resultado = self.buscar_api(tribunal, tipo_processo, 0, 1)
            total_api = resultado.get("hits", {}).get("total", {}).get("value", 0)
            print(f"   💾 Disponíveis na API: {total_api:,}")
            
            if total_api == 0:
                print(f"   ⚠️  Nenhum processo encontrado")
                return 0, 0
            
            coletados = 0
            novos = 0
            duplicados = 0
            from_idx = 0
            limite = min(max_processos, total_api)
            
            while coletados < limite:
                resultado = self.buscar_api(tribunal, tipo_processo, from_idx, 100)
                hits = resultado.get("hits", {}).get("hits", [])
                
                if not hits:
                    break
                
                for hit in hits:
                    source = hit.get("_source", {})
                    numero_bruto = source.get("numeroProcesso", "")
                    
                    if not numero_bruto:
                        continue
                    
                    numero_cnj = self.formatar_numero_cnj(numero_bruto)
                    
                    existe = db.query(Processo).filter(
                        Processo.numero_processo == numero_cnj
                    ).first()
                    
                    if existe:
                        duplicados += 1
                        continue
                    
                    orgao = source.get("orgaoJulgador", {})
                    comarca = orgao.get("nomeOrgao", "Não informado")
                    
                    data_ajuiz = source.get("dataAjuizamento")
                    if data_ajuiz:
                        try:
                            data_ajuiz = datetime.strptime(data_ajuiz[:8], "%Y%m%d").date()
                        except:
                            data_ajuiz = None
                    
                    relevancia = "Média"
                    score = 0.5
                    if data_ajuiz:
                        dias = (datetime.now().date() - data_ajuiz).days
                        if dias < 180:
                            relevancia = "Alta"
                            score = 0.8
                        elif dias > 730:
                            relevancia = "Baixa"
                            score = 0.3
                    
                    processo = Processo(
                        numero_processo=numero_cnj,
                        tribunal=tribunal,
                        tipo_processo=tipo_processo,
                        classe=tipo_processo,
                        comarca=comarca,
                        vara="Vara de Família e Sucessões",
                        data_ajuizamento=data_ajuiz,
                        relevancia=relevancia,
                        score_relevancia=score
                    )
                    
                    try:
                        db.add(processo)
                        db.commit()
                        novos += 1
                    except IntegrityError:
                        db.rollback()
                        duplicados += 1
                
                coletados += len(hits)
                progresso = min(100, int(coletados * 100 / limite))
                print(f"   ✅ {coletados:,}/{limite:,} ({progresso}%) - +{novos} novos, {duplicados} dup")
                
                from_idx += 100
                time.sleep(0.3)
                
                if coletados >= limite:
                    break
            
            print(f"   🎉 Concluído! {novos:,} processos novos")
            return novos, duplicados
            
        finally:
            db.close()
    
    def coletar_tudo(self, max_por_tipo: int = 5000):
        """Coleta todos os tipos de ambos tribunais"""
        print("="*60)
        print("🚀 INICIANDO COLETA DE PROCESSOS REAIS")
        print("="*60)
        
        total_novos = 0
        total_dup = 0
        
        for tribunal in ["TJSP", "TJBA"]:
            for tipo in ["Inventário", "Divórcio"]:
                novos, dup = self.coletar_e_salvar(tribunal, tipo, max_por_tipo)
                total_novos += novos
                total_dup += dup
        
        print("\n" + "="*60)
        print(f"🎉 COLETA FINALIZADA!")
        print(f"✨ Processos novos: {total_novos:,}")
        print(f"🔄 Duplicados: {total_dup:,}")
        print("="*60)
        
        return total_novos, total_dup

if __name__ == "__main__":
    collector = DataJudCollector()
    collector.coletar_tudo(max_por_tipo=5000)
