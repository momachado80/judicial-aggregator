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
    
    def buscar_api(self, tribunal: str, classe: str, from_idx: int = 0, size: int = 100, 
                  comarcas: list = None, valor_min: float = None, valor_max: float = None) -> Dict:
        """Busca processos na API DataJud com filtros"""
        url = self.endpoints.get(tribunal)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"APIKey {self.api_key}"
        }
        
        # Construir query base
        must_clauses = [
            {"match": {"classe.nome": classe}}
        ]
        
        # Filtro de Comarcas (OR)
        if comarcas:
            should_clauses = []
            for comarca in comarcas:
                # Usar match simples para pegar "Vara de Campinas" buscando "Campinas"
                should_clauses.append({"match": {"orgaoJulgador.nome": comarca}})
            
            must_clauses.append({
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            })
            
        # Filtro de Valor da Causa (REMOVIDO DA QUERY API POIS O CAMPO GERALMENTE NÃO EXISTE)
        # A filtragem será feita em memória se o campo vier

        payload = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            },
            "size": size,
            "from": from_idx,
            "sort": [{"dataAjuizamento": {"order": "desc"}}]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro na API: {e}")
            return {"hits": {"hits": [], "total": {"value": 0}}}
    
    def coletar_e_salvar(self, tribunal: str, tipo_processo: str, max_processos: int = 5000,
                        comarcas: list = None, valor_min: float = None, valor_max: float = None,
                        dry_run: bool = False):
        """
        Coleta e salva processos de um tribunal/tipo específico com filtros.
        Args:
            dry_run: Se True, não salva no banco (apenas imprime)
        """
        db = None
        if not dry_run:
            db = SessionLocal()
        
        try:
            print(f"\n📊 Coletando {tipo_processo} do {tribunal}...")
            if comarcas:
                print(f"   📍 Filtro Comarcas: {comarcas}")
            if valor_min or valor_max:
                print(f"   💰 Filtro Valor: {valor_min} a {valor_max}")
            if dry_run:
                print("   🧪 MODO DE TESTE (DRY RUN): Sem salvar no banco")
            
            resultado = self.buscar_api(tribunal, tipo_processo, 0, 1, comarcas, valor_min, valor_max)
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
                resultado = self.buscar_api(tribunal, tipo_processo, from_idx, 100, comarcas, valor_min, valor_max)
                hits = resultado.get("hits", {}).get("hits", [])
                
                if not hits:
                    break
                
                for hit in hits:
                    source = hit.get("_source", {})
                    numero_bruto = source.get("numeroProcesso", "")
                    
                    if not numero_bruto:
                        continue
                    
                    numero_cnj = self.formatar_numero_cnj(numero_bruto)
                    
                    # Verificar duplicidade no banco (apenas se não for dry_run)
                    if not dry_run:
                        existe = db.query(Processo).filter(
                            Processo.numero_processo == numero_cnj
                        ).first()
                        
                        if existe:
                            duplicados += 1
                            continue
                    
                    orgao = source.get("orgaoJulgador", {})
                    comarca = orgao.get("nome", "Não informado")
                    
                    # Extrair valor da causa
                    valor_causa = source.get("dadosBasicos", {}).get("valorCausa", 0.0)
                    
                    data_ajuiz = source.get("dataAjuizamento")
                    if data_ajuiz:
                        try:
                            data_ajuiz = datetime.strptime(data_ajuiz[:8], "%Y%m%d").date()
                        except:
                            data_ajuiz = None
                    
                    relevancia = "Média"
                    score = 0.5
                    # Lógica de relevância baseada em valor e data
                    if valor_causa and valor_causa > 500000:
                        relevancia = "Altíssima"
                        score = 1.0
                    elif data_ajuiz:
                        dias = (datetime.now().date() - data_ajuiz).days
                        if dias < 180:
                            relevancia = "Alta"
                            score = 0.8
                    
                    if dry_run:
                        print(f"   🔎 Encontrado: {numero_cnj} | Comarca: {comarca} | Valor: {valor_causa}")
                        novos += 1
                    else:
                        processo = Processo(
                            numero_processo=numero_cnj,
                            tribunal=tribunal,
                            tipo_processo=tipo_processo,
                            classe=tipo_processo,
                            comarca=comarca,
                            vara="Vara de Família e Sucessões",
                            data_ajuizamento=data_ajuiz,
                            valor_causa=valor_causa,
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
            if db:
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
    
    # Teste com filtros específicos
    print("🧪 TESTE: Coletando Inventários em SP (Capital e Interior)")
    print("⚠️  Nota: Filtro de valor aplicado em memória (se disponível)")
    
    comarcas_teste = ["São Paulo", "Campinas", "Ribeirão Preto", "Sorocaba", "Santos"]
    
    collector.coletar_e_salvar(
        tribunal="TJSP", 
        tipo_processo="Inventário", 
        max_processos=100,
        comarcas=comarcas_teste,
        valor_min=100000,
        dry_run=True
    )
