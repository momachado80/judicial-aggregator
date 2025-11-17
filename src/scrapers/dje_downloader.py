from playwright.sync_api import sync_playwright
import time
import os

def baixar_dje_tjsp(data: str, caderno: str = "12"):
    """Baixa PDF do DJE TJSP"""
    print(f"🌐 Baixando DJE de {data}, caderno {caderno}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
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
            page.evaluate(f'document.querySelector("input[type=\'text\']").value = "{data}"')
            
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

if __name__ == "__main__":
    # Testar com Caderno 12 (Capital Parte I)
    pdf = baixar_dje_tjsp("14/11/2025", caderno="12")
    if pdf:
        print(f"\n🎉 Download completo!")
