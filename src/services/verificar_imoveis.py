"""
Serviço de verificação de imóveis no e-SAJ TJSP
Usa Selenium com Chrome headless para acessar os processos
"""

import time
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Termos que indicam imóveis
TERMOS_IMOVEL = [
    'imóvel', 'imovel', 'imóveis', 'imoveis',
    'matrícula', 'matricula', 
    'apartamento', 'apto',
    'terreno', 'lote', 'gleba',
    'fazenda', 'sítio', 'sitio', 'chácara', 'chacara',
    'escritura', 'registro de imóveis', 'registro de imoveis',
    'certidão de ônus', 'certidao de onus',
    'metros quadrados', 'm²',
    'hectare', 'alqueire',
    'condomínio', 'condominio',
    'edifício', 'edificio',
    'prédio', 'predio',
    'sala comercial', 'galpão', 'galpao',
    'iptu',
]

# Termos para EXCLUIR (falsos positivos)
FALSOS_POSITIVOS = [
    'santa casa',
    'matrícula escolar',
    'matricula escolar',
    'casa de saúde',
    'casa de saude',
    'casa de repouso',
    'casa civil',
    'casa da moeda',
]


def criar_driver() -> webdriver.Chrome:
    """Cria o WebDriver do Chrome configurado para Railway"""
    chrome_options = Options()
    
    # Modo headless obrigatório no servidor
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    # User agent para parecer navegador normal
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # No Railway, o Chrome está instalado globalmente
    chrome_options.binary_location = "/usr/bin/google-chrome-stable"
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    
    return driver


def extrair_texto_pagina(driver: webdriver.Chrome) -> str:
    """Extrai todo o texto da página atual"""
    try:
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts e styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        texto = soup.get_text(separator=' ', strip=True)
        return texto.lower()
    except Exception as e:
        logger.error(f"Erro ao extrair texto: {e}")
        return ""


def verificar_imovel_no_texto(texto: str) -> dict:
    """Verifica se o texto contém menções a imóveis"""
    texto_lower = texto.lower()
    
    # Remove falsos positivos
    for falso in FALSOS_POSITIVOS:
        texto_lower = texto_lower.replace(falso, '')
    
    # Busca termos de imóvel
    termos_encontrados = []
    for termo in TERMOS_IMOVEL:
        if termo in texto_lower:
            count = texto_lower.count(termo)
            termos_encontrados.append({'termo': termo, 'ocorrencias': count})
    
    # Análise de confiança
    total_ocorrencias = sum(t['ocorrencias'] for t in termos_encontrados)
    
    if len(termos_encontrados) >= 3 or total_ocorrencias >= 5:
        confianca = 'alta'
    elif len(termos_encontrados) >= 1:
        confianca = 'media'
    else:
        confianca = 'baixa'
    
    return {
        'tem_imovel': len(termos_encontrados) > 0,
        'confianca': confianca,
        'termos_encontrados': termos_encontrados,
        'total_termos': len(termos_encontrados),
        'total_ocorrencias': total_ocorrencias
    }


def verificar_processo(numero_processo: str) -> dict:
    """
    Verifica um processo específico no e-SAJ
    
    Args:
        numero_processo: Número no formato NNNNNNN-NN.NNNN.N.NN.NNNN
    
    Returns:
        dict com resultado da análise
    """
    driver = None
    
    try:
        logger.info(f"Verificando processo: {numero_processo}")
        
        # Cria driver
        driver = criar_driver()
        
        # URL de consulta
        url = (
            f"https://esaj.tjsp.jus.br/cpopg/search.do?"
            f"conversationId=&cbPesquisa=NUMPROC&"
            f"dadosConsulta.tipoNuProcesso=UNIFICADO&"
            f"dadosConsulta.valorConsultaNuUnificado={numero_processo}"
        )
        
        # Acessa a página
        driver.get(url)
        time.sleep(3)  # Aguarda carregamento
        
        # Extrai texto
        texto = extrair_texto_pagina(driver)
        
        if not texto or len(texto) < 100:
            return {
                'numero': numero_processo,
                'tem_imovel': None,
                'erro': 'Página não carregou corretamente',
                'confianca': None
            }
        
        # Analisa
        resultado = verificar_imovel_no_texto(texto)
        resultado['numero'] = numero_processo
        resultado['erro'] = None
        
        logger.info(
            f"Processo {numero_processo}: "
            f"tem_imovel={resultado['tem_imovel']}, "
            f"confianca={resultado['confianca']}"
        )
        
        return resultado
        
    except Exception as e:
        logger.error(f"Erro ao verificar {numero_processo}: {e}")
        return {
            'numero': numero_processo,
            'tem_imovel': None,
            'erro': str(e),
            'confianca': None
        }
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def verificar_processos_lote(numeros: list[str], delay: float = 2.0) -> list[dict]:
    """
    Verifica múltiplos processos em lote
    
    Args:
        numeros: Lista de números de processo
        delay: Segundos entre cada consulta
    
    Returns:
        Lista de resultados
    """
    resultados = []
    
    for i, numero in enumerate(numeros):
        logger.info(f"Processando {i+1}/{len(numeros)}: {numero}")
        
        resultado = verificar_processo(numero)
        resultados.append(resultado)
        
        # Delay entre requisições para não sobrecarregar
        if i < len(numeros) - 1:
            time.sleep(delay)
    
    return resultados
