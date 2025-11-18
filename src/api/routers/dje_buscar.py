"""
Router para busca de processos via DJE (Diário de Justiça Eletrônico)
Precisão absoluta com filtros avançados
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from src.scrapers.dje_downloader import baixar_dje_intervalo, obter_cadernos_por_comarca
from src.scrapers.dje_parser import extrair_processos_dje
from src.database import SessionLocal
from src.models.processo import Processo
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/dje", tags=["DJE"])

class BuscarDJERequest(BaseModel):
    """
    Request para busca no DJE
    """
    data_inicio: str  # DD/MM/YYYY
    data_fim: str     # DD/MM/YYYY
    comarcas: List[str] = ["São Paulo"]
    tipos_processo: List[str] = ["Inventário", "Divórcio"]
    apenas_imoveis: bool = True
    apenas_ativos: bool = True
    valor_min: Optional[float] = None
    valor_max: Optional[float] = None
    salvar_no_banco: bool = True

class BuscarDJEResponse(BaseModel):
    """Response da busca DJE"""
    total_processos: int
    processos: List[dict]
    pdfs_processados: int
    estatisticas: dict

@router.post("/buscar", response_model=BuscarDJEResponse)
async def buscar_processos_dje(request: BuscarDJERequest):
    """
    Busca processos no DJE com precisão absoluta

    Fluxo:
    1. Baixa PDFs do DJE para o intervalo de datas
    2. Faz parsing com filtros precisos (imóveis, ativos, comarca, valor)
    3. Retorna apenas processos que atendem TODOS os critérios
    """
    try:
        print("\n" + "="*80)
        print("🔍 BUSCA DJE INICIADA")
        print("="*80)
        print(f"📅 Período: {request.data_inicio} até {request.data_fim}")
        print(f"📍 Comarcas: {', '.join(request.comarcas)}")
        print(f"📋 Tipos: {', '.join(request.tipos_processo)}")
        print(f"🏠 Apenas imóveis: {request.apenas_imoveis}")
        print(f"✅ Apenas ativos: {request.apenas_ativos}")
        if request.valor_min:
            print(f"💰 Valor mín: R$ {request.valor_min:,.2f}")
        if request.valor_max:
            print(f"💰 Valor máx: R$ {request.valor_max:,.2f}")
        print("="*80)

        # PASSO 1: Baixar PDFs
        print("\n📥 PASSO 1: Baixando PDFs do DJE...")
        pdfs = baixar_dje_intervalo(
            data_inicio=request.data_inicio,
            data_fim=request.data_fim,
            comarcas=request.comarcas,
            headless=True
        )

        if not pdfs:
            raise HTTPException(
                status_code=404,
                detail="Nenhum PDF foi baixado. Verifique as datas e comarcas."
            )

        print(f"✅ {len(pdfs)} PDFs baixados")

        # PASSO 2: Processar cada PDF com filtros
        print("\n🔍 PASSO 2: Processando PDFs com filtros...")
        todos_processos = []
        estatisticas = {
            "pdfs_processados": 0,
            "processos_encontrados": 0,
            "processos_rejeitados": 0,
            "por_tipo": {},
            "por_relevancia": {},
            "por_comarca": {}
        }

        for pdf_path in pdfs:
            if not os.path.exists(pdf_path):
                print(f"⚠️  PDF não encontrado: {pdf_path}")
                continue

            print(f"\n📄 Processando: {os.path.basename(pdf_path)}")

            processos = extrair_processos_dje(
                pdf_path=pdf_path,
                tipos=request.tipos_processo,
                filtrar_imoveis=request.apenas_imoveis,
                filtrar_ativos=request.apenas_ativos,
                comarcas_filtro=request.comarcas if request.comarcas else None,
                valor_min=request.valor_min,
                valor_max=request.valor_max
            )

            todos_processos.extend(processos)
            estatisticas["pdfs_processados"] += 1

        # PASSO 3: Estatísticas
        print("\n📊 PASSO 3: Gerando estatísticas...")
        estatisticas["processos_encontrados"] = len(todos_processos)

        for p in todos_processos:
            # Por tipo
            tipo = p.get("tipo", "Desconhecido")
            estatisticas["por_tipo"][tipo] = estatisticas["por_tipo"].get(tipo, 0) + 1

            # Por relevância
            rel = p.get("relevancia", "Desconhecida")
            estatisticas["por_relevancia"][rel] = estatisticas["por_relevancia"].get(rel, 0) + 1

            # Por comarca
            comarca = p.get("comarca", "Desconhecida")
            estatisticas["por_comarca"][comarca] = estatisticas["por_comarca"].get(comarca, 0) + 1

        # PASSO 4: Salvar no banco (opcional)
        if request.salvar_no_banco and todos_processos:
            print("\n💾 PASSO 4: Salvando no banco de dados...")
            salvos, duplicados = salvar_processos_dje(todos_processos)
            print(f"✅ {salvos} novos processos salvos")
            print(f"🔄 {duplicados} duplicados ignorados")
            estatisticas["salvos_bd"] = salvos
            estatisticas["duplicados_bd"] = duplicados

        # Resultado final
        print("\n" + "="*80)
        print("🎉 BUSCA CONCLUÍDA")
        print("="*80)
        print(f"📊 Total de processos: {len(todos_processos)}")
        print(f"📄 PDFs processados: {estatisticas['pdfs_processados']}")
        print(f"\n📋 Por tipo:")
        for tipo, count in estatisticas["por_tipo"].items():
            print(f"   {tipo}: {count}")
        print(f"\n🎯 Por relevância:")
        for rel, count in estatisticas["por_relevancia"].items():
            print(f"   {rel}: {count}")
        print("="*80)

        return BuscarDJEResponse(
            total_processos=len(todos_processos),
            processos=todos_processos,
            pdfs_processados=estatisticas["pdfs_processados"],
            estatisticas=estatisticas
        )

    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def salvar_processos_dje(processos: List[dict]) -> tuple:
    """
    Salva processos do DJE no banco de dados

    Returns:
        (novos, duplicados)
    """
    db = SessionLocal()
    novos = 0
    duplicados = 0

    try:
        for proc_data in processos:
            numero = proc_data.get("numero")
            if not numero:
                continue

            # Verificar se já existe
            existe = db.query(Processo).filter(
                Processo.numero_processo == numero
            ).first()

            if existe:
                duplicados += 1
                continue

            # Criar novo processo
            processo = Processo(
                numero_processo=numero,
                tribunal="TJSP",
                tipo_processo=proc_data.get("tipo", "Inventário"),
                classe=proc_data.get("classe", ""),
                comarca=proc_data.get("comarca", ""),
                valor_causa=proc_data.get("valor_causa"),
                relevancia=proc_data.get("relevancia", "Média"),
                score_relevancia=proc_data.get("score_relevancia", 0.5),
                partes=proc_data.get("partes", []),
                status="pendente"
            )

            try:
                db.add(processo)
                db.commit()
                novos += 1
            except IntegrityError:
                db.rollback()
                duplicados += 1

    finally:
        db.close()

    return novos, duplicados


@router.get("/comarcas-disponiveis")
async def listar_comarcas_disponiveis():
    """Lista comarcas disponíveis no sistema DJE"""
    from src.scrapers.dje_downloader import COMARCAS_POR_CADERNO

    comarcas = list(COMARCAS_POR_CADERNO.keys())
    return {
        "comarcas": comarcas,
        "total": len(comarcas),
        "exemplo": {
            "capital": ["São Paulo"],
            "interior": ["Piracicaba", "Campinas", "Santos"],
            "raio_50km_sp": ["Guarulhos", "Santo André", "São Bernardo", "Osasco"],
            "raio_50km_piracicaba": ["Limeira", "Rio Claro", "Americana"]
        }
    }


@router.get("/status")
async def status_dje():
    """Status do sistema DJE"""
    pdfs_dir = "data/dje_pdfs"
    pdfs_existentes = []

    if os.path.exists(pdfs_dir):
        pdfs_existentes = [f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]

    return {
        "status": "online",
        "pdfs_cache": len(pdfs_existentes),
        "diretorio": pdfs_dir,
        "ultimos_pdfs": sorted(pdfs_existentes, reverse=True)[:10] if pdfs_existentes else []
    }
