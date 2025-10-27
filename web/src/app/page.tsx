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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const statsRes = await fetch('http://localhost:8000/processes/stats');
        const statsData = await statsRes.json();
        setStats(statsData);

        const processosRes = await fetch('http://localhost:8000/processes?page_size=20');
        const processosData = await processosRes.json();
        setProcessos(processosData.items);
      } catch (error) {
        console.error('Erro ao buscar dados:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
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

        <div className="processes-section">
          <h2>📋 Últimos Processos</h2>
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
        </div>
      </main>
    </div>
  );
}
