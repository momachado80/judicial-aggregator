from fastapi import APIRouter
from typing import List, Optional
import json
from pathlib import Path

router = APIRouter()

def carregar_processos_imoveis():
    """Carrega processos com imóveis do arquivo JSON"""
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


@router.get("/processos-com-imoveis")
async def listar_processos_com_imoveis(
    tipo: Optional[str] = None,
    comarca: Optional[str] = None,
    apenas_imoveis: bool = True
):
    """Lista processos que mencionam imóveis nos PDFs do DJE"""
    data = carregar_processos_imoveis()
    processos = data.get("processos", [])
    
    # Filtrar
    if apenas_imoveis:
        processos = [p for p in processos if p.get("tem_imovel")]
    
    if tipo:
        processos = [p for p in processos if tipo.lower() in p.get("tipo", "").lower()]
    
    if comarca:
        processos = [p for p in processos if comarca in p.get("codigo_comarca", "")]
    
    # Adicionar URL do TJSP
    for p in processos:
        n = p["numero"]
        p["url_tjsp"] = f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={n}"
    
    return {
        "total": len(processos),
        "processos": processos
    }


@router.get("/estatisticas-imoveis")
async def estatisticas_imoveis():
    """Estatísticas dos processos com imóveis"""
    data = carregar_processos_imoveis()
    processos = data.get("processos", [])
    
    com_imovel = [p for p in processos if p.get("tem_imovel")]
    inventarios = [p for p in com_imovel if p.get("tipo") == "Inventário"]
    divorcios = [p for p in com_imovel if p.get("tipo") == "Divórcio"]
    
    # Contar por comarca
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
