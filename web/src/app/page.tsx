'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import './dashboard.css';

interface Stats {
  por_tribunal: { [key: string]: number };
  por_relevancia: { [key: string]: number };
  por_tipo: { [key: string]: number };
  total: number;
}

interface Processo {
  id: number;
  numero_cnj: string;
  tribunal: string;
  tipo_processo: string;
  classe: string;
  comarca: string;
  relevance: string;
  valor_causa: number | null;
}

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [processos, setProcessos] = useState<Processo[]>([]);
  const [novosHoje, setNovosHoje] = useState(0);
  const [loading, setLoading] = useState(true);
  
  const [filtroTribunal, setFiltroTribunal] = useState('');
  const [filtroRelevancia, setFiltroRelevancia] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');

  useEffect(() => {
    fetchData();
  }, [filtroTribunal, filtroRelevancia, filtroTipo]);

  async function fetchData() {
    try {
      setLoading(true);
      
      const statsRes = await fetch('http://localhost:8000/processes/stats');
      const statsData = await statsRes.json();
      setStats(statsData);

      const novosRes = await fetch('http://localhost:8000/processes/novos-hoje');
      const novosData = await novosRes.json();
      setNovosHoje(novosData.novos_hoje);

      const params = new URLSearchParams();
      params.append('page_size', '200');
      if (filtroTribunal) params.append('tribunal', filtroTribunal);
      if (filtroRelevancia) params.append('relevancia', filtroRelevancia);
      if (filtroTipo) params.append('tipo_processo', filtroTipo);
      
      const processosRes = await fetch(`http://localhost:8000/processes?${params.toString()}`);
      const processosData = await processosRes.json();
      setProcessos(processosData.items || []);
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
      setProcessos([]);
    } finally {
      setLoading(false);
    }
  }

  if (loading && !stats) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚖️</div>
          <div>Carregando dados...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <main className="dashboard-main">
        <h1 className="dashboard-title">📊 Dashboard - Processos Judiciais</h1>

        <div className="kpis">
          <div className="kpi-card">
            <div className="kpi-value">{stats?.total || 0}</div>
            <div className="kpi-label">Total de Processos</div>
          </div>
          <div className="kpi-card kpi-new">
            <div className="kpi-value" style={{ color: '#10b981' }}>{novosHoje}</div>
            <div className="kpi-label">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                ✨ Novos Hoje
              </span>
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{stats?.por_relevancia?.['Alta'] || 0}</div>
            <div className="kpi-label">Alta Relevância</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{stats?.por_tribunal?.['TJSP'] || 0}</div>
            <div className="kpi-label">TJSP</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-value">{stats?.por_tribunal?.['TJBA'] || 0}</div>
            <div className="kpi-label">TJBA</div>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat-card">
            <h3>📍 Por Tribunal</h3>
            {stats && Object.entries(stats.por_tribunal).map(([tribunal, count]) => (
              <div key={tribunal} className="stat-item">
                <span>{tribunal}</span>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
          <div className="stat-card">
            <h3>🔥 Por Relevância</h3>
            {stats && Object.entries(stats.por_relevancia).map(([relevancia, count]) => (
              <div key={relevancia} className="stat-item">
                <span>{relevancia}</span>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
          <div className="stat-card">
            <h3>📑 Por Tipo</h3>
            {stats && Object.entries(stats.por_tipo).map(([tipo, count]) => (
              <div key={tipo} className="stat-item">
                <span>{tipo}</span>
                <strong>{count}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="filters-section">
          <h2>🔍 Filtrar Processos</h2>
          <div className="filters-grid">
            <div className="filter-group">
              <label>Tribunal:</label>
              <select value={filtroTribunal} onChange={(e) => setFiltroTribunal(e.target.value)} className="filter-select">
                <option value="">Todos</option>
                <option value="TJSP">TJSP</option>
                <option value="TJBA">TJBA</option>
              </select>
            </div>
            <div className="filter-group">
              <label>Relevância:</label>
              <select value={filtroRelevancia} onChange={(e) => setFiltroRelevancia(e.target.value)} className="filter-select">
                <option value="">Todas</option>
                <option value="Alta">Alta</option>
                <option value="Média">Média</option>
                <option value="Baixa">Baixa</option>
              </select>
            </div>
            <div className="filter-group">
              <label>Tipo:</label>
              <select value={filtroTipo} onChange={(e) => setFiltroTipo(e.target.value)} className="filter-select">
                <option value="">Todos</option>
                <option value="Inventário">Inventário</option>
                <option value="Divórcio">Divórcio</option>
              </select>
            </div>
          </div>
          {(filtroTribunal || filtroRelevancia || filtroTipo) && (
            <button 
              onClick={() => { setFiltroTribunal(''); setFiltroRelevancia(''); setFiltroTipo(''); }} 
              className="clear-filters-btn"
            >
              ✕ Limpar Filtros
            </button>
          )}
        </div>

        <div className="processes-section">
          <h2>📋 Processos Encontrados: {processos?.length || 0}</h2>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>Carregando...</div>
          ) : processos && processos.length > 0 ? (
            <div className="processes-grid">
              {processos.map((processo) => (
                <Link href={`/processo/${processo.id}`} key={processo.id} className="process-card">
                  <div className="process-header">
                    <span className={`badge ${processo.relevance?.toLowerCase()}`}>{processo.relevance}</span>
                    <span className="tribunal-badge">{processo.tribunal}</span>
                  </div>
                  <div className="process-number">{processo.numero_cnj}</div>
                  <div className="process-info">
                    <div>📑 {processo.tipo_processo}</div>
                    <div>🏛️ {processo.comarca}</div>
                    {processo.valor_causa && (<div>💰 R$ {processo.valor_causa.toLocaleString('pt-BR')}</div>)}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              Nenhum processo encontrado com os filtros selecionados.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
