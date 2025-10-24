from datetime import datetime
from typing import Any, Dict, List
import hashlib

def generate_movement_hash(numero_cnj: str, data: datetime, tipo_tpu: str, descricao_norm: str) -> str:
    data_str = data.isoformat() if isinstance(data, datetime) else str(data)
    content = f"{numero_cnj}|{data_str}|{tipo_tpu}|{descricao_norm}"
    return hashlib.sha256(content.encode()).hexdigest()

class Normalizer:
    def to_canonical(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        canonical = {
            "numero_cnj": raw_data.get("numeroCNJ", ""),
            "tribunal": raw_data.get("tribunal", ""),
            "classe_tpu": raw_data.get("classe", ""),
            "assunto_tpu": raw_data.get("assuntos", []),
            "orgao": raw_data.get("orgao"),
            "vara": raw_data.get("vara"),
            "comarca": raw_data.get("comarca"),
            "valor_causa": self._parse_float(raw_data.get("valorCausa")),
            "updated_at": self._parse_datetime(raw_data.get("dataAtualizacao")),
            "parties": self._normalize_parties(raw_data.get("partes", [])),
            "movements": self._normalize_movements(raw_data.get("numeroCNJ", ""), raw_data.get("movimentos", []))
        }
        return canonical
    
    def _normalize_parties(self, parties: List[Dict]) -> List[Dict]:
        normalized = []
        for party in parties:
            normalized.append({
                "tipo": party.get("tipo", "Desconhecido"),
                "nome": party.get("nome", "").strip(),
                "documento_hash": self._hash_doc(party.get("documento"))
            })
        return normalized
    
    def _normalize_movements(self, numero_cnj: str, movements: List[Dict]) -> List[Dict]:
        normalized = []
        for mov in movements:
            descricao_raw = mov.get("descricao", "")
            descricao_norm = self._normalize_text(descricao_raw)
            data = self._parse_datetime(mov.get("data"))
            tipo_tpu = mov.get("tipoMovimento")
            normalized.append({
                "data": data,
                "tipo_tpu": tipo_tpu,
                "descricao_raw": descricao_raw,
                "descricao_norm": descricao_norm,
                "hash_idem": generate_movement_hash(numero_cnj, data, tipo_tpu, descricao_norm)
            })
        return normalized
    
    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except:
                try:
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except:
                    pass
        return datetime.utcnow()
    
    def _parse_float(self, value: Any):
        if value is None:
            return None
        try:
            return float(value)
        except:
            return None
    
    def _normalize_text(self, text: str) -> str:
        return text.lower().strip()
    
    def _hash_doc(self, doc: str):
        if not doc:
            return None
        return hashlib.sha256(doc.encode()).hexdigest()

normalizer = Normalizer()
