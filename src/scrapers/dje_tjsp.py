import requests
import pdfplumber
from datetime import datetime, timedelta
from typing import List, Dict
import re
import os

class DJETJSPScraper:
    """Scraper do Diário de Justiça Eletrônico do TJSP"""
    
    BASE_URL = "https://www.dje.tjsp.jus.br/cdje"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def buscar_processos(
        self, 
        data_inicio: str,  # formato: DD/MM/YYYY
        data_fim: str,     # formato: DD/MM/YYYY
        tipos: List[str] = ["Inventário", "Divórcio"],
        comarcas: List[str] = None
    ) -> List[Dict]:
        """
        Busca processos no DJE do TJSP
        
        Args:
            data_inicio: Data inicial (DD/MM/YYYY)
            data_fim: Data final (DD/MM/YYYY)
            tipos: Lista de tipos de processo
            comarcas: Lista de comarcas (None = todas)
        
        Returns:
            Lista de processos encontrados
        """
        print(f"🔍 Buscando DJE de {data_inicio} até {data_fim}")
        
        # Construir palavras-chave
        palavras = " OR ".join([f'"{tipo}"' for tipo in tipos])
        
        # Fazer busca avançada
        params = {
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'caderno': 'Judicial - 1ª Instância - Interior',
            'palavras': palavras
        }
        
        print(f"📝 Palavras-chave: {palavras}")
        
        # TODO: Implementar download e parse dos PDFs
        # Por enquanto, retorna vazio
        return []
    
    def parse_pdf(self, pdf_path: str, comarcas: List[str] = None) -> List[Dict]:
        """Extrai processos de um PDF do DJE"""
        processos = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                
                # Regex para encontrar processos
                # Formato: NNNNNNN-DD.AAAA.8.26.OOOO
                pattern = r'(\d{7}-\d{2}\.\d{4}\.8\.26\.\d{4})'
                
                for match in re.finditer(pattern, text):
                    numero = match.group(1)
                    
                    # Extrair contexto ao redor do número
                    start = max(0, match.start() - 500)
                    end = min(len(text), match.end() + 500)
                    contexto = text[start:end]
                    
                    # Detectar tipo
                    tipo = None
                    if 'Inventário' in contexto or 'inventário' in contexto:
                        tipo = 'Inventário'
                    elif 'Divórcio' in contexto or 'divórcio' in contexto:
                        tipo = 'Divórcio'
                    
                    if tipo:
                        processos.append({
                            'numero': numero,
                            'tipo': tipo,
                            'contexto': contexto[:200]  # Primeiros 200 chars
                        })
        
        return processos

if __name__ == "__main__":
    # Teste
    scraper = DJETJSPScraper()
    processos = scraper.buscar_processos(
        data_inicio="01/11/2025",
        data_fim="15/11/2025",
        tipos=["Inventário", "Divórcio"]
    )
    print(f"✅ Encontrados {len(processos)} processos")
