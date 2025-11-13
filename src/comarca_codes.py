"""Mapeamento de comarcas para códigos CNJ"""

COMARCAS_TJSP = {
    "São Paulo": "0090", "Campinas": "0114", "Santos": "0127",
    "São Bernardo do Campo": "0129", "Santo André": "0130",
    "Ribeirão Preto": "0131", "Sorocaba": "0132", "Guarulhos": "0133",
    "Osasco": "0134", "Mauá": "0135", "Diadema": "0136",
    "Piracicaba": "0137", "Carapicuíba": "0138", "Bauru": "0139",
    "São José dos Campos": "0140", "Franca": "0141", "Jundiaí": "0142",
    "Limeira": "0143", "Suzano": "0144", "Taboão da Serra": "0145",
    "Sumaré": "0146", "Americana": "0019", "Araraquara": "0021",
    "Araçatuba": "0020", "Assis": "0023", "Avaré": "0024",
    "Barretos": "0027", "Birigui": "0030", "Botucatu": "0032",
    "Bragança Paulista": "0033", "Catanduva": "0037", "Cruzeiro": "0040",
    "Fernandópolis": "0046", "Guaratinguetá": "0049", "Indaiatuba": "0055",
    "Itapetininga": "0056", "Itapeva": "0057", "Itu": "0058",
    "Jaboticabal": "0059", "Jacareí": "0060", "Jales": "0061",
    "Jaú": "0062", "Leme": "0067", "Lins": "0068", "Marília": "0070",
    "Matão": "0071", "Mococa": "0073", "Mogi das Cruzes": "0074",
    "Mogi Guaçu": "0075", "Olímpia": "0078", "Ourinhos": "0079",
    "Penápolis": "0081", "Pindamonhangaba": "0083",
    "Presidente Prudente": "0085", "Rio Claro": "0088",
    "Santa Bárbara d'Oeste": "0095", "São Carlos": "0096",
    "São João da Boa Vista": "0097", "São José do Rio Preto": "0098",
    "Sertãozinho": "0100", "Taquaritinga": "0103", "Tatuí": "0104",
    "Taubaté": "0105", "Tupã": "0107", "Votuporanga": "0110"
}

COMARCAS_TJBA = {
    "Salvador": "0001", "Feira de Santana": "0002",
    "Vitória da Conquista": "0003", "Camaçari": "0004",
    "Itabuna": "0005", "Juazeiro": "0006", "Lauro de Freitas": "0007",
    "Ilhéus": "0008", "Jequié": "0009", "Alagoinhas": "0010",
    "Barreiras": "0011", "Paulo Afonso": "0012",
    "Santo Antônio de Jesus": "0013", "Valença": "0014",
    "Simões Filho": "0015", "Teixeira de Freitas": "0016",
    "Candeias": "0017", "Jacobina": "0018", "Eunápolis": "0019",
    "Senhor do Bonfim": "0020", "Porto Seguro": "0021",
    "Brumado": "0022", "Guanambi": "0023", "Santo Amaro": "0024",
    "Serrinha": "0025", "Irecê": "0026", "Cruz das Almas": "0027",
    "Conceição do Coité": "0028", "Bom Jesus da Lapa": "0029",
    "Dias d'Ávila": "0030"
}

def get_comarca_code(comarca_nome, tribunal):
    comarca_nome_clean = comarca_nome.strip().title()
    if tribunal == "TJSP":
        return COMARCAS_TJSP.get(comarca_nome_clean)
    elif tribunal == "TJBA":
        return COMARCAS_TJBA.get(comarca_nome_clean)
    return None

def get_tribunal_code(tribunal):
    return {"TJSP": "26", "TJBA": "05"}.get(tribunal)

def build_processo_pattern(comarca_nome, tribunal):
    comarca_code = get_comarca_code(comarca_nome, tribunal)
    if not comarca_code:
        return None
    tribunal_code = get_tribunal_code(tribunal)
    return f"*8.{tribunal_code}.{comarca_code}"

def get_all_comarcas(tribunal=None):
    if tribunal == "TJSP":
        return COMARCAS_TJSP.copy()
    elif tribunal == "TJBA":
        return COMARCAS_TJBA.copy()
    else:
        all_comarcas = {}
        all_comarcas.update({f"{k} (SP)": v for k, v in COMARCAS_TJSP.items()})
        all_comarcas.update({f"{k} (BA)": v for k, v in COMARCAS_TJBA.items()})
        return all_comarcas
