"""
Mapeamento completo de códigos de comarca para TJSP e TJBA
"""

TJSP_COMARCAS = {
    "0001": "São Paulo",
    "0019": "Americana",
    "0114": "Campinas",
    "0223": "Piracicaba",
    "0650": "Taboão da Serra",
    "0266": "Itaquaquecetuba",
    "0047": "São Vicente",
    "0002": "Santos",
    "0003": "Guarulhos",
    "0127": "Mogi das Cruzes",
    "0286": "Ribeirão Preto",
    "0602": "Guarulhos",
    "0228": "Araraquara",
    "0562": "Tatuí",
    "0050": "Itapetininga",
    "0438": "Mogi-Guaçu",
    "0530": "São Pedro",
    "0224": "Araras",
    "0152": "Guarulhos",
    "0344": "Sorocaba",
    "0361": "São José dos Campos",
    "0309": "Campinas",
    "0477": "Taubaté"
}

TJBA_COMARCAS = {
    "0001": "Salvador",
    "0002": "Feira de Santana",
    "0003": "Vitória da Conquista"
}

def formatar_numero_cnj(numero: str) -> str:
    """
    Formata número para padrão CNJ
    """
    digitos = ''.join(c for c in numero if c.isdigit())
    
    if len(digitos) == 20:
        return f"{digitos[0:7]}-{digitos[7:9]}.{digitos[9:13]}.{digitos[13]}.{digitos[14:16]}.{digitos[16:20]}"
    
    return numero


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
    """
    try:
        numero_formatado = formatar_numero_cnj(numero_processo)
        partes = numero_formatado.split('.')
        
        if len(partes) >= 5:
            codigo = partes[-1]
            return codigo.zfill(4)
        
        return "0000"
    except Exception as e:
        return "0000"
