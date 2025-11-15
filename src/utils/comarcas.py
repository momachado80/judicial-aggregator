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
    "0002": "Santos",
    "0003": "Guarulhos",
    "0127": "Mogi das Cruzes",
    "0223": "Piracicaba",
    "0286": "Ribeirão Preto",
    "0309": "Campinas",
    "0344": "Sorocaba",
    "0361": "São José dos Campos",
    "0477": "Taubaté"
}

TJBA_COMARCAS = {
    "0001": "Salvador",
    "0002": "Feira de Santana",
    "0003": "Vitória da Conquista"
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
    Extrai código comarca do número CNJ
    Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
    Exemplo: 1003711-15.2025.8.26.0650
                                  ^^^^
    """
    try:
        # Separar por ponto
        partes = numero_processo.split('.')
        
        # Último elemento = código comarca
        if len(partes) >= 5:
            codigo = partes[-1]
            return codigo.zfill(4)
        
        return "0000"
    except Exception as e:
        print(f"Erro extrair comarca {numero_processo}: {e}")
        return "0000"
