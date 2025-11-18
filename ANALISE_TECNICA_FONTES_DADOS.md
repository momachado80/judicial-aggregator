# 📊 Análise Técnica: API DataJud vs DJE (Diário Oficial)

**Data:** 18/11/2025
**Objetivo:** Determinar a melhor estratégia para coleta precisa de processos judiciais

---

## 🎯 REQUISITOS DO SISTEMA

### Requisitos Funcionais

1. **Tribunais:** Foco em TJSP (prioritário)
2. **Comarcas:** São Paulo, Piracicaba + raio de ~50km
3. **Tipos de processo:** Inventário e Divórcio (Litigioso/Consensual)
4. **Critério essencial:** Processos que envolvam **IMÓVEIS**
5. **Status:** Apenas processos **ATIVOS** (excluir extintos e suspensos)
6. **Filtros:** Comarca, valor da causa, tipo, intervalo de datas
7. **Precisão:** **ABSOLUTA** - sem resultados fora do escopo

### Problema Atual

❌ **Inconsistência nos resultados:**
- Busca por "Inventário" retorna "Propriedade Intelectual"
- Processos fora do escopo esperado
- Impossível filtrar por assunto específico (imóveis)
- Impossível filtrar por status processual (ativo/extinto)

---

## 🔬 ANÁLISE TÉCNICA DAS FONTES

### 1️⃣ API DataJud (CNJ)

**URL:** `https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search`
**Tecnologia:** Elasticsearch
**Autenticação:** API Key pública

#### ✅ Vantagens

- **Velocidade:** Retorna milhares de processos em segundos
- **Estruturada:** Dados normalizados em JSON
- **Abrangência:** 10.000+ processos disponíveis
- **Paginação:** Suporte nativo para grandes volumes
- **Manutenção:** CNJ mantém e atualiza os dados

#### ❌ Limitações CRÍTICAS

1. **Filtros limitados da API:**
   ```json
   {
     "query": {
       "bool": {
         "must": [
           {"term": {"classe.codigo": "39"}},  // ✅ Funciona
           {"term": {"tribunal": "TJSP"}}      // ✅ Funciona
         ]
       }
     }
   }
   ```

2. **Filtros NÃO disponíveis na query direta:**
   - ❌ Assunto específico (imóveis vs. outros bens)
   - ❌ Status processual (ativo/extinto/suspenso/arquivado)
   - ❌ Comarca (precisa filtrar no backend após receber dados)
   - ❌ Movimentações específicas (penhora, leilão, etc.)

3. **Problema de classificação:**
   - Processos podem estar mal classificados no sistema do CNJ
   - "Inventário" pode incluir casos sem relação com imóveis
   - Código de classe 39 traz TODOS os inventários (móveis, semoventes, marcas, etc.)

4. **Disponibilidade:**
   - ⚠️ API atualmente retornando **403 Access Denied**
   - Pode haver bloqueios por IP, região ou mudança de chave
   - Dependência externa do CNJ

#### 📊 Estrutura de Dados (quando funciona)

```json
{
  "numeroProcesso": "00567233219978050001",
  "tribunal": "TJSP",
  "classe": {
    "codigo": "39",
    "nome": "Inventário"
  },
  "orgaoJulgador": {
    "nomeOrgao": "1ª Vara de Família - Foro Regional de Santo Amaro"
  },
  "dataAjuizamento": "19970101",
  "valorCausa": 150000.50,
  "assunto": ["Inventário e Partilha"],  // ⚠️ Genérico demais
  "movimentos": [
    {
      "codigo": "123",
      "nome": "Juntada de documentos",
      "dataHora": "2024-01-15T10:30:00Z"
    }
  ],
  "partes": [...]
}
```

**Problema:** Campo `assunto` é muito genérico. Não distingue:
- Inventário com imóveis
- Inventário apenas com veículos
- Inventário com marcas/patentes
- Inventário com ações/investimentos

---

### 2️⃣ DJE - Diário de Justiça Eletrônico

**URL:** `https://www.dje.tjsp.jus.br`
**Tecnologia:** Scraping de PDFs publicados diariamente

#### ✅ Vantagens

1. **Fonte oficial e confiável:**
   - Publicações oficiais do tribunal
   - Dados juridicamente válidos
   - Atualizações diárias garantidas

2. **Contexto completo:**
   - Texto integral da publicação
   - Possível identificar menção a "imóvel", "terreno", "casa", "apartamento"
   - Informações de advogados, partes, valores

3. **Filtro por caderno:**
   - Caderno 11: Judicial - 1ª Instância - Interior - Parte I
   - Caderno 12: Judicial - 1ª Instância - Capital - Parte I
   - Caderno 13: Judicial - 1ª Instância - Capital - Parte II

