#!/usr/bin/env python3
"""
Script de teste para scraping do e-SAJ TJSP
Objetivo: Acessar um processo e buscar menções a imóveis nos autos

IMPORTANTE: Este é um script de TESTE. Rode manualmente para ver se funciona.
Se funcionar, podemos integrar ao sistema principal.

Requisitos:
    pip install selenium webdriver-manager beautifulsoup4
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Termos que indicam imóveis
TERMOS_IMOVEL = [
    'imóvel', 'imovel', 'imóveis', 'imoveis',
    'matrícula', 'matricula', 
    'apartamento', 'apto',
    'casa', 'residência', 'residencia',
    'terreno', 'lote', 'gleba',
    'fazenda', 'sítio', 'sitio', 'chácara', 'chacara',
    'escritura', 'registro de imóveis', 'registro de imoveis',
    'certidão de ônus', 'certidao de onus',
    'metros quadrados', 'm²', 'm2',
    'hectare', 'alqueire',
    'condomínio', 'condominio',
    'edifício', 'edificio',
    'prédio', 'predio',
    'sala comercial', 'loja', 'galpão', 'galpao',
    'iptu', 'contribuinte imobiliário'
]

# Termos para EXCLUIR (falsos positivos conhecidos)
FALSOS_POSITIVOS = [
    'santa casa',
    'matrícula escolar',
    'casa de saúde',
    'casa de repouso'
]


def configurar_navegador(headless=False):
    """Configura o Chrome WebDriver"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver


