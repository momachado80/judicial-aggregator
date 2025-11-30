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
from src.utils.indexador_dje import indexar_todos_pdfs, ler_cache, filtrar_processos_cache, ordenar_processos
from src.database import SessionLocal
from src.models.processo import Processo
from sqlalchemy.exc import IntegrityError

router = APIRouter(tags=["DJE"])

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
        try:
            pdfs = baixar_dje_intervalo(
                data_inicio=request.data_inicio,
                data_fim=request.data_fim,
                comarcas=request.comarcas,
                headless=True
            )
        except NotImplementedError as e:
            # Se estiver no Railway, pular download e tentar usar PDFs existentes
            print(f"⚠️ {e}")
            print("⚠️ Tentando processar apenas PDFs já existentes no cache...")
            pdfs = []
            # Tentar listar PDFs existentes que batem com a data (lógica simplificada)
            # Na verdade, se não baixou, não tem novos. Mas pode ter antigos.
            # Vamos avisar o usuário que o download foi pulado.
            raise HTTPException(
                status_code=501,
                detail=f"Download desabilitado neste ambiente: {str(e)}"
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
    """
    Lista comarcas do TJSP disponíveis para busca

    Retorna:
    - "São Paulo" representa TODOS os foros da capital (26 foros)
    - Comarcas do interior (ex: Piracicaba, Campinas, Santos)

    Total: ~350 comarcas
    """
    from src.utils.comarcas import COMARCAS_TJSP, FOROS_SAO_PAULO_CAPITAL

    # Coletar apenas comarcas do interior (excluir foros da capital)
    comarcas_interior = []

    for codigo, nome in COMARCAS_TJSP.items():
        # Pular foros da capital (serão representados por "São Paulo")
        if codigo in FOROS_SAO_PAULO_CAPITAL:
            continue

        comarcas_interior.append({
            "codigo": codigo,
            "nome": nome,
            "tipo": "interior"
        })

    # Ordenar alfabeticamente
    comarcas_interior.sort(key=lambda x: x["nome"])

    # Adicionar "São Paulo" no início (representa todos os foros)
    comarcas_lista = ["São Paulo"] + [c["nome"] for c in comarcas_interior]

    return {
        "comarcas": comarcas_lista,
        "total": len(comarcas_lista),
        "info": "São Paulo representa todos os 26 foros da capital",
        "exemplos": {
            "capital": ["São Paulo"],
            "grande_sp": ["Guarulhos", "Santo André", "São Bernardo do Campo", "Osasco", "Mogi das Cruzes"],
            "interior": ["Piracicaba", "Campinas", "Santos", "Ribeirão Preto", "Sorocaba"]
        }
    }


@router.post("/baixar-pdfs-periodo")
async def baixar_pdfs_periodo(
    background_tasks: BackgroundTasks,
    data_inicio: str,
    data_fim: str,
    comarcas: List[str] = ["São Paulo", "Piracicaba", "Campinas", "Santos"]
):
    """
    📥 Baixa PDFs de um período específico (ex: 01/01/2024 a 31/01/2024)

    IMPORTANTE: Executa em BACKGROUND. Pode levar HORAS dependendo do período!

    Args:
        data_inicio: Data início (DD/MM/YYYY ou YYYY-MM-DD)
        data_fim: Data fim (DD/MM/YYYY ou YYYY-MM-DD)
        comarcas: Lista de comarcas para baixar

    Exemplo:
        POST /api/dje/baixar-pdfs-periodo
        {
            "data_inicio": "01/01/2024",
            "data_fim": "31/01/2024",
            "comarcas": ["São Paulo", "Piracicaba"]
        }
    """
    from datetime import datetime

    # Converter formato se vier YYYY-MM-DD
    if "-" in data_inicio:
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").strftime("%d/%m/%Y")
    if "-" in data_fim:
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d").strftime("%d/%m/%Y")

    def baixar_em_background():
        """Função que roda em background"""
        try:
            print(f"\n{'='*80}")
            print(f"📥 DOWNLOAD DE PDFs POR PERÍODO")
            print(f"📅 Período: {data_inicio} a {data_fim}")
            print(f"📍 Comarcas: {', '.join(comarcas)}")
            print(f"{'='*80}\n")

            try:
                pdfs_baixados = baixar_dje_intervalo(
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    comarcas=comarcas,
                    headless=True
                )
            except NotImplementedError as e:
                print(f"⚠️ DOWNLOAD CANCELADO: {e}")
                return

            print(f"\n{'='*80}")
            print(f"✅ DOWNLOAD CONCLUÍDO!")
            print(f"📦 Total de PDFs baixados: {len(pdfs_baixados)}")
            print(f"{'='*80}\n")

            # Reindexar automaticamente após baixar
            print("🔄 Reindexando cache...")
            from src.utils.indexador_dje import indexar_todos_pdfs
            cache = indexar_todos_pdfs()
            print(f"✅ Cache atualizado! {cache['total_processos']} processos indexados.")

        except Exception as e:
            print(f"\n❌ ERRO no download: {e}\n")
            import traceback
            traceback.print_exc()

    # Adicionar tarefa em background
    background_tasks.add_task(baixar_em_background)

    # Calcular número aproximado de dias
    try:
        d1 = datetime.strptime(data_inicio, "%d/%m/%Y")
        d2 = datetime.strptime(data_fim, "%d/%m/%Y")
        dias = (d2 - d1).days
    except:
        dias = "?"

    return {
        "status": "iniciado",
        "mensagem": f"Download de PDFs do período {data_inicio} a {data_fim} iniciado em background",
        "periodo": {
            "inicio": data_inicio,
            "fim": data_fim,
            "dias_aproximados": dias
        },
        "comarcas": comarcas,
        "aviso": f"Este processo pode levar várias horas! (~{len(comarcas) * (dias if isinstance(dias, int) else 30)} PDFs)",
        "info": "Após o download, o cache será reindexado automaticamente. Acompanhe o progresso nos logs."
    }


@router.post("/baixar-pdfs-automatico")
async def baixar_pdfs_automatico(
    background_tasks: BackgroundTasks,
    dias: int = 30,
    todas_comarcas: bool = True
):
    """
    ⚠️ DEPRECATED: Use /baixar-pdfs-periodo para maior controle

    Baixa PDFs dos últimos N dias de TODOS os cadernos do TJSP
    """
    from datetime import datetime, timedelta

    # Calcular datas
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=dias)

    data_inicio_str = data_inicio.strftime("%d/%m/%Y")
    data_fim_str = data_fim.strftime("%d/%m/%Y")

    comarcas = ["São Paulo", "Piracicaba", "Campinas", "Santos", "Guarulhos"] if todas_comarcas else ["São Paulo"]

    def baixar_em_background():
        """Função que roda em background"""
        try:
            print(f"\n{'='*80}")
            print(f"🚀 INICIANDO DOWNLOAD AUTOMÁTICO DE PDFs")
            print(f"📅 Período: {data_inicio_str} a {data_fim_str} ({dias} dias)")
            print(f"📍 Comarcas: {', '.join(comarcas)}")
            print(f"{'='*80}\n")

            try:
                pdfs_baixados = baixar_dje_intervalo(
                    data_inicio=data_inicio_str,
                    data_fim=data_fim_str,
                    comarcas=comarcas,
                    headless=True
                )
            except NotImplementedError as e:
                print(f"⚠️ DOWNLOAD CANCELADO: {e}")
                return

            print(f"\n{'='*80}")
            print(f"✅ DOWNLOAD CONCLUÍDO!")
            print(f"📦 Total de PDFs baixados: {len(pdfs_baixados)}")
            print(f"{'='*80}\n")

        except Exception as e:
            print(f"\n❌ ERRO no download em background: {e}\n")

    # Adicionar tarefa em background
    background_tasks.add_task(baixar_em_background)

    return {
        "status": "iniciado",
        "mensagem": f"Download de PDFs dos últimos {dias} dias foi iniciado em background",
        "periodo": {
            "inicio": data_inicio_str,
            "fim": data_fim_str,
            "dias": dias
        },
        "comarcas": comarcas,
        "info": "O download está acontecendo no servidor. Aguarde alguns minutos e verifique os PDFs disponíveis em /api/dje/status"
    }


