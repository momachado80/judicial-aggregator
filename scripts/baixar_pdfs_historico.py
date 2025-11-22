"""
Script para baixar PDFs históricos do DJE TJSP (Caderno 12)

Baixa PDFs dos últimos 2-4 anos para ter uma base de dados completa.
PDFs ficam apenas localmente, não são commitados no Git.
"""
import os
import sys
from datetime import datetime, timedelta
from src.scrapers.dje_downloader import baixar_dje_tjsp

def gerar_dias_uteis(data_inicio, data_fim):
    """Gera lista de dias úteis (seg-sex) entre duas datas"""
    dias_uteis = []
    data_atual = data_inicio

    while data_atual <= data_fim:
        # 0 = segunda, 6 = domingo
        if data_atual.weekday() < 5:  # Segunda a sexta
            dias_uteis.append(data_atual.strftime("%d/%m/%Y"))
        data_atual += timedelta(days=1)

    return dias_uteis

def baixar_historico(anos=2, caderno="12", continuar_de=None):
    """
    Baixa PDFs históricos do DJE

    Args:
        anos: Quantos anos para trás baixar (2 ou 4)
        caderno: Código do caderno (12 = Capital Parte I)
        continuar_de: Data para continuar download (formato DD/MM/YYYY)
    """
    # Calcular período
    hoje = datetime.now()
    data_fim = hoje
    data_inicio = hoje - timedelta(days=anos * 365)

    print("="*80)
    print(f"📥 DOWNLOAD DE PDFs HISTÓRICOS - DJE TJSP")
    print("="*80)
    print(f"📅 Período: {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}")
    print(f"📚 Caderno: {caderno}")
    print(f"⏱️  Isso pode levar HORAS (há centenas de PDFs)")
    print("="*80)

    # Gerar lista de dias úteis
    dias_uteis = gerar_dias_uteis(data_inicio, data_fim)
    print(f"\n📊 {len(dias_uteis)} dias úteis encontrados")

    # Se continuar de uma data específica, pular anteriores
    if continuar_de:
        idx = dias_uteis.index(continuar_de) if continuar_de in dias_uteis else 0
        dias_uteis = dias_uteis[idx:]
        print(f"▶️  Continuando de {continuar_de} ({len(dias_uteis)} dias restantes)")

    # Verificar quais já foram baixados
    pdfs_existentes = set(os.listdir("data/dje_pdfs")) if os.path.exists("data/dje_pdfs") else set()

    sucessos = 0
    erros = 0
    pulados = 0

    for i, data in enumerate(dias_uteis, 1):
        # Verificar se já existe
        filename = f"dje_{data.replace('/', '-')}_cad{caderno}.pdf"
        if filename in pdfs_existentes:
            print(f"[{i}/{len(dias_uteis)}] ⏩ {data} - já existe")
            pulados += 1
            continue

        try:
            print(f"\n[{i}/{len(dias_uteis)}] 📥 Baixando {data}...")
            baixar_dje_tjsp(data, caderno=caderno, headless=True)
            sucessos += 1

            # A cada 10 PDFs, mostrar progresso
            if sucessos % 10 == 0:
                print(f"\n📊 Progresso: {sucessos} baixados, {erros} erros, {pulados} pulados")

        except KeyboardInterrupt:
            print(f"\n\n⚠️  Download interrompido pelo usuário")
            print(f"📊 Resumo parcial:")
            print(f"   ✅ {sucessos} PDFs baixados com sucesso")
            print(f"   ❌ {erros} erros")
            print(f"   ⏩ {pulados} já existiam")
            print(f"\n💡 Para continuar de onde parou, execute:")
            print(f"   python scripts/baixar_pdfs_historico.py --continuar-de {data}")
            sys.exit(0)

        except Exception as e:
            print(f"   ❌ Erro: {e}")
            erros += 1

            # Se muitos erros seguidos, pausar
            if erros > 5 and sucessos == 0:
                print(f"\n⚠️  Muitos erros consecutivos. Verifique sua conexão.")
                break

            continue

    # Resumo final
    print("\n" + "="*80)
    print("✅ DOWNLOAD CONCLUÍDO!")
    print("="*80)
    print(f"✅ {sucessos} PDFs baixados com sucesso")
    print(f"❌ {erros} erros")
    print(f"⏩ {pulados} já existiam")
    print(f"📊 Total de PDFs: {sucessos + pulados}")
    print("="*80)

    print(f"\n💡 Próximo passo: Indexar os PDFs")
    print(f"   python -m src.utils.indexador_dje")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Baixar PDFs históricos do DJE TJSP")
    parser.add_argument("--anos", type=int, default=2, choices=[2, 4],
                       help="Quantos anos para trás baixar (2 ou 4)")
    parser.add_argument("--caderno", type=str, default="12",
                       help="Código do caderno (12=Capital)")
    parser.add_argument("--continuar-de", type=str,
                       help="Continuar download de uma data específica (DD/MM/YYYY)")

    args = parser.parse_args()

    baixar_historico(
        anos=args.anos,
        caderno=args.caderno,
        continuar_de=args.continuar_de
    )