def buscar_processo(driver, numero_processo):
    """
    Acessa a página de consulta do TJSP e busca o processo
    
    Args:
        driver: WebDriver do Selenium
        numero_processo: Número no formato NNNNNNN-NN.NNNN.N.NN.NNNN
    
    Returns:
        True se encontrou o processo, False caso contrário
    """
    # URL de consulta direta
    url = f"https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&dadosConsulta.valorConsultaNuUnificado={numero_processo}"
    
    print(f"\n{'='*60}")
    print(f"Acessando processo: {numero_processo}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    driver.get(url)
    time.sleep(3)  # Aguarda carregamento
    
    return True


def extrair_texto_pagina(driver):
    """Extrai todo o texto da página atual"""
    try:
        # Pega o HTML da página
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts e styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extrai texto
        texto = soup.get_text(separator=' ', strip=True)
        return texto.lower()
    except Exception as e:
        print(f"Erro ao extrair texto: {e}")
        return ""


def verificar_imovel_no_texto(texto):
    """
    Verifica se o texto contém menções a imóveis
    
    Returns:
        dict com resultado da análise
    """
    texto_lower = texto.lower()
    
    # Primeiro, verifica falsos positivos
    for falso in FALSOS_POSITIVOS:
        if falso in texto_lower:
            # Remove o falso positivo do texto para não confundir
            texto_lower = texto_lower.replace(falso, '')
    
    # Busca termos de imóvel
    termos_encontrados = []
    for termo in TERMOS_IMOVEL:
        if termo in texto_lower:
            # Conta ocorrências
            count = texto_lower.count(termo)
            termos_encontrados.append({'termo': termo, 'ocorrencias': count})
    
    # Análise
    tem_imovel = len(termos_encontrados) > 0
    confianca = 'alta' if len(termos_encontrados) >= 3 else 'media' if len(termos_encontrados) >= 1 else 'baixa'
    
    return {
        'tem_imovel': tem_imovel,
        'confianca': confianca,
        'termos_encontrados': termos_encontrados,
        'total_termos': len(termos_encontrados)
    }


def tentar_acessar_documentos(driver):
    """
    Tenta acessar a aba de documentos/peças do processo
    """
    try:
        # Procura por links de documentos
        links_docs = driver.find_elements(By.PARTIAL_LINK_TEXT, "Documento")
        links_autos = driver.find_elements(By.PARTIAL_LINK_TEXT, "Autos")
        links_peticao = driver.find_elements(By.PARTIAL_LINK_TEXT, "Petição")
        
        todos_links = links_docs + links_autos + links_peticao
        
        if todos_links:
            print(f"Encontrados {len(todos_links)} links de documentos")
            return todos_links
        else:
            print("Nenhum link de documento encontrado")
            return []
    except Exception as e:
        print(f"Erro ao buscar documentos: {e}")
        return []


def analisar_processo(numero_processo, headless=False):
    """
    Função principal que analisa um processo
    
    Args:
        numero_processo: Número do processo formatado
        headless: Se True, não abre janela do navegador
    
    Returns:
        dict com resultado da análise
    """
    driver = None
    
    try:
        print("\n" + "="*60)
        print("INICIANDO ANÁLISE DE PROCESSO")
        print("="*60)
        
        # Configura navegador
        print("\n[1/4] Configurando navegador...")
        driver = configurar_navegador(headless=headless)
        
        # Busca processo
        print("\n[2/4] Buscando processo no TJSP...")
        buscar_processo(driver, numero_processo)
        
        # Extrai texto da página principal
        print("\n[3/4] Extraindo informações da página...")
        texto = extrair_texto_pagina(driver)
        
        # Verifica menções a imóveis
        print("\n[4/4] Analisando menções a imóveis...")
        resultado = verificar_imovel_no_texto(texto)
        
        # Mostra resultado
        print("\n" + "="*60)
        print("RESULTADO DA ANÁLISE")
        print("="*60)
        print(f"Processo: {numero_processo}")
        print(f"Tem imóvel: {'SIM' if resultado['tem_imovel'] else 'NAO'}")
        print(f"Confiança: {resultado['confianca']}")
        print(f"Termos encontrados: {resultado['total_termos']}")
        
        if resultado['termos_encontrados']:
            print("\nTermos detectados:")
            for t in resultado['termos_encontrados']:
                print(f"  - '{t['termo']}': {t['ocorrencias']} ocorrência(s)")
        
        # Salva screenshot para debug
        screenshot_path = f"screenshot_{numero_processo.replace('.', '_').replace('-', '_')}.png"
        driver.save_screenshot(screenshot_path)
        print(f"\nScreenshot salvo: {screenshot_path}")
        
        return resultado
        
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        return {'tem_imovel': False, 'erro': str(e)}
        
    finally:
        if driver:
            print("\nFechando navegador...")
            driver.quit()


def testar_multiplos_processos(processos, headless=False, delay=5):
    """
    Testa múltiplos processos com delay entre cada um
    
    Args:
        processos: Lista de números de processo
        headless: Se True, não abre janela
        delay: Segundos entre cada consulta (para não sobrecarregar)
    """
    resultados = []
    
    for i, processo in enumerate(processos):
        print(f"\n\n{'#'*60}")
        print(f"PROCESSO {i+1} de {len(processos)}")
        print(f"{'#'*60}")
        
        resultado = analisar_processo(processo, headless=headless)
        resultado['numero'] = processo
        resultados.append(resultado)
        
        if i < len(processos) - 1:
            print(f"\nAguardando {delay} segundos antes do próximo...")
            time.sleep(delay)
    
    # Resumo final
    print("\n\n" + "="*60)
    print("RESUMO FINAL")
    print("="*60)
    
    com_imovel = [r for r in resultados if r.get('tem_imovel')]
    sem_imovel = [r for r in resultados if not r.get('tem_imovel')]
    
    print(f"Total analisados: {len(resultados)}")
    print(f"Com indicação de imóvel: {len(com_imovel)}")
    print(f"Sem indicação de imóvel: {len(sem_imovel)}")
    
    if com_imovel:
        print("\nProcessos COM indicação de imóvel:")
        for r in com_imovel:
            print(f"  - {r['numero']} (confiança: {r.get('confianca', 'N/A')})")
    
    return resultados


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    # Processos de teste (peguei da sua screenshot)
    PROCESSOS_TESTE = [
        "1007829-84.2025.8.26.0019",  # Inventário - Americana
        "1006159-11.2025.8.26.0019",  # Inventário - Americana
        "1005457-65.2025.8.26.0019",  # Inventário - Americana
    ]
    
    print("="*60)
    print("TESTE DE SCRAPING DO e-SAJ TJSP")
    print("="*60)
    print("\nEste script vai:")
    print("1. Abrir o Chrome automaticamente")
    print("2. Acessar cada processo no site do TJSP")
    print("3. Extrair o texto da página")
    print("4. Buscar menções a imóveis")
    print("\nPressione ENTER para continuar ou CTRL+C para cancelar...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelado pelo usuário.")
        exit()
    
    # Roda o teste (com janela visível para debug)
    resultados = testar_multiplos_processos(
        PROCESSOS_TESTE, 
        headless=False,  # Mude para True para rodar sem abrir janela
        delay=5  # 5 segundos entre cada processo
    )
    
    print("\n\nTeste concluído!")
