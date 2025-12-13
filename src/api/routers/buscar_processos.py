from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from src.utils.comarcas import get_comarca_nome, extrair_codigo_comarca, COMARCAS_TJSP, expandir_sao_paulo, FOROS_SAO_PAULO_CAPITAL

router = APIRouter()
executor = ThreadPoolExecutor(max_workers=20)

class BuscarProcessosRequest(BaseModel):
    tribunais: List[str]
    tipos_processo: List[str]
    comarcas: Optional[List[str]] = None
    quantidade: int = 500
    usar_cache: bool = True
    incluir_extintos: bool = False

TIPOS_PROCESSO_MAPPING = {
    "Inventário": 39,
    "Divórcio Litigioso": 12541,
    "Divórcio Consensual": 12372
}

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

MOVIMENTOS_INATIVOS = {
    "baixa definitiva",
    "arquivado definitivamente",
    "trânsito em julgado",
    "processo suspenso",
    "suspensão do processo",
    "sobrestamento",
}


def get_codigos_comarca_por_nome(nome: str) -> List[str]:
    nome_lower = nome.lower().strip()
    
    if nome_lower in ["são paulo", "sao paulo", "sp capital", "são paulo (capital)", "sao paulo (capital)", "capital"]:
        return list(FOROS_SAO_PAULO_CAPITAL)
    
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower == nome_comarca.lower():
            return [codigo]
    
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower in nome_comarca.lower() or nome_comarca.lower() in nome_lower:
            return [codigo]
    
    return []


def get_ultimo_movimento(movimentos: List[Dict]) -> Dict:
    if not movimentos:
        return {}
    movs_ordenados = sorted(movimentos, key=lambda m: m.get("dataHora", ""), reverse=True)
    return movs_ordenados[0] if movs_ordenados else {}


def processo_esta_ativo(movimentos: List[Dict]) -> tuple[bool, str]:
    ultimo = get_ultimo_movimento(movimentos)
    if not ultimo:
        return True, "sem_movimentos"
    
    nome_mov = ultimo.get("nome", "").lower().strip()
    
    if nome_mov == "definitivo":
        return False, "definitivo"
    
    for termo in MOVIMENTOS_INATIVOS:
        if termo in nome_mov:
            return False, termo
    
    return True, "ativo"


def _buscar_periodo(tribunal: str, tipo_cod: int, codigo_comarca: str, data_inicio: str, data_fim: str, tipo: str) -> List[Dict]:
    """Busca todos os processos de um periodo especifico"""
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal.lower()}/_search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"APIKey {DATAJUD_API_KEY}"
    }
    
    processos = []
    
    for pagina in range(10):
        from_offset = pagina * 1000
        if from_offset >= 10000:
            break
        
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"classe.codigo": tipo_cod}},
                        {"range": {"dataAjuizamento": {"gte": data_inicio, "lte": data_fim}}}
                    ]
                }
            },
            "size": 1000,
            "from": from_offset,
            "sort": [{"dataAjuizamento": {"order": "desc"}}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=query, timeout=30)
            if response.status_code != 200:
                break
            
            hits = response.json().get("hits", {}).get("hits", [])
            if not hits:
                break
            
            for hit in hits:
                source = hit.get("_source", {})
                numero = source.get("numeroProcesso", "")
                if not numero:
                    continue
                
                codigo = extrair_codigo_comarca(numero)
                if codigo != codigo_comarca:
                    continue
                
                movimentos = source.get("movimentos", [])
                ultimo_mov = get_ultimo_movimento(movimentos)
                ativo, motivo = processo_esta_ativo(movimentos)
                
                processos.append({
                    "numero": numero,
                    "tribunal": tribunal,
                    "tipo": tipo,
                    "comarca": get_comarca_nome(codigo, tribunal),
                    "codigo_comarca": codigo,
                    "data_ajuizamento": source.get("dataAjuizamento"),
                    "valor_causa": source.get("valorCausa"),
                    "ultimo_movimento": ultimo_mov.get("nome", ""),
                    "data_ultimo_movimento": ultimo_mov.get("dataHora", "")[:10] if ultimo_mov.get("dataHora") else "",
                    "ativo": ativo,
                    "motivo_inativo": motivo if not ativo else None,
                    "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={numero[:7]}-{numero[7:9]}.{numero[9:13]}.{numero[13:14]}.{numero[14:16]}.{numero[16:20]}"
                })
            
            print(f"Periodo {data_inicio[:7]}: pag {pagina+1}, {len(hits)} hits, {len(processos)} da comarca")
            
            if len(hits) < 1000:
                break
                
        except Exception as e:
            print(f"Erro periodo {data_inicio}: {e}")
            break
    
    return processos


