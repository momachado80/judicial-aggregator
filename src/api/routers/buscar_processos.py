from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
from src.utils.comarcas import get_comarca_nome, extrair_codigo_comarca, COMARCAS_TJSP, FOROS_SAO_PAULO_CAPITAL

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
    "Divisão e Demarcação": 34,
    "Extinção de Condomínio": {"classe": 7, "assuntos": ["Extinção", "Condomínio"]},
    "Inventário": 39,
    "Divórcio Litigioso": 12541,
    "Divórcio Consensual": 12372
}

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

MOVIMENTOS_INATIVOS = {
    "baixa definitiva", "arquivado definitivamente", "trânsito em julgado",
    "processo suspenso", "suspensão do processo", "sobrestamento",
}


def get_codigos_comarca_por_nome(nome: str) -> List[str]:
    nome_lower = nome.lower().strip()
    if nome_lower in ["são paulo", "sao paulo", "sp capital", "capital", "são paulo (capital)", "sao paulo (capital)"]:
        return list(FOROS_SAO_PAULO_CAPITAL)
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower == nome_comarca.lower():
            return [codigo]
    for codigo, nome_comarca in COMARCAS_TJSP.items():
        if nome_lower in nome_comarca.lower():
            return [codigo]
    return []


def get_ultimo_movimento(movimentos: List[Dict]) -> Dict:
    if not movimentos:
        return {}
    return sorted(movimentos, key=lambda m: m.get("dataHora", ""), reverse=True)[0]


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



def _get_tipo_codigo(tipo: str) -> int:
    """Retorna o código da classe para um tipo de processo"""
    tipo_config = TIPOS_PROCESSO_MAPPING.get(tipo)
    if isinstance(tipo_config, dict):
        return tipo_config["classe"]
    return tipo_config if tipo_config else 39

def _get_assuntos_filtro(tipo: str) -> list:
    """Retorna os assuntos para filtrar, se houver"""
    tipo_config = TIPOS_PROCESSO_MAPPING.get(tipo)
    if isinstance(tipo_config, dict):
        return tipo_config.get("assuntos", [])
    return []

