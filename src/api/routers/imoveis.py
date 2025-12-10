"""
Router para verificação de imóveis
- Mantém funcionalidade antiga (JSON)
- Adiciona nova funcionalidade via Selenium
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# MODELOS
# ============================================================

class VerificarImovelRequest(BaseModel):
    numero: str


class VerificarLoteRequest(BaseModel):
    numeros: list[str]


# ============================================================
# CACHE EM MEMÓRIA
# ============================================================

_cache_verificacoes: dict[str, dict] = {}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def carregar_processos_imoveis():
    """Carrega processos com imóveis do arquivo JSON (legado)"""
    caminhos = [
        Path("src/data/processos_com_imoveis.json"),
        Path("data/processos_com_imoveis.json"),
        Path("/app/src/data/processos_com_imoveis.json"),
    ]
    
    for caminho in caminhos:
        if caminho.exists():
            with open(caminho, 'r') as f:
                return json.load(f)
    
    return {"total": 0, "com_imovel": 0, "processos": []}


# ============================================================
# ENDPOINTS LEGADOS (mantidos para compatibilidade)
# ============================================================

@router.get("/processos-com-imoveis")
async def listar_processos_com_imoveis(
    tipo: Optional[str] = None,
    comarca: Optional[str] = None,
    apenas_imoveis: bool = True
):
    """Lista processos que mencionam imóveis nos PDFs do DJE (legado)"""
    data = carregar_processos_imoveis()
    processos = data.get("processos", [])
    
    if apenas_imoveis:
        processos = [p for p in processos if p.get("tem_imovel")]
    
    if tipo:
        processos = [p for p in processos if tipo.lower() in p.get("tipo", "").lower()]
    
    if comarca:
        processos = [p for p in processos if comarca in p.get("codigo_comarca", "")]
    
    for p in processos:
        n = p["numero"]
        p["url_tjsp"] = f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={n}"
    
    return {
        "total": len(processos),
        "processos": processos
    }


@router.get("/estatisticas-imoveis")
async def estatisticas_imoveis():
    """Estatísticas dos processos com imóveis (legado)"""
    data = carregar_processos_imoveis()
    processos = data.get("processos", [])
    
    com_imovel = [p for p in processos if p.get("tem_imovel")]
    inventarios = [p for p in com_imovel if p.get("tipo") == "Inventário"]
    divorcios = [p for p in com_imovel if p.get("tipo") == "Divórcio"]
    
    comarcas = {}
    for p in com_imovel:
        cod = p.get("codigo_comarca", "?")
        comarcas[cod] = comarcas.get(cod, 0) + 1
    
    return {
        "total_processos": len(processos),
        "com_imovel": len(com_imovel),
        "inventarios": len(inventarios),
        "divorcios": len(divorcios),
        "por_comarca": comarcas
    }


# ============================================================
# NOVOS ENDPOINTS - VERIFICAÇÃO VIA SELENIUM
# ============================================================

@router.post("/verificar-imovel")
async def verificar_imovel(request: VerificarImovelRequest):
    """
    Verifica se um processo tem imóvel acessando o e-SAJ TJSP
    Usa Selenium com Chrome headless
    """
    numero = request.numero.strip()
    
    # Verifica cache
    if numero in _cache_verificacoes:
        logger.info(f"Cache hit para {numero}")
        cached = _cache_verificacoes[numero].copy()
        cached['from_cache'] = True
        return cached
    
    try:
        from src.services.verificar_imoveis import verificar_processo
        
        resultado = verificar_processo(numero)
        resultado['from_cache'] = False
        
        # Salva no cache
        _cache_verificacoes[numero] = resultado
        
        return resultado
        
    except ImportError as e:
        logger.error(f"Selenium não disponível: {e}")
        raise HTTPException(
            status_code=503,
            detail="Serviço de verificação não disponível. Selenium não instalado."
        )
    except Exception as e:
        logger.error(f"Erro ao verificar {numero}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar processo: {str(e)}"
        )


@router.post("/verificar-imoveis-lote")
async def verificar_imoveis_lote(request: VerificarLoteRequest):
    """
    Verifica múltiplos processos em lote (máx 10 por requisição)
    """
    numeros = [n.strip() for n in request.numeros if n.strip()]
    
    if len(numeros) > 10:
        raise HTTPException(
            status_code=400,
            detail="Máximo de 10 processos por requisição para não sobrecarregar"
        )
    
    if len(numeros) == 0:
        raise HTTPException(
            status_code=400,
            detail="Nenhum número de processo informado"
        )
    
    resultados = []
    
    try:
        from src.services.verificar_imoveis import verificar_processo
        import time
        
        for i, numero in enumerate(numeros):
            # Verifica cache primeiro
            if numero in _cache_verificacoes:
                cached = _cache_verificacoes[numero].copy()
                cached['from_cache'] = True
                resultados.append(cached)
                continue
            
            resultado = verificar_processo(numero)
            resultado['from_cache'] = False
            _cache_verificacoes[numero] = resultado
            resultados.append(resultado)
            
            # Delay entre requisições (exceto último)
            if i < len(numeros) - 1:
                time.sleep(2)
        
        # Estatísticas
        com_imovel = [r for r in resultados if r.get('tem_imovel') == True]
        sem_imovel = [r for r in resultados if r.get('tem_imovel') == False]
        com_erro = [r for r in resultados if r.get('erro')]
        
        return {
            "total": len(resultados),
            "com_imovel": len(com_imovel),
            "sem_imovel": len(sem_imovel),
            "com_erro": len(com_erro),
            "resultados": resultados
        }
        
    except ImportError as e:
        logger.error(f"Selenium não disponível: {e}")
        raise HTTPException(
            status_code=503,
            detail="Serviço de verificação não disponível"
        )
    except Exception as e:
        logger.error(f"Erro no lote: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar processos: {str(e)}"
        )


@router.get("/verificar-imovel/status")
async def status_verificacao():
    """
    Verifica se o serviço de verificação via Selenium está disponível
    """
    try:
        from src.services.verificar_imoveis import criar_driver
        
        # Tenta criar o driver para verificar se Chrome está funcionando
        driver = criar_driver()
        driver.quit()
        
        return {
            "disponivel": True,
            "cache_size": len(_cache_verificacoes),
            "mensagem": "Serviço de verificação de imóveis está operacional"
        }
    except ImportError:
        return {
            "disponivel": False,
            "cache_size": len(_cache_verificacoes),
            "mensagem": "Selenium não instalado"
        }
    except Exception as e:
        return {
            "disponivel": False,
            "cache_size": len(_cache_verificacoes),
            "mensagem": f"Erro: {str(e)}"
        }


@router.delete("/verificar-imovel/cache")
async def limpar_cache():
    """Limpa o cache de verificações"""
    global _cache_verificacoes
    tamanho_anterior = len(_cache_verificacoes)
    _cache_verificacoes = {}
    
    return {
        "mensagem": "Cache limpo com sucesso",
        "itens_removidos": tamanho_anterior
    }


@router.get("/verificar-imovel/cache")
async def ver_cache():
    """Mostra o conteúdo do cache"""
    return {
        "total": len(_cache_verificacoes),
        "processos": list(_cache_verificacoes.keys()),
        "detalhes": _cache_verificacoes
    }