def _buscar_simples(tribunal: str, tipo: str, max_processos: int) -> List[Dict]:
    """Busca simples sem filtro de comarca"""
    tipo_cod = TIPOS_PROCESSO_MAPPING.get(tipo, 39)
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal.lower()}/_search"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"APIKey {DATAJUD_API_KEY}"
    }
    
    query = {
        "query": {"bool": {"must": [{"term": {"classe.codigo": tipo_cod}}]}},
        "size": min(max_processos, 1000),
        "sort": [{"dataAjuizamento": {"order": "desc"}}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=query, timeout=30)
        if response.status_code != 200:
            return []
        
        hits = response.json().get("hits", {}).get("hits", [])
        processos = []
        
        for hit in hits:
            source = hit.get("_source", {})
            numero = source.get("numeroProcesso", "")
            if not numero:
                continue
            
            codigo = extrair_codigo_comarca(numero)
            movimentos = source.get("movimentos", [])
            ultimo_mov = get_ultimo_movimento(movimentos)
            ativo, motivo = processo_esta_ativo(movimentos)
            
            processos.append({
                "numero": numero,
                "tribunal": tribunal,
                "tipo": tipo,
                "comarca": get_comarca_nome(codigo, tribunal),
                "codigo_comarca": codigo,
                "data_ajuizamento": source.get("dataAjuizamento"),
                "valor_causa": source.get("valorCausa"),
                "ultimo_movimento": ultimo_mov.get("nome", ""),
                "data_ultimo_movimento": ultimo_mov.get("dataHora", "")[:10] if ultimo_mov.get("dataHora") else "",
                "ativo": ativo,
                "motivo_inativo": motivo if not ativo else None,
                "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={numero[:7]}-{numero[7:9]}.{numero[9:13]}.{numero[13:14]}.{numero[14:16]}.{numero[16:20]}"
            })
        
        return processos
        
    except Exception as e:
        print(f"Erro busca simples: {e}")
        return []


@router.post("/buscar-processos")
async def buscar_processos(request: BuscarProcessosRequest):
    try:
        loop = asyncio.get_event_loop()
        
        codigos_comarca = []
        if request.comarcas:
            for nome in request.comarcas:
                codigos = get_codigos_comarca_por_nome(nome)
                codigos_comarca.extend(codigos)
                print(f"Comarca '{nome}' -> codigos: {codigos}")
        
        if not codigos_comarca:
            # Sem comarca - busca simples
            tasks = []
            for tribunal in request.tribunais:
                for tipo in request.tipos_processo:
                    task = loop.run_in_executor(executor, _buscar_simples, tribunal, tipo, 1000)
                    tasks.append(task)
            
            resultados = await asyncio.gather(*tasks)
            todos = []
            for r in resultados:
                todos.extend(r)
        else:
            # Com comarca - busca paralela por periodos
            hoje = datetime.now()
            periodos = []
            
            # 5 anos em periodos de 6 meses
            for i in range(60):
                data_fim = hoje - timedelta(days=i*30)
                data_inicio = hoje - timedelta(days=(i+1)*30)
                periodos.append((data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))
            
            # Criar todas as tasks em paralelo
            tasks = []
            for codigo in codigos_comarca:
                for tribunal in request.tribunais:
                    for tipo in request.tipos_processo:
                        tipo_cod = TIPOS_PROCESSO_MAPPING.get(tipo, 39)
                        for data_inicio, data_fim in periodos:
                            task = loop.run_in_executor(
                                executor, _buscar_periodo,
                                tribunal, tipo_cod, codigo, data_inicio, data_fim, tipo
                            )
                            tasks.append(task)
            
            print(f"Executando {len(tasks)} buscas em paralelo...")
            resultados = await asyncio.gather(*tasks)
            
            todos = []
            for r in resultados:
                todos.extend(r)
        
        # Filtrar extintos
        if not request.incluir_extintos:
            antes = len(todos)
            todos = [p for p in todos if p.get("ativo", True)]
            print(f"Total: {antes} | Ativos: {len(todos)} | Extintos removidos: {antes - len(todos)}")
        
        # Remover duplicatas
        vistos = set()
        unicos = []
        for p in todos:
            if p["numero"] not in vistos:
                vistos.add(p["numero"])
                unicos.append(p)
        
        # Ordenar por data
        unicos.sort(key=lambda x: x.get("data_ajuizamento", ""), reverse=True)
        
        print(f"Retornando {min(len(unicos), request.quantidade)} processos")
        return unicos[:request.quantidade]
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comarcas")
async def listar_comarcas():
    from src.utils.comarcas import COMARCAS_TJSP, COMARCAS_TJBA
    return {
        "TJSP": sorted(set(COMARCAS_TJSP.values())),
        "TJBA": sorted(set(COMARCAS_TJBA.values()))
    }