4. **Precisão geográfica:**
   - Publicações por comarca específica
   - Possível focar apenas em São Paulo e Piracicaba

#### ❌ Limitações

1. **Performance:**
   - Download de PDFs grandes (10-50 MB cada)
   - Processamento lento via OCR/parsing
   - ~100-200 processos/dia por comarca

2. **Complexidade técnica:**
   - Requer Playwright (automação de browser)
   - Parsing de PDF com regex (sujeito a erros)
   - Estrutura de dados não padronizada

3. **Cobertura:**
   - Apenas processos **publicados naquele dia**
   - Não acessa histórico completo
   - Necessário rodar diariamente sem falhas

4. **Manutenção:**
   - Site do DJE pode mudar layout
   - Scraper precisa ser atualizado
   - Riscos de bloqueio por automação

#### 📊 Exemplo de Extração

```
COMARCA DE SÃO PAULO - FORO REGIONAL DE SANTO AMARO
1ª Vara de Família e Sucessões

Processo nº 1234567-89.2024.8.26.0002
Inventário
Requerente: MARIA DA SILVA
Requerido: ESPÓLIO DE JOÃO DA SILVA

[...] partilha do imóvel situado na Rua das Flores, 123, apartamento 45,
matrícula nº 12.345 do 1º Cartório de Registro de Imóveis [...]
avaliado em R$ 450.000,00 [...]

Advogado: Dr. José Santos - OAB/SP 123.456
```

**Vantagem:** Com parsing inteligente, é possível detectar:
- ✅ Menção explícita a "imóvel"
- ✅ Endereço do imóvel
- ✅ Matrícula do imóvel
- ✅ Valor da avaliação

---

## 🎯 RECOMENDAÇÃO TÉCNICA

### 🏆 **Estratégia Híbrida (Melhor das Duas Abordagens)**

#### Fase 1: Busca Primária via API DataJud (quando disponível)

**Por quê:**
- Velocidade e volume
- Acesso a histórico completo
- Dados estruturados

**Filtros aplicados:**
```python
query = {
    "query": {
        "bool": {
            "must": [
                {"term": {"classe.codigo": "39"}},  # Inventário
                {"term": {"tribunal": "TJSP"}}
            ],
            "must_not": [
                # Futuramente: excluir processos extintos
                {"term": {"situacao.codigo": "EXTINTO"}},
                {"term": {"situacao.codigo": "ARQUIVADO"}}
            ]
        }
    },
    "size": 1000,
    "sort": [{"dataAjuizamento": {"order": "desc"}}]
}
```

**Filtros no Backend (após receber dados):**
1. ✅ Filtrar por comarca (São Paulo, Piracicaba + região)
2. ✅ Filtrar por valor da causa
3. ❌ **NÃO consegue filtrar assunto (imóveis)** ← PROBLEMA

---

#### Fase 2: Análise de Movimentações (Detecção de Imóveis)

Para cada processo retornado pela API:

```python
PALAVRAS_CHAVE_IMOVEIS = [
    "imóvel", "imovel", "terreno", "casa", "apartamento",
    "lote", "propriedade", "registro de imóveis",
    "matrícula", "escritura", "metragem", "área construída",
    "condomínio", "unidade autônoma"
]

PALAVRAS_CHAVE_URGENCIA = [
    "penhora", "leilão", "hasta pública", "adjudicação",
    "alienação judicial", "partilha", "avaliação"
]

def tem_imovel(processo):
    """Analisa movimentações para detectar menção a imóveis"""
    texto_completo = " ".join([
        mov.get("nome", "")
        for mov in processo.get("movimentos", [])
    ]).lower()

    return any(palavra in texto_completo for palavra in PALAVRAS_CHAVE_IMOVEIS)
```

**Limitação:** Processos recém-distribuídos podem não ter movimentações suficientes.

---

#### Fase 3: Complemento via DJE (Casos Novos e Validação)

**Estratégia:**
1. Rodar coleta DJE **diariamente** para comarcas-alvo
2. Fazer parsing com foco em:
   - Inventários e Divórcios
   - Menção explícita a imóveis
   - Comarca = São Paulo ou Piracicaba

3. Cruzar com dados da API:
   - Se processo já existe → enriquecer dados
   - Se não existe → novo processo detectado

**Vantagem:**
- ✅ Detecta processos novos no mesmo dia
- ✅ Garante precisão (texto completo disponível)
- ✅ Independente da API DataJud

---

## 📋 IMPLEMENTAÇÃO RECOMENDADA

### Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────┐
│                   USUÁRIO (Frontend)                    │
│  - Seleciona comarcas: São Paulo, Piracicaba           │
│  - Define valor da causa: R$ 100k - R$ 1M              │
│  - Tipo: Inventário                                     │
│  - Apenas com imóveis: ✓                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              BACKEND - Orquestrador                     │
└─────────────────────────────────────────────────────────┘
          │                            │
          ▼                            ▼
