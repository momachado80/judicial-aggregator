import os
from dotenv import load_dotenv

load_dotenv()

# DataJud API
DATAJUD_BASE_URL = os.getenv("DATAJUD_BASE_URL", "https://api-publica.datajud.cnj.jus.br")
DATAJUD_API_KEY = os.getenv("DATAJUD_API_KEY", "")

# Filtros para coleta
TRIBUNAIS = ["TJSP", "TJBA"]
CLASSES_PROCESSO = {
    "8015": "Divórcio",
    "8016": "Inventário"
}

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jud_user:jud_pass@db:5432/jud_agg")
