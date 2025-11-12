#!/bin/bash
echo "🔍 TESTANDO ENDPOINT DE BUSCA SOB DEMANDA"
echo "========================================"
echo ""
echo "Buscando 10 Inventários do TJSP com valor > R$100.000..."
echo ""

curl -X POST "https://judicial-aggregator-production.up.railway.app/api/buscar-processos" \
  -H "Content-Type: application/json" \
  -d '{
    "tribunal": "TJSP",
    "tipo_processo": "Inventário",
    "valor_causa_min": 100000,
    "limit": 10
  }' 2>/dev/null | python3 -m json.tool

echo ""
echo "========================================"