┌─────────────────────┐      ┌──────────────────────────┐
│  Coletor API DataJud│      │    Coletor DJE           │
│  (Busca em massa)   │      │  (Busca diária/          │
│                     │      │   intervalo de datas)    │
│  + Filtro backend:  │      │                          │
│    - Comarca        │      │  + Parsing inteligente:  │
│    - Valor          │      │    - Detecta "imóvel"    │
│    - Data           │      │    - Extrai endereço     │
│                     │      │    - Extrai valor        │
└──────────┬──────────┘      └───────────┬──────────────┘
           │                             │
           └──────────┬──────────────────┘
                      ▼
         ┌─────────────────────────────┐
         │   Análise de Conteúdo       │
         │   (Palavras-chave)          │
         │                             │
         │   - tem_imovel()            │
         │   - tem_urgencia()          │
         │   - calcular_relevancia()   │
         └──────────┬──────────────────┘
                    ▼
         ┌─────────────────────────────┐
         │   Banco de Dados            │
         │   (Processos filtrados)     │
         │                             │
         │   Score de relevância:      │
         │   1.0 = Imóvel + urgente    │
         │   0.8 = Imóvel confirmado   │
         │   0.5 = Possível imóvel     │
         │   0.2 = Sem indício         │
         └─────────────────────────────┘
```

---

## 🚀 PLANO DE AÇÃO

### ✅ Implementação Imediata (Esta Semana)

1. **Corrigir acesso à API DataJud**
   - Verificar se chave expirou
   - Testar com nova chave da Wiki CNJ
   - Implementar retry com exponential backoff

2. **Melhorar filtros backend**
   ```python
   # src/api/routers/buscar_processos.py

   # Adicionar filtro de status
   must_not_filters = [
       {"term": {"situacao": "Extinto"}},
       {"term": {"situacao": "Arquivado"}},
       {"term": {"situacao": "Suspenso"}}
   ]

   # Adicionar análise de movimentações
   def filtrar_por_imovel(processos):
       return [p for p in processos if tem_imovel(p)]
   ```

3. **Implementar análise de palavras-chave**
   - Criar função `tem_imovel(processo)`
   - Criar função `calcular_score_relevancia(processo)`
   - Adicionar campo `tem_imovel: boolean` no banco

### 📅 Implementação Curto Prazo (Próximas 2 Semanas)

4. **Integrar coleta DJE complementar**
   - Job diário: baixar DJE de São Paulo e Piracicaba
   - Parsing focado em Inventários e Divórcios
   - Cruzamento com base da API

5. **Filtro de intervalo de datas**
   - Permitir buscar publicações DJE de 01/11 a 30/11
   - Interface no frontend para selecionar período

6. **Comarcas da região (raio 50km)**
   - Mapear comarcas próximas a SP e Piracicaba
   - Adicionar lista configurável no frontend

### 🎯 Implementação Médio Prazo (1 Mês)

7. **Machine Learning para classificação**
   - Treinar modelo para identificar processos com imóveis
   - Features: movimentações, partes, valores
   - Acurácia esperada: >90%

8. **Monitoramento de status processual**
   - Webhook para mudanças de status
   - Alertas quando processo fica ativo/extinto

---

## 💡 DECISÃO FINAL

### 🏆 **Usar AMBAS as fontes simultaneamente**

**API DataJud:** Busca em massa, histórico, velocidade
**DJE:** Precisão, validação, processos novos

**Fluxo ideal:**
1. API DataJud busca 1000 processos de Inventário TJSP
2. Backend filtra por comarca (São Paulo, Piracicaba)
3. Backend analisa movimentações (detecta imóveis)
4. Score de relevância calculado
5. DJE complementa diariamente com novos processos
6. Cruzamento elimina duplicatas e enriquece dados

**Resultado esperado:**
- ✅ Precisão absoluta (apenas processos com imóveis)
- ✅ Cobertura completa (histórico + novos)
- ✅ Velocidade (API para volume, DJE para precisão)
- ✅ Confiabilidade (redundância de fontes)

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Meta | Como medir |
|---------|------|-----------|
| Precisão | >95% | Processos retornados realmente têm imóveis |
| Cobertura | >90% | % de processos relevantes capturados |
| Falsos positivos | <5% | Processos sem imóveis que passaram |
| Latência | <5s | Tempo de resposta da busca |
| Atualização | Diária | Novos processos aparecem em 24h |

---

**Conclusão:** A solução ideal é **HÍBRIDA**, combinando a velocidade da API DataJud com a precisão do DJE, aplicando filtros inteligentes no backend baseados em análise de conteúdo.
