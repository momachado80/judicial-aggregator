#!/usr/bin/env python3
"""
Busca processos de inventário/divórcio com ALTO VALOR DA CAUSA
(proxy para processos com patrimônio significativo)
"""
import json
import requests

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

TIPOS = {
    39: "Inventário", 
    12541: "Divórcio Litigioso", 
    12372: "Divórcio Consensual",
    1310: "Arrolamento Sumário"
}

VALOR_MINIMO = 100000  # R$ 100.000

def buscar_tipo(tipo_codigo):
    url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search"
    headers = {"Content-Type": "application/json", "Authorization": f"APIKey {DATAJUD_API_KEY}"}
    
    # Buscar processos com valor da causa >= R$ 100.000
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"classe.codigo": tipo_codigo}},
                    {"range": {"valorCausa": {"gte": VALOR_MINIMO}}}
                ]
            }
        },
        "size": 1000,
        "sort": [{"valorCausa": {"order": "desc"}}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=query, timeout=60)
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        
        print(f"  {TIPOS.get(tipo_codigo)}: {len(hits)} processos com valor >= R$ {VALOR_MINIMO:,}")
        
        processos = []
        for hit in hits:
            source = hit.get("_source", {})
            numero = source.get("numeroProcesso", "")
            valor = source.get("valorCausa", 0)
            
            # Verificar se não está extinto
            movimentos = source.get("movimentos", [])
            if movimentos:
                ultimo = sorted(movimentos, key=lambda m: m.get("dataHora", ""), reverse=True)[0]
                nome_mov = ultimo.get("nome", "").lower()
                if nome_mov == "definitivo" or "baixa definitiva" in nome_mov:
                    continue
            
            n = numero
            processos.append({
                "numero": f"{n[:7]}-{n[7:9]}.{n[9:13]}.{n[13:14]}.{n[14:16]}.{n[16:]}",
                "tipo": TIPOS.get(tipo_codigo, ""),
                "valor_causa": valor,
                "codigo_comarca": numero[-4:],
                "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={n[:7]}-{n[7:9]}.{n[9:13]}.{n[13:14]}.{n[14:16]}.{n[16:]}"
            })
        
        return processos
    except Exception as e:
        print(f"Erro: {e}")
        return []

def main():
    print(f"Buscando processos com valor da causa >= R$ {VALOR_MINIMO:,}...\n")
    
    todos = []
    for tipo_cod in TIPOS.keys():
        processos = buscar_tipo(tipo_cod)
        todos.extend(processos)
    
    # Remover duplicados
    vistos = set()
    unicos = []
    for p in todos:
        if p["numero"] not in vistos:
            vistos.add(p["numero"])
            unicos.append(p)
    
    # Ordenar por valor
    unicos.sort(key=lambda x: x.get("valor_causa", 0), reverse=True)
    
    print(f"\n{'='*60}")
    print(f"RESULTADO:")
    print(f"  Total processos com alto valor: {len(unicos)}")
    print(f"{'='*60}")
    
    # Salvar
    resultado = {"total": len(unicos), "processos": unicos}
    with open("data/processos_alto_valor.json", "w") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    print(f"\nTop 15 por valor:")
    for p in unicos[:15]:
        print(f"  R$ {p['valor_causa']:>12,.2f} | {p['tipo']:20} | {p['numero']}")

if __name__ == "__main__":
    main()
