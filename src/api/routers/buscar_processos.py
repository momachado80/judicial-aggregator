from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
from src.utils.comarcas import get_comarca_nome, extrair_codigo_comarca, formatar_numero_cnj, get_comarca_codigo, get_comarca_codigo

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
    "Inventário": "39",
    "Divórcio Litigioso": "99", 
    "Divórcio Consensual": "98"
}

DATAJUD_API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

@router.post("/buscar-processos")
async def buscar_processos(request: BuscarProcessosRequest):
    try:
        print(f"🔍 Buscando: {request.comarcas}")
        # Expandir "São Paulo" para todos os foros da capital
        from src.utils.comarcas import expandir_sao_paulo
        if request.comarcas:
            request.comarcas = expandir_sao_paulo(request.comarcas)
        todos_processos = []
        codigos_encontrados = {}  # Para ver quais códigos aparecem
        
        for tribunal in request.tribunais:
            for tipo in request.tipos_processo:
                tipo_cod = TIPOS_PROCESSO_MAPPING.get(tipo, "289")
                
                url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal.lower()}/_search"
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"APIKey {DATAJUD_API_KEY}"
                }
                
                must_filters = [
                    {"term": {"classe.codigo": tipo_cod}},
                    {"term": {"tribunal": tribunal}}
                ]
                
                query = {
                    "query": {
                        "bool": {
                            "must": must_filters
                        }
                    },
                    "size": min(request.quantidade, 1000),
                    "sort": [{"dataAjuizamento": {"order": "desc"}}]
                }
                
                response = requests.post(url, headers=headers, json=query, timeout=30)
                
                if response.status_code != 200:
                    print(f"❌ Erro API: {response.status_code}")
                    continue
                    
                data = response.json()
                hits = data.get("hits", {}).get("hits", [])
                
                print(f"✅ API retornou {len(hits)} processos")
                
                for hit in hits:
                    source = hit.get("_source", {})
                    numero = source.get("numeroProcesso", "")
                    
                    if not numero:
                        continue
                    
                    # Extrair comarca
                    codigo_comarca = extrair_codigo_comarca(numero)
                    nome_comarca = get_comarca_nome(codigo_comarca, tribunal)
                    
                    # CONTAR CÓDIGOS
                    if codigo_comarca not in codigos_encontrados:
                        codigos_encontrados[codigo_comarca] = {"nome": nome_comarca, "count": 0}
                    codigos_encontrados[codigo_comarca]["count"] += 1
                    
                    # FILTRO: Se tem comarcas selecionadas
                    if request.comarcas and len(request.comarcas) > 0:
                        comarca_aceita = False
                        
                        for comarca_filtro in request.comarcas:
                            if comarca_filtro.lower() == nome_comarca.lower():
                                comarca_aceita = True
                                break
                        
                        if not comarca_aceita:
                            continue
                    
                    # Filtrar por valor
                    valor_causa = source.get("valorCausa")
                    if request.valor_causa_min and valor_causa:
                        if valor_causa < request.valor_causa_min:
                            continue
                    if request.valor_causa_max and valor_causa:
                        if valor_causa > request.valor_causa_max:
                            continue
                    
                    numero_formatado = formatar_numero_cnj(numero)
                    
                    processo = {
                        "numero": numero,
                        "tribunal": tribunal,
                        "tipo": tipo,
                        "comarca": nome_comarca,
                        "valor_causa": valor_causa,
                        "data_ajuizamento": source.get("dataAjuizamento"),
                        "url_tjsp": f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&numeroDigitoAnoUnificado=&foroNumeroUnificado=&dadosConsulta.valorConsultaNuUnificado={numero_formatado}&dadosConsulta.tipoNuProcesso=UNIFICADO" if tribunal == "TJSP" else None
                    }
                    
                    todos_processos.append(processo)
                    
                    if len(todos_processos) >= request.quantidade:
                        break
                
                if len(todos_processos) >= request.quantidade:
                    break
            
            if len(todos_processos) >= request.quantidade:
                break
        
        # MOSTRAR TOP 20 CÓDIGOS
        print(f"📊 Top 20 códigos de comarca encontrados:")
        sorted_codigos = sorted(codigos_encontrados.items(), key=lambda x: x[1]["count"], reverse=True)
        for codigo, info in sorted_codigos[:20]:
            print(f"   {codigo}: {info['nome']} ({info['count']} processos)")
        
        print(f"🎉 Retornando {len(todos_processos)} processos")
        return todos_processos[:request.quantidade]
        
    except Exception as e:
        print(f"💥 ERRO: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
