#!/usr/bin/env python3
"""
Carga inicial de processos de múltiplas comarcas
Baixa PDFs de um período maior (último mês) para popular o sistema
"""
import os
import json
from datetime import datetime, timedelta
from src.scrapers.dje_downloader import baixar_dje_intervalo
from src.scrapers.dje_parser import extrair_processos_dje

def main():
    print("="*80)
    print("🚀 CARGA INICIAL - Múltiplas Comarcas")
    print("="*80)

    # Últimos 30 dias
    hoje = datetime.now()
    um_mes_atras = hoje - timedelta(days=30)

    data_inicio = um_mes_atras.strftime("%d/%m/%Y")
    data_fim = hoje.strftime("%d/%m/%Y")

    # Comarcas principais do Estado de São Paulo
    comarcas = [
        "São Paulo",      # Capital
        "Guarulhos",      # Grande SP
        "Campinas",       # Interior
        "Santos",         # Litoral
        "São Bernardo do Campo",  # Grande SP
        "Santo André",    # Grande SP
        "Osasco",         # Grande SP
        "Ribeirão Preto", # Interior
        "Sorocaba",       # Interior
        "Piracicaba",     # Interior
        "Bauru",          # Interior
        "São José dos Campos",  # Vale do Paraíba
        "Jundiaí",        # Interior
        "Mogi das Cruzes" # Grande SP
    ]

    print(f"\n📅 Período: {data_inicio} até {data_fim} (últimos 30 dias)")
    print(f"📍 Comarcas ({len(comarcas)}): {', '.join(comarcas)}")
    print(f"📚 Cadernos: 11, 12, 13, 14 (Capital + Interior)")
    print(f"\n⚠️  ATENÇÃO: Este processo pode levar 4-6 horas!\n")

    resposta = input("Deseja continuar? (s/N): ")
    if resposta.lower() != 's':
        print("Cancelado.")
        return

    # PASSO 1: Baixar PDFs
    print("\n📥 PASSO 1: Baixando PDFs de múltiplas comarcas...\n")

    try:
        pdfs = baixar_dje_intervalo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            comarcas=comarcas,
            headless=True
        )
        print(f"\n✅ {len(pdfs)} PDFs baixados")
    except Exception as e:
        print(f"\n⚠️  Erro ao baixar PDFs: {e}")
        print("Continuando com PDFs existentes...")
        pdfs = []

    # PASSO 2: Processar TODOS os PDFs (inicial)
    print(f"\n📄 PASSO 2: Processando TODOS os PDFs...\n")

    pdfs_dir = "data/dje_pdfs"
    todos_pdf_files = sorted([
        os.path.join(pdfs_dir, f)
        for f in os.listdir(pdfs_dir)
        if f.endswith('.pdf')
    ]) if os.path.exists(pdfs_dir) else []

    print(f"📁 Total de PDFs encontrados: {len(todos_pdf_files)}")

    todos_processos = []
    for i, pdf_path in enumerate(todos_pdf_files, 1):
        print(f"[{i}/{len(todos_pdf_files)}] {os.path.basename(pdf_path)}")

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

            todos_processos.extend(processos)
            print(f"   ✅ {len(processos)} processos\n")

        except Exception as e:
            print(f"   ❌ Erro: {e}\n")

    print(f"\n✅ {len(todos_processos)} processos extraídos no total")

    # PASSO 3: Salvar cache
    print(f"\n💾 PASSO 3: Salvando cache...\n")

    cache_path = "data/dje_cache.json"

    cache = {
        'total_processos': len(todos_processos),
        'total_pdfs': len(todos_pdf_files),
        'processos': todos_processos,
        'data_indexacao': datetime.now().isoformat(),
        'ultima_atualizacao': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"✅ Cache salvo: {cache_path}")

    # Estatísticas
    from collections import Counter
    tipos_count = Counter(p['tipo'] for p in todos_processos)
    comarcas_count = Counter(p.get('comarca', 'Desconhecida') for p in todos_processos)

    print("\n" + "="*80)
    print("📊 ESTATÍSTICAS FINAIS")
    print("="*80)
    print(f"📄 Total de PDFs: {len(todos_pdf_files)}")
    print(f"⚖️  Total de processos: {len(todos_processos)}")

    print(f"\n📋 Distribuição por tipo:")
    for tipo, count in sorted(tipos_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   {tipo}: {count}")

    print(f"\n📍 Top 10 comarcas:")
    for comarca, count in comarcas_count.most_common(10):
        print(f"   {comarca}: {count}")

    print("="*80)
    print("\n✅ Carga inicial concluída!")
    print("Agora o sistema tem processos de múltiplas comarcas.")
    print("A atualização diária manterá o cache sempre atualizado.\n")

if __name__ == "__main__":
    main()
