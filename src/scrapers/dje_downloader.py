from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime, timedelta
from typing import List, Optional

# Mapeamento de cadernos DJE TJSP
CADERNOS_TJSP = {
    "11": "Judicial - 1ª Instância - Interior - Parte I",
    "12": "Judicial - 1ª Instância - Capital - Parte I",
    "13": "Judicial - 1ª Instância - Capital - Parte II",
    "14": "Judicial - 1ª Instância - Interior - Parte II"
}

# Comarcas por caderno
COMARCAS_POR_CADERNO = {
    "São Paulo": ["12", "13"],  # Capital
    "Piracicaba": ["11", "14"],  # Interior
    "Campinas": ["11", "14"],
    "Santos": ["11", "14"],
    "Guarulhos": ["11", "14"]
}

def baixar_dje_tjsp(data: str, caderno: str = "12", headless: bool = True):
    """
    Baixa PDF do DJE TJSP

    Args:
        data: Data no formato DD/MM/YYYY
        caderno: Código do caderno (11, 12, 13, 14)
        headless: Se True, roda sem abrir janela do browser
    """
    print(f"🌐 Baixando DJE de {data}, caderno {caderno} ({CADERNOS_TJSP.get(caderno, 'Desconhecido')})")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=['--ignore-certificate-errors']
        )
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            print("📡 Acessando DJE...")
            page.goto("https://www.dje.tjsp.jus.br/cdje/index.do", timeout=30000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            print("✅ Página carregada!")
            
            # Preencher data usando o name correto
            print(f"📝 Preenchendo data: {data}")
            page.fill('input[type="text"]', data)

            # Trigger change event para o JavaScript do site processar
            page.evaluate('document.querySelector("input[type=\'text\']").dispatchEvent(new Event("change", { bubbles: true }))')

            # Aguardar campo de caderno ser habilitado (não mais disabled)
            print(f"⏳ Aguardando campo de caderno ser habilitado...")
            page.wait_for_function('document.querySelector("select[name=\\"cadernosCad\\"]").disabled === false', timeout=10000)
            time.sleep(1)

            # Selecionar caderno usando name="cadernosCad"
            print(f"📚 Selecionando caderno {caderno}...")
            page.select_option('select[name="cadernosCad"]', caderno)
            
            time.sleep(1)
            
            # Preparar download
            download_path = os.path.abspath("data/dje_pdfs")
            os.makedirs(download_path, exist_ok=True)
            
            # Clicar em Download
            print("⬇️  Clicando em Download...")
            with page.expect_download(timeout=60000) as download_info:
                page.click('input[value="Download"]')
            
            download = download_info.value
            filename = f"dje_{data.replace('/', '-')}_cad{caderno}.pdf"
            filepath = os.path.join(download_path, filename)
            download.save_as(filepath)
            
            size = os.path.getsize(filepath)
            print(f"✅ Salvo: {filepath}")
            print(f"📊 Tamanho: {size / 1024 / 1024:.2f} MB")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
        finally:
            time.sleep(2)
            browser.close()

def baixar_dje_intervalo(
    data_inicio: str,
    data_fim: str,
    comarcas: List[str] = ["São Paulo"],
    headless: bool = True
) -> List[str]:
    """
    Baixa múltiplos DJEs de um intervalo de datas

    Args:
        data_inicio: Data inicial (DD/MM/YYYY)
        data_fim: Data final (DD/MM/YYYY)
        comarcas: Lista de comarcas para filtrar cadernos
        headless: Se True, roda sem abrir janela do browser

    Returns:
        Lista de caminhos dos PDFs baixados
    """
    print("="*80)
    print(f"📅 Baixando DJEs de {data_inicio} até {data_fim}")
    print(f"📍 Comarcas: {', '.join(comarcas)}")
    print("="*80)

    # Converter datas
    inicio = datetime.strptime(data_inicio, "%d/%m/%Y")
    fim = datetime.strptime(data_fim, "%d/%m/%Y")

    # Determinar cadernos necessários
    cadernos_necessarios = set()
    for comarca in comarcas:
        cadernos = COMARCAS_POR_CADERNO.get(comarca, ["11", "12", "13", "14"])
        cadernos_necessarios.update(cadernos)

    print(f"📚 Cadernos a baixar: {', '.join(sorted(cadernos_necessarios))}\n")

    pdfs_baixados = []
    data_atual = inicio

    while data_atual <= fim:
        data_str = data_atual.strftime("%d/%m/%Y")

        # Pular finais de semana (DJE não publica)
        if data_atual.weekday() >= 5:  # 5 = Sábado, 6 = Domingo
            print(f"⏭️  Pulando {data_str} (final de semana)")
            data_atual += timedelta(days=1)
            continue

        print(f"\n📆 Processando {data_str}...")

        for caderno in sorted(cadernos_necessarios):
            pdf_path = baixar_dje_tjsp(data_str, caderno, headless=headless)
            if pdf_path:
                pdfs_baixados.append(pdf_path)
                print(f"   ✅ Caderno {caderno} baixado")
            else:
                print(f"   ⚠️  Caderno {caderno} falhou")

            time.sleep(2)  # Delay entre downloads

        data_atual += timedelta(days=1)

    print("\n" + "="*80)
    print(f"🎉 Download completo! {len(pdfs_baixados)} PDFs baixados")
    print("="*80)

    return pdfs_baixados


def obter_cadernos_por_comarca(comarca: str) -> List[str]:
    """Retorna os cadernos apropriados para uma comarca"""
    return COMARCAS_POR_CADERNO.get(comarca, ["11", "14"])


if __name__ == "__main__":
    import sys

    # Teste 1: Download único
    print("🧪 TESTE 1: Download de um único DJE")
    pdf = baixar_dje_tjsp("15/11/2025", caderno="12", headless=False)
    if pdf:
        print(f"✅ Sucesso: {pdf}\n")

    # Teste 2: Intervalo de datas
    print("\n🧪 TESTE 2: Intervalo de 3 dias (São Paulo)")
    pdfs = baixar_dje_intervalo(
        data_inicio="13/11/2025",
        data_fim="15/11/2025",
        comarcas=["São Paulo"],
        headless=True
    )
    print(f"✅ {len(pdfs)} PDFs baixados")

    # Teste 3: Múltiplas comarcas
    print("\n🧪 TESTE 3: São Paulo e Piracicaba (1 dia)")
    pdfs = baixar_dje_intervalo(
        data_inicio="15/11/2025",
        data_fim="15/11/2025",
        comarcas=["São Paulo", "Piracicaba"],
        headless=True
    )
    print(f"✅ {len(pdfs)} PDFs baixados")
