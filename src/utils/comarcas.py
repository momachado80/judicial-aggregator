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
    "0602": "Guarulhos",
    "0228": "Araraquara",
    "0562": "Tatuí",
    "0050": "Itapetininga",
    "0438": "Mogi-Guaçu",
    "0530": "São Pedro",
    "0224": "Araras"
}

TJBA_COMARCAS = {
    "0001": "Salvador",
    "0002": "Feira de Santana",
    "0003": "Vitória da Conquista"
}

def formatar_numero_cnj(numero: str) -> str:
    """
    Formata número para padrão CNJ
    Entrada: 10368157920248260602 (20 dígitos)
    Saída: 1036815-79.2024.8.26.0602
    """
    # Remove tudo que não é dígito
    digitos = ''.join(c for c in numero if c.isdigit())
    
    # Aplica máscara: NNNNNNN-DD.AAAA.J.TR.OOOO
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
        # Primeiro formata o número
        numero_formatado = formatar_numero_cnj(numero_processo)
        
        # Separa por ponto
        partes = numero_formatado.split('.')
        
        # Último elemento = código comarca
        if len(partes) >= 5:
            codigo = partes[-1]
            return codigo.zfill(4)
        
        return "0000"
    except Exception as e:
        print(f"Erro extrair comarca {numero_processo}: {e}")
        return "0000"
