#!/usr/bin/env python3
"""
Busca MASSIVA no DataJud - todos os processos de inventário/divórcio
verificando menção a imóveis
"""
import json
import requests

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

KEYWORDS_IMOVEL = [
    'imóvel', 'imovel', 'matrícula', 'matricula', 'escritura',
    'itcmd', 'itbi', 'registro de imóveis', 'partilha de bens',
    'apartamento', 'casa', 'terreno', 'lote', 'fazenda', 'sítio', 
    'chácara', 'fração ideal', 'condomínio'
]

TIPOS = {39: "Inventário", 12541: "Divórcio Litigioso", 12372: "Divórcio Consensual", 1310: "Arrolamento Sumário"}

def tem_imovel(texto):
    texto_lower = texto.lower()
    return any(kw in texto_lower for kw in KEYWORDS_IMOVEL)

def buscar_tipo(tipo_codigo, quantidade=1000):
    url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
    headers = {"Content-Type": "application/json", "Authorization": f"APIKey {DATAJUD_API_KEY}"}
    
    query = {
        "query": {"term": {"classe.codigo": tipo_codigo}},
        "size": quantidade,
        "sort": [{"dataAjuizamento": {"order": "desc"}}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=query, timeout=60)
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        print(f"  {TIPOS.get(tipo_codigo)}: {len(hits)} processos")
        
        com_imovel = []
        for hit in hits:
            source = hit.get("_source", {})
            numero = source.get("numeroProcesso", "")
            
            texto = " ".join([
                mov.get("nome", "") + " " + mov.get("complemento", "")
                for mov in source.get("movimentos", [])
            ])
            texto += " ".join([a.get("nome", "") for a in source.get("assuntos", [])])
            
            if tem_imovel(texto):
                n = numero
                com_imovel.append({
                    "numero": f"{n[:7]}-{n[7:9]}.{n[9:13]}.{n[13:14]}.{n[14:16]}.{n[16:]}",
                    "tipo": TIPOS.get(tipo_codigo, ""),
                    "tem_imovel": True,
                    "codigo_comarca": numero[-4:],
                    "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={n[:7]}-{n[7:9]}.{n[9:13]}.{n[13:14]}.{n[14:16]}.{n[16:]}"
                })
        
        return com_imovel
    except Exception as e:
        print(f"Erro: {e}")
        return []

def main():
    print("Busca massiva no DataJud (1000 por tipo)...\n")
    
    todos = []
    for tipo_cod in TIPOS.keys():
        resultado = buscar_tipo(tipo_cod, 1000)
        todos.extend(resultado)
        print(f"    -> {len(resultado)} com imóvel\n")
    
    # Remover duplicados e mesclar com existentes
    vistos = set()
    unicos = []
    
    try:
        with open("data/processos_com_imoveis.json", "r") as f:
            for p in json.load(f).get("processos", []):
                if p["numero"] not in vistos:
                    vistos.add(p["numero"])
                    unicos.append(p)
    except:
        pass
    
    for p in todos:
        if p["numero"] not in vistos:
            vistos.add(p["numero"])
            unicos.append(p)
    
    print(f"{'='*50}")
    print(f"TOTAL: {len(unicos)} processos com imóvel")
    print(f"{'='*50}")
    
    resultado = {"total": len(unicos), "processos": unicos}
    with open("data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    with open("src/data/processos_com_imoveis.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
