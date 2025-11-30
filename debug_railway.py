import os
import sys
import json

print(f"CWD: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    from src.utils.comarcas import COMARCAS_TJSP
    print(f"✅ COMARCAS_TJSP loaded. Length: {len(COMARCAS_TJSP)}")
except Exception as e:
    print(f"❌ Error loading COMARCAS_TJSP: {e}")

cache_path = "data/dje_cache.json"
if os.path.exists(cache_path):
    print(f"✅ Cache file found at {cache_path}")
    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)
        print(f"✅ Cache loaded. Total processes: {data.get('total_processos')}")
    except Exception as e:
        print(f"❌ Error reading cache: {e}")
else:
    print(f"❌ Cache file NOT found at {cache_path}")
