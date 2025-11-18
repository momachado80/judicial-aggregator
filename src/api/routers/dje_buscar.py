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
    """Status do sistema DJE com diagnóstico detalhado"""
    import os
    from pathlib import Path

    pdfs_dir = "data/dje_pdfs"
    pdfs_existentes = []
    diagnostico = {}

    # Verificar se está em modo Railway (sem Playwright)
    railway_mode = os.getenv("RAILWAY_DEPLOY", "false") == "true"

    # Diagnóstico detalhado do filesystem
    try:
        cwd = os.getcwd()
        diagnostico["current_working_directory"] = cwd
        diagnostico["data_dir_exists"] = os.path.exists("data")
        diagnostico["data_dir_absolute_path"] = os.path.abspath("data")
        diagnostico["pdfs_dir_exists"] = os.path.exists(pdfs_dir)
        diagnostico["pdfs_dir_absolute_path"] = os.path.abspath(pdfs_dir)

        # Listar conteúdo do diretório data se existir
        if os.path.exists("data"):
            diagnostico["data_dir_contents"] = os.listdir("data")
        else:
            diagnostico["data_dir_contents"] = []

        # Listar PDFs se o diretório existir
        if os.path.exists(pdfs_dir):
            all_files = os.listdir(pdfs_dir)
            pdfs_existentes = [f for f in all_files if f.endswith('.pdf')]
            diagnostico["all_files_in_pdfs_dir"] = all_files[:20]  # Primeiros 20

            # Verificar tamanho dos arquivos
            if pdfs_existentes:
                sample_pdf = os.path.join(pdfs_dir, pdfs_existentes[0])
                diagnostico["sample_pdf_size_bytes"] = os.path.getsize(sample_pdf)

    except Exception as e:
        diagnostico["error"] = str(e)

    return {
        "status": "online",
        "modo": "railway" if railway_mode else "local",
        "download_disponivel": not railway_mode,
        "pdfs_cache": len(pdfs_existentes),
        "diretorio": pdfs_dir,
        "ultimos_pdfs": sorted(pdfs_existentes, reverse=True)[:10] if pdfs_existentes else [],
        "diagnostico": diagnostico
    }


@router.post("/processar-pdfs-cache")
async def processar_pdfs_cache(
    tipos_processo: List[str] = ["Inventário", "Divórcio"],
    comarcas: Optional[List[str]] = None,
    apenas_imoveis: bool = True,
    apenas_ativos: bool = True,
    valor_min: Optional[float] = None,
    valor_max: Optional[float] = None
):
    """
    Processa PDFs que já estão em cache (data/dje_pdfs/)

    IDEAL PARA PRODUÇÃO NO RAILWAY - não precisa de Playwright!

    Este endpoint processa PDFs que foram:
    - Baixados localmente e commitados no repo
    - Previamente baixados e salvos no servidor
    - Enviados via upload (futuro)
    """
    try:
        pdfs_dir = "data/dje_pdfs"

        if not os.path.exists(pdfs_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Diretório de PDFs não encontrado: {pdfs_dir}"
            )

        # Listar PDFs disponíveis
        pdfs_disponiveis = [
            os.path.join(pdfs_dir, f)
            for f in os.listdir(pdfs_dir)
            if f.endswith('.pdf')
        ]

        if not pdfs_disponiveis:
            return {
                "total_processos": 0,
                "processos": [],
                "pdfs_processados": 0,
                "mensagem": "Nenhum PDF encontrado no cache"
            }

        print(f"\n📁 Processando {len(pdfs_disponiveis)} PDFs do cache...")

        # Processar cada PDF
        todos_processos = []
        pdfs_com_erro = []
        pdfs_processados_sucesso = 0

        for pdf_path in pdfs_disponiveis:
            pdf_nome = os.path.basename(pdf_path)
            print(f"\n📄 {pdf_nome}")

            try:
                processos = extrair_processos_dje(
                    pdf_path=pdf_path,
                    tipos=tipos_processo,
                    filtrar_imoveis=apenas_imoveis,
                    filtrar_ativos=apenas_ativos,
                    comarcas_filtro=comarcas,
                    valor_min=valor_min,
                    valor_max=valor_max
                )
                todos_processos.extend(processos)
                pdfs_processados_sucesso += 1
                print(f"  ✅ {len(processos)} processos encontrados")

            except Exception as e:
                erro_msg = f"{pdf_nome}: {str(e)}"
                pdfs_com_erro.append(erro_msg)
                print(f"  ⚠️ ERRO ao processar: {str(e)}")
                continue

        # Estatísticas
        from collections import Counter
        tipos_count = Counter(p.get("tipo") for p in todos_processos)
        relevancia_count = Counter(p.get("relevancia") for p in todos_processos)

        return {
            "total_processos": len(todos_processos),
            "processos": todos_processos,
            "pdfs_total": len(pdfs_disponiveis),
            "pdfs_processados_sucesso": pdfs_processados_sucesso,
            "pdfs_com_erro": len(pdfs_com_erro),
            "erros": pdfs_com_erro if pdfs_com_erro else None,
            "estatisticas": {
                "por_tipo": dict(tipos_count),
                "por_relevancia": dict(relevancia_count)
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
