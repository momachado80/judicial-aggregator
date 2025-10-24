import hashlib
from datetime import datetime

def generate_movement_hash(numero_cnj: str, data: datetime, tipo_tpu: str, descricao_norm: str) -> str:
    data_str = data.isoformat() if isinstance(data, datetime) else str(data)
    content = f"{numero_cnj}|{data_str}|{tipo_tpu}|{descricao_norm}"
    return hashlib.sha256(content.encode()).hexdigest()

def is_duplicate_movement(db_session, hash_idem: str) -> bool:
    from src.normalization.models import Movement
    existing = db_session.query(Movement).filter(Movement.hash_idem == hash_idem).first()
    return existing is not None
