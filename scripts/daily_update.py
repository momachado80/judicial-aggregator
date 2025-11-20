#!/usr/bin/env python3
"""
Atualização diária automática do DJE
Baixa PDFs dos últimos 3 dias e atualiza o cache
"""
import os
import json
from datetime import datetime, timedelta
from src.scrapers.dje_downloader import baixar_dje_intervalo
from src.scrapers.dje_parser import extrair_processos_dje

def main():
    print("="*80)
    print("🤖 ATUALIZAÇÃO DIÁRIA AUTOMÁTICA DO DJE")
    print("="*80)

    # Calcular últimos 3 dias (incluindo hoje)
    hoje = datetime.now()
    tres_dias_atras = hoje - timedelta(days=3)

    data_inicio = tres_dias_atras.strftime("%d/%m/%Y")
    data_fim = hoje.strftime("%d/%m/%Y")

    # Comarcas principais (Capital + Interior)
    comarcas = [
        "São Paulo",      # Capital
        "Guarulhos",      # Grande SP
        "Campinas",       # Interior
        "Santos",         # Litoral
        "Ribeirão Preto", # Interior
        "Sorocaba",       # Interior
        "Piracicaba"      # Interior
    ]

    print(f"\n📅 Período: {data_inicio} até {data_fim}")
    print(f"📍 Comarcas: {', '.join(comarcas)}")
    print(f"📚 Cadernos: 11, 12, 13, 14 (Capital + Interior)\n")

    # PASSO 1: Baixar PDFs dos últimos 3 dias (Capital + Interior)
    print("📥 PASSO 1: Baixando PDFs...\n")

    try:
        pdfs = baixar_dje_intervalo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            comarcas=comarcas,  # Capital + Interior
            headless=True
        )
        print(f"\n✅ {len(pdfs)} PDFs baixados")
    except Exception as e:
        print(f"\n⚠️  Erro ao baixar PDFs: {e}")
        print("Continuando com PDFs existentes...")
        pdfs = []

    # PASSO 2: Processar novos PDFs
    print(f"\n📄 PASSO 2: Processando novos PDFs...\n")

    novos_processos = []
    for pdf_path in pdfs:
        if not os.path.exists(pdf_path):
            continue

        print(f"   Processando {os.path.basename(pdf_path)}...")

        try:
            processos = extrair_processos_dje(
                pdf_path,
                tipos=['Inventário', 'Divórcio', 'Arrolamento'],
                filtrar_imoveis=False,
                filtrar_ativos=True
            )

            # Adicionar data do PDF
            pdf_basename = os.path.basename(pdf_path)
            data_pdf = pdf_basename.split('_')[1]
            for p in processos:
                p['data_pdf'] = data_pdf

            novos_processos.extend(processos)
            print(f"      ✅ {len(processos)} processos")

        except Exception as e:
            print(f"      ❌ Erro: {e}")

    print(f"\n✅ {len(novos_processos)} novos processos extraídos")

    # PASSO 3: Atualizar cache (merge com processos existentes)
    print(f"\n💾 PASSO 3: Atualizando cache...\n")

    cache_path = "data/dje_cache.json"

    # Carregar cache existente
    processos_existentes = []
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_existente = json.load(f)
                processos_existentes = cache_existente.get('processos', [])
                print(f"   📦 Cache existente: {len(processos_existentes)} processos")
        except Exception as e:
            print(f"   ⚠️  Erro ao ler cache: {e}")

    # Merge: adicionar apenas processos novos (evitar duplicatas)
    numeros_existentes = {p['numero'] for p in processos_existentes}
    processos_realmente_novos = [
        p for p in novos_processos
        if p['numero'] not in numeros_existentes
    ]

    # Combinar
    todos_processos = processos_existentes + processos_realmente_novos

    print(f"   ➕ Processos novos adicionados: {len(processos_realmente_novos)}")
    print(f"   📊 Total no cache: {len(todos_processos)}")

    # Contar PDFs únicos
    pdfs_dir = "data/dje_pdfs"
    total_pdfs = len([f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]) if os.path.exists(pdfs_dir) else 0

    # Salvar cache atualizado
    cache_atualizado = {
        'total_processos': len(todos_processos),
        'total_pdfs': total_pdfs,
        'processos': todos_processos,
        'data_indexacao': datetime.now().isoformat(),
        'ultima_atualizacao': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache_atualizado, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Cache salvo: {cache_path}")

    # Estatísticas
    from collections import Counter
    tipos_count = Counter(p['tipo'] for p in todos_processos)

    print("\n" + "="*80)
    print("📊 ESTATÍSTICAS FINAIS")
    print("="*80)
    print(f"📄 Total de PDFs: {total_pdfs}")
    print(f"⚖️  Total de processos: {len(todos_processos)}")
    print(f"🆕 Novos processos hoje: {len(processos_realmente_novos)}")
    print(f"\n📋 Distribuição por tipo:")
    for tipo, count in sorted(tipos_count.items()):
        print(f"   {tipo}: {count}")
    print("="*80)

if __name__ == "__main__":
    main()
