import os
from typing import Dict
import yaml

class RelevanceClassifier:
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict:
        rules_path = os.path.join("config", "rules.yaml")
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            return {
                "Alta": {"movimentos_keywords": ["sentença", "acórdão"], "min_value": 50000},
                "Média": {"movimentos_keywords": ["despacho", "intimação"]},
                "Baixa": {"default": True}
            }
    
    def classify_process(self, process_data: Dict) -> str:
        if self._check_alta(process_data):
            return "Alta"
        if self._check_media(process_data):
            return "Média"
        return "Baixa"
    
    def classify_movement(self, movement_text: str) -> str:
        text_lower = movement_text.lower()
        alta_keywords = self.rules.get("Alta", {}).get("movimentos_keywords", [])
        if any(kw in text_lower for kw in alta_keywords):
            return "Alta"
        media_keywords = self.rules.get("Média", {}).get("movimentos_keywords", [])
        if any(kw in text_lower for kw in media_keywords):
            return "Média"
        return "Baixa"
    
    def _check_alta(self, process_data: Dict) -> bool:
        rules = self.rules.get("Alta", {})
        min_value = rules.get("min_value", 50000)
        valor_causa = process_data.get("valor_causa", 0) or 0
        if valor_causa >= min_value:
            return True
        keywords = rules.get("movimentos_keywords", [])
        movements = process_data.get("movements", [])
        for mov in movements:
            desc = mov.get("descricao_norm", "").lower()
            if any(kw in desc for kw in keywords):
                return True
        return False
    
    def _check_media(self, process_data: Dict) -> bool:
        rules = self.rules.get("Média", {})
        keywords = rules.get("movimentos_keywords", [])
        movements = process_data.get("movements", [])
        for mov in movements:
            desc = mov.get("descricao_norm", "").lower()
            if any(kw in desc for kw in keywords):
                return True
        return False

classifier = RelevanceClassifier()
