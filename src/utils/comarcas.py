
def extrair_codigo_comarca(numero_processo):
    """Extrai código da comarca do número CNJ (posições 16-20)"""
    numero_limpo = ''.join(filter(str.isdigit, str(numero_processo)))
    if len(numero_limpo) >= 20:
        return numero_limpo[16:20]
    return None

def formatar_numero_cnj(numero):
    """Formata número no padrão CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO"""
    numero_limpo = ''.join(filter(str.isdigit, str(numero)))
    if len(numero_limpo) == 20:
        return f"{numero_limpo[0:7]}-{numero_limpo[7:9]}.{numero_limpo[9:13]}.{numero_limpo[13]}.{numero_limpo[14:16]}.{numero_limpo[16:20]}"
    return numero