@router.get("/teste-simples")
async def teste_simples():
    """
    Teste simples: processa 1 PDF sem filtros para verificar se está funcionando
    """
    import os
    from src.scrapers.dje_parser import extrair_processos_dje

    pdfs_dir = "data/dje_pdfs"

    if not os.path.exists(pdfs_dir):
        return {"erro": "Diretório de PDFs não encontrado"}

    # Pegar primeiro PDF disponível (caderno 11 - menor)
    pdfs = sorted([
        os.path.join(pdfs_dir, f)
        for f in os.listdir(pdfs_dir)
        if f.endswith('cad11.pdf')
    ])

    if not pdfs:
        return {"erro": "Nenhum PDF encontrado"}

    pdf_teste = pdfs[0]
    pdf_nome = os.path.basename(pdf_teste)

    try:
        # Processar SEM FILTROS
        processos = extrair_processos_dje(
            pdf_path=pdf_teste,
            tipos=["Inventário", "Divórcio"],
            filtrar_imoveis=False,
            filtrar_ativos=False,
            comarcas_filtro=None
        )

        return {
            "sucesso": True,
            "pdf_testado": pdf_nome,
            "total_processos": len(processos),
            "processos": processos[:5],  # Primeiros 5
            "mensagem": f"Teste OK! Encontrados {len(processos)} processos de Inventário/Divórcio"
        }

    except Exception as e:
        return {
            "sucesso": False,
            "erro": str(e),
            "pdf_testado": pdf_nome
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


class BuscarCacheRequest(BaseModel):
    """Request para busca no cache instantâneo"""
    tipos_processo: List[str] = ["Inventário", "Divórcio"]
    comarcas: Optional[List[str]] = None
    apenas_imoveis: bool = False
    apenas_ativos: bool = True
    valor_min: Optional[float] = None
    valor_max: Optional[float] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None
    ordenar_por: str = "relevancia_desc"

@router.post("/buscar-cache-instantaneo")
async def buscar_cache_instantaneo(request: BuscarCacheRequest):
    """
    🚀 BUSCA INSTANTÂNEA - Usa cache JSON pré-processado
    
    VELOCIDADE: < 100ms (ao invés de 2+ minutos)
    
    Este endpoint lê um arquivo JSON que contém TODOS os processos
    já extraídos dos PDFs. A busca é EXTREMAMENTE RÁPIDA porque
    apenas filtra dados já processados.
    
    IMPORTANTE: O cache precisa ser gerado primeiro com /reindexar
    """
    try:
        cache_path = "data/dje_cache.json"

        # Verificar se cache existe
        print(f"DEBUG: Buscando cache em {os.path.abspath(cache_path)}")
        if not os.path.exists(cache_path):
            print(f"ERROR: Cache file NOT FOUND at {os.path.abspath(cache_path)}")
            # Listar arquivos na pasta data para debug
            if os.path.exists("data"):
                print(f"DEBUG: Conteúdo de data/: {os.listdir('data')}")
            else:
                print(f"DEBUG: Pasta data/ não existe!")
                
            raise HTTPException(
                status_code=404,
                detail="Cache não encontrado. Execute /api/dje/reindexar primeiro para gerar o índice."
            )

        # Ler cache
        cache = ler_cache(cache_path)

        # Filtrar processos (INSTANTÂNEO!)
        processos_filtrados = filtrar_processos_cache(
            cache=cache,
            tipos=request.tipos_processo,
            comarcas=request.comarcas,
            apenas_imoveis=request.apenas_imoveis,
            apenas_ativos=request.apenas_ativos,
            valor_min=request.valor_min,
            valor_max=request.valor_max,
            data_inicio=request.data_inicio,
            data_fim=request.data_fim
        )

        # Ordenar processos (INSTANTÂNEO!)
        processos_filtrados = ordenar_processos(
            processos=processos_filtrados,
            ordenar_por=request.ordenar_por
        )

        # LIMITE DE 100 PROCESSOS PARA BUSCAS ABERTAS
        # "Em comarcas maiores como São Paulo Capital, numa pesquisa aberta,
        # puxe os 100 processos mais recentes"
        total_antes_limite = len(processos_filtrados)
        limite_aplicado = False

        if request.data_inicio is None and request.data_fim is None:
            # Busca aberta (sem filtro de data): limitar a 100 mais recentes
            # Primeiro, ordenar por data para garantir que pegamos os mais recentes
            from datetime import datetime

            def get_data_processo(p):
                data_pdf = p.get("data_pdf", "01-01-2000")
                try:
                    return datetime.strptime(data_pdf, "%d-%m-%Y")
                except:
                    return datetime(2000, 1, 1)

            # Ordenar por data (mais recente primeiro) temporariamente
            processos_ordenados_data = sorted(processos_filtrados, key=get_data_processo, reverse=True)

            # Pegar os 100 mais recentes
            processos_filtrados = processos_ordenados_data[:100]

            # Agora reaplicar a ordenação original escolhida pelo usuário
            processos_filtrados = ordenar_processos(
                processos=processos_filtrados,
                ordenar_por=request.ordenar_por
            )

            limite_aplicado = True

        # Estatísticas
        from collections import Counter
        tipos_count = Counter(p.get("tipo") for p in processos_filtrados)
        relevancia_count = Counter(p.get("relevancia") for p in processos_filtrados)

        # Descrição da ordenação
        ordenacao_desc = {
            "relevancia_desc": "Alta relevância primeiro",
            "relevancia_asc": "Baixa relevância primeiro",
            "data_desc": "Mais recentes primeiro",
            "data_asc": "Mais antigos primeiro",
            "valor_desc": "Maior valor primeiro",
            "valor_asc": "Menor valor primeiro"
        }

        # Mensagem de resultado
        if limite_aplicado:
            mensagem = f"Busca aberta: retornando os 100 processos mais recentes de {total_antes_limite} encontrados."
        else:
            mensagem = f"Busca com filtro de data: {len(processos_filtrados)} processos encontrados."

        return {
            "total_processos": len(processos_filtrados),
            "total_processos_antes_limite": total_antes_limite if limite_aplicado else len(processos_filtrados),
            "limite_aplicado": limite_aplicado,
            "processos": processos_filtrados,
            "pdfs_disponiveis_total": cache["total_pdfs"],
            "pdfs_processados_sucesso": cache["total_pdfs"],
            "data_indexacao": cache["data_indexacao"],
            "ordenacao": {
                "criterio": request.ordenar_por,
                "descricao": ordenacao_desc.get(request.ordenar_por, "Sem ordenação")
            },
            "estatisticas": {
                "por_tipo": dict(tipos_count),
                "por_relevancia": dict(relevancia_count)
            },
            "mensagem": mensagem,
            "cache_info": {
                "total_processos_indexados": cache["total_processos"],
                "total_pdfs_indexados": cache["total_pdfs"]
            }
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindexar")
async def reindexar_pdfs(background_tasks: BackgroundTasks, limite_pdfs: Optional[int] = None):
    """
    Reindexar PDFs e gerar cache JSON

    Args:
        limite_pdfs: Quantidade máxima de PDFs a processar (mais recentes primeiro).
                     None = processar todos.
                     Use 10-15 para evitar problemas de memória no Railway.

    ATENÇÃO: Este processo leva 5-20 minutos dependendo do limite.

    Após a indexação, todas as buscas serão INSTANTÂNEAS!
    """
    def indexar_background():
        try:
            print("\n🚀 Iniciando indexação em background...")
            cache = indexar_todos_pdfs(limite_pdfs=limite_pdfs)
            print(f"✅ Indexação concluída! {cache['total_processos']} processos indexados.")
        except Exception as e:
            print(f"❌ Erro na indexação: {e}")
            import traceback
            traceback.print_exc()

    background_tasks.add_task(indexar_background)

    if limite_pdfs:
        return {
            "status": "iniciado",
            "mensagem": f"Indexação iniciada (limitada a {limite_pdfs} PDFs mais recentes). Isso levará 5-10 minutos.",
            "info": "Acompanhe o progresso nos logs do servidor. Após concluir, use /buscar-cache-instantaneo para buscas rápidas.",
            "modo": "limitado",
            "limite": limite_pdfs
        }
    else:
        return {
            "status": "iniciado",
            "mensagem": "Indexação iniciada em background (TODOS os PDFs). Isso levará 10-20 minutos.",
            "info": "Acompanhe o progresso nos logs do servidor. Após concluir, use /buscar-cache-instantaneo para buscas rápidas.",
            "modo": "completo"
        }


@router.post("/processar-pdfs-cache")
async def processar_pdfs_cache(
    tipos_processo: List[str] = ["Inventário", "Divórcio"],
    comarcas: Optional[List[str]] = None,
    apenas_imoveis: bool = False,
    apenas_ativos: bool = True,
    valor_min: Optional[float] = None,
    valor_max: Optional[float] = None,
    limite_pdfs: int = 1
):
    """
    ⚠️ DEPRECATED: Use /buscar-cache-instantaneo para buscas rápidas

    Este endpoint processa PDFs em tempo real (LENTO - 30s por PDF)
    """
    try:
        pdfs_dir = "data/dje_pdfs"

        if not os.path.exists(pdfs_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Diretório de PDFs não encontrado: {pdfs_dir}"
            )

        # Listar PDFs disponíveis
        todos_pdfs = [
            os.path.join(pdfs_dir, f)
            for f in os.listdir(pdfs_dir)
            if f.endswith('.pdf') and not f.startswith('teste')
        ]

        if not todos_pdfs:
            return {
                "total_processos": 0,
                "processos": [],
                "pdfs_processados": 0,
                "mensagem": "Nenhum PDF encontrado no cache"
            }

        # Ordenar por data (mais recente primeiro) e aplicar limite
        todos_pdfs.sort(reverse=True)
        pdfs_disponiveis = todos_pdfs[:limite_pdfs]

        print(f"\n📁 Processando {len(pdfs_disponiveis)} de {len(todos_pdfs)} PDFs disponíveis...")

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
            "pdfs_disponiveis_total": len(todos_pdfs),
            "pdfs_processados": len(pdfs_disponiveis),
            "pdfs_processados_sucesso": pdfs_processados_sucesso,
            "pdfs_com_erro": len(pdfs_com_erro),
            "erros": pdfs_com_erro if pdfs_com_erro else None,
            "estatisticas": {
                "por_tipo": dict(tipos_count),
                "por_relevancia": dict(relevancia_count)
            },
            "mensagem": f"Processados {len(pdfs_disponiveis)} PDFs mais recentes de {len(todos_pdfs)} disponíveis"
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
