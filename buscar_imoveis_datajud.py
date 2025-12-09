#!/usr/bin/env python3
"""
Busca processos de inventário/divórcio no DataJud e verifica menção a imóveis nos movimentos
"""
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

KEYWORDS_IMOVEL = [
    'imóvel', 'imovel', 'imóveis', 'imoveis',
    'matrícula', 'matricula', 'escritura',
    'itcmd', 'itbi', 'registro de imóveis',
    'partilha de bens', 'bem imóvel', 'bens imóveis',
    'apartamento', 'casa', 'terreno', 'lote',
    'fazenda', 'sítio', 'sitio', 'chácara', 'chacara',
    'fração ideal', 'fracao ideal', 'condomínio', 'condominio'
]

TIPOS = {
    39: "Inventário",
    12541: "Divórcio Litigioso",
    12372: "Divórcio Consensual",
    1310: "Arrolamento Sumário",
    1311: "Arrolamento Comum"
}

COMARCAS_IMPORTANTES = [
    "0100",  # São Paulo - Foro Central
    "0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009", "0010",  # Foros regionais SP
    "0114",  # Campinas
    "0577",  # São José dos Campos  
    "0576",  # Santos
    "0554",  # Ribeirão Preto
    "0451",  # Piracicaba
    "0405",  # Osasco
    "0362",  # Mogi das Cruzes
    "0224",  # Guarulhos
]

def tem_imovel(texto):
    texto_lower = texto.lower()
    for kw in KEYWORDS_IMOVEL:
        if kw in texto_lower:
            return True
    return False

def buscar_por_tipo_comarca(tipo_codigo, comarca_codigo):
    url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"APIKey {DATAJUD_API_KEY}"
    }
    
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"classe.codigo": tipo_codigo}},
                    {"wildcard": {"numeroProcesso": f"*{comarca_codigo}"}}
                ]
            }
        },
        "size": 200,
        "sort": [{"dataAjuizamento": {"order": "desc"}}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=query, timeout=30)
        if response.status_code != 200:
            return []
        
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        processos_com_imovel = []
        
        for hit in hits:
            source = hit.get("_source", {})
            numero = source.get("numeroProcesso", "")
            
            # Concatenar todos os textos de movimentos
            texto_movimentos = ""
            for mov in source.get("movimentos", []):
                texto_movimentos += mov.get("nome", "") + " "
                texto_movimentos += mov.get("complemento", "") + " "
            
            # Adicionar assuntos
            for assunto in source.get("assuntos", []):
                texto_movimentos += assunto.get("nome", "") + " "
            
            if tem_imovel(texto_movimentos):
                codigo_comarca = numero[-4:] if len(numero) >= 4 else ""
                n = numero
                processos_com_imovel.append({
                    "numero": f"{n[:7]}-{n[7:9]}.{n[9:13]}.{n[13:14]}.{n[14:16]}.{n[16:]}",
                    "tipo": TIPOS.get(tipo_codigo, ""),
                    "tem_imovel": True,
                    "codigo_comarca": codigo_comarca,
                    "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={n[:7]}-{n[7:9]}.{n[9:13]}.{n[13:14]}.{n[14:16]}.{n[16:]}"
                })
        
        return processos_com_imovel
    except Exception as e:
        print(f"Erro {tipo_codigo}/{comarca_codigo}: {e}")
        return []


def main():
    print("Buscando processos com imóveis no DataJud...")
    
    todos = []
    total_buscas = len(TIPOS) * len(COMARCAS_IMPORTANTES)
    busca_atual = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for tipo_cod in TIPOS.keys():
            for comarca in COMARCAS_IMPORTANTES:
                futures.append(executor.submit(buscar_por_tipo_comarca, tipo_cod, comarca))
        
        for future in as_completed(futures):
            busca_atual += 1
            resultado = future.result()
            todos.extend(resultado)
            if busca_atual % 20 == 0:
                print(f"Buscas: {busca_atual}/{total_buscas} | Encontrados: {len(todos)}")
    
    # Remover duplicados
    vistos = set()
    unicos = []
    for p in todos:
        if p["numero"] not in vistos:
            vistos.add(p["numero"])
            unicos.append(p)
    
    print(f"\n{'='*60}")
    print(f"RESULTADO:")
    print(f"  Total com menção a imóvel: {len(unicos)}")
    print(f"{'='*60}")
    
    # Carregar existentes e mesclar
    try:
        with open("data/processos_com_imoveis.json", "r") as f:
            existentes = json.load(f)
            for p in existentes.get("processos", []):
                if p["numero"] not in vistos:
                    vistos.add(p["numero"])
                    unicos.append(p)
    except:
        pass
    
    # Salvar
    resultado = {"total": len(unicos), "processos": unicos}
    
    with open("data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    with open("src/data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    print(f"Arquivo atualizado com {len(unicos)} processos!")
    
    print(f"\nExemplos:")
    for p in unicos[:10]:
        print(f"  {p['numero']} | {p['tipo']}")

if __name__ == "__main__":
    main()
