# ⚖️ Judicial Aggregator

Sistema profissional de monitoramento e agregação de processos judiciais do TJSP e TJBA.

## 🎯 Funcionalidades

- ✅ Dashboard analítico com 5 gráficos interativos
- ✅ Sistema de busca e filtros avançados
- ✅ Export de relatórios em PDF e Excel
- ✅ Página de detalhes completa de processos
- ✅ Sistema de relevância automática
- ✅ Design responsivo e moderno

## 🏗️ Tecnologias

**Backend:**
- Python 3.11
- FastAPI
- PostgreSQL 15
- SQLAlchemy
- ReportLab (PDF)
- OpenPyXL (Excel)

**Frontend:**
- Next.js 14
- React 18
- TypeScript
- Recharts
- Axios

**Infraestrutura:**
- Docker Compose
- Redis

## 🚀 Como Rodar
```bash
# Subir todos os containers
docker-compose up -d

# Popular banco com dados demo
docker-compose exec app python -m src.jobs.seed_demo

# Acessar
Frontend: http://localhost:3000
API: http://localhost:8000
Docs: http://localhost:8000/docs
```

## 📊 Status Atual

- **Ambiente:** Demo/Desenvolvimento
- **Dados:** 100 processos de demonstração
- **Versão:** 2.0.0

## 🔒 Privacidade

Este é um repositório **PRIVADO**. Não compartilhar credenciais ou dados sensíveis.

---

**Desenvolvido com ❤️ para modernizar o monitoramento judicial**
