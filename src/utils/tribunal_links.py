"""Gera links para consulta nos sites dos tribunais"""
import re

def gerar_link_tjsp(numero_cnj: str) -> str:
    """Link direto para processo no TJSP"""
    numero = numero_cnj.replace('-', '').replace('.', '')
    return f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&dadosConsulta.localPesquisa.cdLocal=-1&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&numeroDigitoAnoUnificado={numero[0:15]}&foroNumeroUnificado={numero[16:20]}&dadosConsulta.valorConsultaNuUnificado={numero_cnj}"

def gerar_link_tjba(numero_cnj: str) -> str:
    """Link para consulta no TJBA"""
    return f"https://esaj.tjba.jus.br/cpopg/open.do?gateway=true"

def gerar_link_tribunal(numero_cnj: str, tribunal: str) -> str:
    """Retorna link baseado no tribunal"""
    if tribunal == "TJSP":
        return gerar_link_tjsp(numero_cnj)
    elif tribunal == "TJBA":
        return gerar_link_tjba(numero_cnj)
    return None
