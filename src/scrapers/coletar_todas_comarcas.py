"""
Script para coletar processos de TODAS as comarcas de SP e BA
Coleta de forma distribuída para garantir representatividade
"""
import requests
import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.database import get_db
from src.models import Processo

class ColetorCompleto:
    def __init__(self):
        self.url_tjsp = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
        self.url_tjba = "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
        }
    
    def buscar_todos_processos(self, tribunal: str, classe: str, max_processos: int = 50000):
        """Busca TODOS os processos disponíveis, sem limite artificial"""
        
        url = self.url_tjsp if tribunal == "TJSP" else self.url_tjba
        
        print(f"\n{'='*60}")
        print(f"🔍 Coletando {classe} do {tribunal}")
        print(f"🎯 Meta: até {max_processos:,} processos")
        print(f"{'='*60}\n")
        
        db = next(get_db())
        total_novos = 0
        total_duplicados = 0
        from_page = 0
        batch_size = 100
        
        while from_page < max_processos:
            payload = {
                "query": {"match": {"classe.nome": classe}},
                "size": batch_size,
                "from": from_page,
                "sort": [{"dataAjuizamento": {"order": "desc"}}]  # Mais recentes primeiro
            }
            
            try:
                response = requests.post(url, json=payload, headers=self.headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                hits = data.get("hits", {}).get("hits", [])
                total_disponivel = data.get("hits", {}).get("total", {}).get("value", 0)
                
                if from_page == 0:
                    print(f"📊 Total disponível na API: {total_disponivel:,}")
                
                if not hits:
                    print(f"✅ Fim dos resultados em {from_page:,} processos")
                    break
                
                # Processar e salvar
                for hit in hits:
                    source = hit.get("_source", {})
                    numero_cnj = source.get("numeroProcesso", "")
                    
                    if not numero_cnj or len(numero_cnj) < 20:
                        continue
                    
                    # Extrair comarca do CNJ (últimos 4 dígitos)
                    codigo_comarca = ''.join(c for c in numero_cnj if c.isdigit())[-4:]
                    comarca = f"Comarca {codigo_comarca}"  # Placeholder, será atualizado depois
                    
                    # Verificar duplicata
                    existe = db.query(Processo).filter(
                        Processo.numero_processo == numero_cnj
                    ).first()
                    
                    if existe:
                        total_duplicados += 1
                        continue
                    
                    # Criar processo
                    processo = Processo(
                        numero_processo=numero_cnj,
                        tribunal=tribunal,
                        tipo_processo=classe,
                        classe=classe,
                        comarca=comarca,
                        relevancia="Média",
                        score_relevancia=0.6,
                        status="pendente"
                    )
                    
                    try:
                        db.add(processo)
                        db.commit()
                        total_novos += 1
                    except IntegrityError:
                        db.rollback()
                        total_duplicados += 1
                
                # Progresso
                from_page += batch_size
                progresso = min(100, (from_page * 100) // min(max_processos, total_disponivel))
                print(f"📥 {from_page:,} processados | +{total_novos:,} novos | ~{total_duplicados:,} duplicados | {progresso}%")
                
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Erro na página {from_page}: {e}")
                time.sleep(2)
                continue
        
        print(f"\n✅ Concluído {tribunal} - {classe}")
        print(f"   Novos: {total_novos:,}")
        print(f"   Duplicados: {total_duplicados:,}\n")
        
        return total_novos, total_duplicados
    
    def coletar_tudo(self):
        """Coleta TUDO de ambos os tribunais"""
        
        print("\n" + "="*60)
        print("🚀 COLETA MASSIVA DE PROCESSOS")
        print("="*60)
        
        total_geral = 0
        
        for tribunal in ["TJSP", "TJBA"]:
            for classe in ["Inventário", "Divórcio"]:
                novos, _ = self.buscar_todos_processos(tribunal, classe, max_processos=50000)
                total_geral += novos
        
        print("\n" + "="*60)
        print(f"🎉 COLETA COMPLETA!")
        print(f"✨ Total de processos novos: {total_geral:,}")
        print("="*60)
        
        # Atualizar comarcas
        print("\n🔄 Atualizando comarcas...")
        import requests
        resp = requests.post("https://judicial-aggregator-production.up.railway.app/api/atualizar-comarcas-massa")
        print(f"✅ {resp.json()}")

if __name__ == "__main__":
    coletor = ColetorCompleto()
    coletor.coletar_tudo()
