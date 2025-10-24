import os
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx

class DataJudClient:
    def __init__(self):
        self.base_url = os.getenv("DATAJUD_BASE_URL", "")
        self.token = os.getenv("DATAJUD_TOKEN", "")
        self.demo_mode = os.getenv("DEMO_SEED", "false").lower() == "true" or not self.base_url
        
    def search(self, tribunal: str, classes: List[str], assuntos: List[str], updated_since: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        if self.demo_mode:
            return self._mock_search(tribunal, classes, assuntos, limit)
        try:
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            params = {"tribunal": tribunal, "classes": ",".join(classes), "assuntos": ",".join(assuntos), "limit": limit}
            if updated_since:
                params["updatedSince"] = updated_since
            with httpx.Client(timeout=30.0) as client:
                response = client.get(f"{self.base_url}/processos", headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching from DataJud: {e}")
            return {"items": [], "cursor": None}
    
    def _mock_search(self, tribunal: str, classes: List[str], assuntos: List[str], limit: int) -> Dict[str, Any]:
        items = []
        for i in range(min(limit, 50)):
            tipo = "Inventário" if "8016" in classes else "Divórcio"
            numero_base = random.randint(1000000, 9999999)
            ano = random.randint(2020, 2024)
            numero_cnj = f"{numero_base:07d}-{random.randint(10, 99)}.{ano}.8.26.{random.randint(100, 999):04d}"
            item = {
                "numeroCNJ": numero_cnj,
                "tribunal": tribunal,
                "classe": classes[0] if classes else "8016",
                "assuntos": assuntos,
                "orgao": f"Vara de Família - {tribunal}",
                "vara": f"{random.randint(1, 10)}ª Vara",
                "comarca": random.choice(["São Paulo", "Salvador", "Campinas"]),
                "valorCausa": round(random.uniform(10000, 500000), 2),
                "dataAtualizacao": (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat(),
                "partes": [
                    {"tipo": "Autor", "nome": f"João da Silva {i}", "documento": None},
                    {"tipo": "Réu", "nome": f"Maria Santos {i}", "documento": None}
                ],
                "movimentos": self._generate_mock_movements(tipo)
            }
            items.append(item)
        return {"items": items, "cursor": None, "total": len(items)}
    
    def _generate_mock_movements(self, tipo: str) -> List[Dict]:
        movements = []
        base_date = datetime.now() - timedelta(days=180)
        if tipo == "Inventário":
            templates = ["Juntada de certidão de óbito", "Intimação das partes", "Nomeação de inventariante", "Sentença de homologação de partilha"]
        else:
            templates = ["Distribuição por sorteio", "Despacho determinando citação", "Sentença de divórcio", "Trânsito em julgado"]
        for i, desc in enumerate(templates[:random.randint(3, 4)]):
            movements.append({"data": (base_date + timedelta(days=i*15)).isoformat(), "tipoMovimento": str(random.randint(1, 999)), "descricao": desc})
        return movements
