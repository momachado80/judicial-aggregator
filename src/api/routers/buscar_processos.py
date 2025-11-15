from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
from src.utils.comarcas import get_nome_comarca, extrair_codigo_comarca

router = APIRouter()

class BuscarProcessosRequest(BaseModel):
    tribunais: List[str]
    tipos_processo: List[str]
    comarcas: Optional[List[str]] = None
    valor_causa_min: Optional[float] = None
    valor_causa_max: Optional[float] = None
    ano: Optional[int] = None
    quantidade: int = 50

TIPOS_PROCESSO_MAPPING = {
    "Inventário": "289",
    "Divórcio Litigioso": "1107", 
    "Divórcio Consensual": "1108"
}

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

@router.post("/buscar-processos")
async def buscar_processos(request: BuscarProcessosRequest):
    try:
        print(f"🔍 Request: tribunais={request.tribunais}, tipos={request.tipos_processo}, comarcas={request.comarcas}")
        todos_processos = []
        
        for tribunal in request.tribunais:
            for tipo in request.tipos_processo:
                print(f"📋 Buscando: {tribunal} - {tipo}")
                
                tipo_cod = TIPOS_PROCESSO_MAPPING.get(tipo, "289")
                
                url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal.lower()}/_search"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"APIKey {DATAJUD_API_KEY}"
                }
                
                # Query com filtro de tipo
                query = {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"classe.codigo": tipo_cod}}
                            ]
                        }
                    },
                    "size": request.quantidade * 10,
                    "sort": [{"dataAjuizamento": {"order": "desc"}}]
                }
                
                print(f"📡 Chamando {url}")
                response = requests.post(url, headers=headers, json=query, timeout=30)
                
                print(f"📥 Status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"❌ Erro: {response.text[:500]}")
                    continue
                    
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                
                print(f"✅ Encontrados {len(hits)} processos")
                
                for hit in hits:
                    source = hit.get("_source", {})
                    numero = source.get("numeroProcesso", "")
                    
                    if not numero:
                        continue
                    
                    codigo_comarca = extrair_codigo_comarca(numero)
                    nome_comarca = get_nome_comarca(codigo_comarca, tribunal)
                    
                    # Filtrar por comarca
                    if request.comarcas:
                        comarca_match = any(
                            c.lower() in nome_comarca.lower()
                            for c in request.comarcas
                        )
                        if not comarca_match:
                            continue
                    
                    # Filtrar por valor
                    valor_causa = source.get("valorCausa")
                    if request.valor_causa_min and valor_causa:
                        if valor_causa < request.valor_causa_min:
                            continue
                    if request.valor_causa_max and valor_causa:
                        if valor_causa > request.valor_causa_max:
                            continue
                    
                    processo = {
                        "numero": numero,
                        "tribunal": tribunal,
                        "tipo": tipo,
                        "comarca": nome_comarca,
                        "valor_causa": valor_causa,
                        "data_ajuizamento": source.get("dataAjuizamento"),
                        "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/show.do?processo.numero={numero}" if tribunal == "TJSP" else None
                    }
                    
                    todos_processos.append(processo)
                    print(f"  ✅ {nome_comarca} - Total: {len(todos_processos)}")
                    
                    if len(todos_processos) >= request.quantidade:
                        break
                
                if len(todos_processos) >= request.quantidade:
                    break
            
            if len(todos_processos) >= request.quantidade:
                break
        
        print(f"🎉 Retornando {len(todos_processos)} processos")
        return todos_processos[:request.quantidade]
        
    except Exception as e:
        print(f"💥 ERRO: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