def _buscar_com_wildcard(tribunal: str, tipo_cod: int, codigo_comarca: str, tipo: str, max_processos: int) -> List[Dict]:
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal.lower()}/_search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"APIKey {DATAJUD_API_KEY}"
    }
    
    processos = []
    wildcard_pattern = f"*826{codigo_comarca}"
    
    # Paginar com from (limite 10k, então max 10 páginas de 1000)
    for pagina in range(10):
        if len(processos) >= max_processos:
            break
        
        from_offset = pagina * 1000
        
        # Construir cláusulas must (inclui assuntos se for tipo especial)
        must_clauses = [
            {"term": {"classe.codigo": tipo_cod}},
            {"wildcard": {"numeroProcesso": wildcard_pattern}}
        ]
        for assunto in _get_assuntos_filtro(tipo):
            must_clauses.append({"match": {"assuntos.nome": assunto}})
        
        query = {
            "query": {
                "bool": {
                    "must": must_clauses
                }
            },
            "size": 1000,
            "from": from_offset,
            "sort": [{"dataAjuizamento": {"order": "desc"}}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=query, timeout=60)
            if response.status_code != 200:
                print(f"Erro API {response.status_code}: {response.text[:200]}")
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
            
            print(f"Wildcard {tipo} pag {pagina+1}: {len(hits)} hits, total: {len(processos)}")
            
            if len(hits) < 1000:
                break
                
        except Exception as e:
            print(f"Erro: {e}")
            break
    
    return processos


def _buscar_simples(tribunal: str, tipo: str, max_processos: int) -> List[Dict]:
    tipo_cod = _get_tipo_codigo(tipo)
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
            tasks = []
            for tribunal in request.tribunais:
                for tipo in request.tipos_processo:
                    task = loop.run_in_executor(executor, _buscar_simples, tribunal, tipo, 1000)
                    tasks.append(task)
            resultados = await asyncio.gather(*tasks)
        else:
            tasks = []
            for codigo in codigos_comarca:
                for tribunal in request.tribunais:
                    for tipo in request.tipos_processo:
                        tipo_cod = _get_tipo_codigo(tipo)
                        task = loop.run_in_executor(
                            executor, _buscar_com_wildcard,
                            tribunal, tipo_cod, codigo, tipo, request.quantidade
                        )
                        tasks.append(task)
            
            print(f"Executando {len(tasks)} buscas com wildcard...")
            resultados = await asyncio.gather(*tasks)
        
        todos = []
        for r in resultados:
            todos.extend(r)
        
        if not request.incluir_extintos:
            antes = len(todos)
            todos = [p for p in todos if p.get("ativo", True)]
            print(f"Total: {antes} | Ativos: {len(todos)} | Extintos removidos: {antes - len(todos)}")
        
        vistos = set()
        unicos = []
        for p in todos:
            if p["numero"] not in vistos:
                vistos.add(p["numero"])
                unicos.append(p)
        
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


# ========== BUSCA POR NOME DE PARTE ==========

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import re

def _get_chrome_driver():
    """Configura o Chrome em modo headless"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(options=options)


def _buscar_por_parte_esaj(nome_parte: str, max_resultados: int = 100) -> List[Dict]:
    """Busca processos por nome de parte no e-SAJ TJSP"""
    driver = None
    processos = []
    
    try:
        driver = _get_chrome_driver()
        
        # Acessa a página de busca
        url = "https://esaj.tjsp.jus.br/cpopg/open.do"
        driver.get(url)
        time.sleep(2)
        
        # Seleciona busca por nome da parte
        select_tipo = Select(driver.find_element(By.ID, "cbPesquisa"))
        select_tipo.select_by_value("NMPARTE")
        time.sleep(0.5)
        
        # Preenche o nome
        campo_nome = driver.find_element(By.ID, "dadosConsulta.valorConsulta")
        campo_nome.clear()
        campo_nome.send_keys(nome_parte)
        
        # Clica em pesquisar
        btn_pesquisar = driver.find_element(By.ID, "botaoConsultarProcessos")
        btn_pesquisar.click()
        
        # Aguarda resultados
        time.sleep(3)
        
        # Verifica se tem resultados
        try:
            # Tenta encontrar a lista de processos
            lista = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#listagemDeProcessos, .resultadoLista, .processoLista"))
            )
        except:
            # Pode ter ido direto para um processo único
            pass
        
        # Extrai os processos da página
        # Tenta diferentes seletores possíveis
        linhas = driver.find_elements(By.CSS_SELECTOR, "tr.fundoClaro, tr.fundoEscuro, .linhaProcesso")
        
        if not linhas:
            # Tenta outro seletor
            linhas = driver.find_elements(By.CSS_SELECTOR, "a.linkProcesso, a[href*='processo.codigo']")
        
        for linha in linhas[:max_resultados]:
            try:
                # Extrai número do processo
                texto = linha.text
                match = re.search(r'(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})', texto)
                if match:
                    numero_formatado = match.group(1)
                    numero_limpo = numero_formatado.replace("-", "").replace(".", "")
                    
                    processos.append({
                        "numero": numero_limpo,
                        "numero_formatado": numero_formatado,
                        "fonte": "e-SAJ",
                        "url": f"https://esaj.tjsp.jus.br/cpopg/show.do?processo.codigo={numero_limpo}"
                    })
            except Exception as e:
                print(f"Erro extraindo linha: {e}")
                continue
        
        # Se não encontrou com seletores, tenta extrair do HTML bruto
        if not processos:
            html = driver.page_source
            matches = re.findall(r'(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})', html)
            for numero_formatado in list(set(matches))[:max_resultados]:
                numero_limpo = numero_formatado.replace("-", "").replace(".", "")
                processos.append({
                    "numero": numero_limpo,
                    "numero_formatado": numero_formatado,
                    "fonte": "e-SAJ",
                    "url": f"https://esaj.tjsp.jus.br/cpopg/show.do?processo.codigo={numero_limpo}"
                })
        
        print(f"Busca por parte '{nome_parte}': {len(processos)} processos encontrados")
        
    except Exception as e:
        print(f"Erro na busca por parte: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
    
    return processos


class BuscarPorParteRequest(BaseModel):
    nome_parte: str
    max_resultados: int = 100


@router.post("/buscar-por-parte")
async def buscar_por_parte(request: BuscarPorParteRequest):
    """Busca processos por nome de parte no e-SAJ TJSP"""
    try:
        if len(request.nome_parte) < 3:
            raise HTTPException(status_code=400, detail="Nome deve ter pelo menos 3 caracteres")
        
        loop = asyncio.get_event_loop()
        processos = await loop.run_in_executor(
            executor, _buscar_por_parte_esaj, 
            request.nome_parte, request.max_resultados
        )
        
        return {
            "nome_buscado": request.nome_parte,
            "total": len(processos),
            "processos": processos
        }
        
    except Exception as e:
        print(f"ERRO busca por parte: {e}")
        raise HTTPException(status_code=500, detail=str(e))
