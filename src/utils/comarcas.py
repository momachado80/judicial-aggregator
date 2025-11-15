"""
Mapeamento completo de códigos de comarca para TJSP e TJBA
"""

TJSP_COMARCAS = {
    "0001": "São Paulo",
    "0019": "Americana",
    "0114": "Campinas",
    "0650": "Taboão da Serra",
    "0266": "Itaquaquecetuba",
    "0047": "São Vicente",
    # ... (cole aqui a lista completa que criamos antes)
}

TJBA_COMARCAS = {
    "0001": "Salvador",
    "0002": "Feira de Santana",
    # ... (lista TJBA)
}

def get_nome_comarca(codigo: str, tribunal: str) -> str:
    """Retorna o nome da comarca pelo código"""
    if tribunal == "TJSP":
        return TJSP_COMARCAS.get(codigo, f"Comarca {codigo}")
    elif tribunal == "TJBA":
        return TJBA_COMARCAS.get(codigo, f"Comarca {codigo}")
    return f"Comarca {codigo}"


def extrair_codigo_comarca(numero_processo: str) -> str:
    """
    Extrai o código da comarca do número do processo CNJ
    
    Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
    Exemplo: 1003711-15.2025.8.26.0650
                                  ^^^^
    """
    try:
        # Remover traços e pontos extras
        numero_limpo = numero_processo.replace('-', '').replace('.', '')
        
        # Pegar últimos 4 dígitos
        if len(numero_limpo) >= 4:
            codigo = numero_limpo[-4:]
            print(f"  📍 Extraído código {codigo} de {numero_processo}")
            return codigo
        
        return "0000"
    except Exception as e:
        print(f"  ❌ Erro ao extrair comarca de {numero_processo}: {e}")
        return "0000"
