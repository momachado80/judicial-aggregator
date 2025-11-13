'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import AdvancedFilters, { FilterValues } from '@/components/AdvancedFilters';
import { extrairComarcaEData } from '@/utils/cnj';
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
  data_ajuizamento: string | null;
  status?: string;
}

type StatusTab = 'todos' | 'interesse' | 'descartado' | 'pendente';

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [processos, setProcessos] = useState<Processo[]>([]);
  const [novosHoje, setNovosHoje] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<FilterValues>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [activeTab, setActiveTab] = useState<StatusTab>('todos');

  useEffect(() => {
    fetchData();
  }, [filters, currentPage, activeTab]);

  async function fetchData() {
    try {
      setLoading(true);
      
      const statsRes = await fetch('https://judicial-aggregator-production.up.railway.app/processes/stats');
      const statsData = await statsRes.json();
      setStats(statsData);

      const novosRes = await fetch('https://judicial-aggregator-production.up.railway.app/processes/novos-hoje');
      const novosData = await novosRes.json();
      setNovosHoje(novosData.novos_hoje);

      const queryParams = new URLSearchParams({
        page: currentPage.toString(),
        page_size: '20',
      });

      if (activeTab !== 'todos') {
        queryParams.append('status', activeTab);
      }

      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          queryParams.append(key, value);
        }
      });

      const processosRes = await fetch(`https://judicial-aggregator-production.up.railway.app/processes?${queryParams.toString()}`);
      const processosData = await processosRes.json();
      setProcessos(processosData.items);
      setTotalPages(processosData.total_pages);
      setTotal(processosData.total);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
    } finally {
      setLoading(false);
    }
  }

  const handleFilterChange = (newFilters: FilterValues) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  const handleTabChange = (tab: StatusTab) => {
    setActiveTab(tab);
    setCurrentPage(1);
  };

  const handleStatusChange = async (processoId: number, novoStatus: string, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    const processoAtual = processos.find(p => p.id === processoId);
    const statusAtual = processoAtual?.status || 'pendente';
    const statusFinal = statusAtual === novoStatus ? 'pendente' : novoStatus;
    
    try {
      const response = await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${processoId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: statusFinal }),
      });

      if (response.ok) {
        setProcessos(processos.map(p => 
          p.id === processoId ? { ...p, status: statusFinal } : p
        ));
        
        if (activeTab === statusAtual && statusFinal === 'pendente') {
          setProcessos(processos.filter(p => p.id !== processoId));
          setTotal(total - 1);
        }
      }
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
      alert('Erro ao atualizar status');
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-main">
        <h1 className="dashboard-title">⚖️ Judicial Aggregator</h1>

        {stats && (
          <div className="kpis">
            <div className="kpi-card">
              <div className="kpi-value">{stats.total.toLocaleString()}</div>
              <div className="kpi-label">TOTAL DE PROCESSOS</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">{novosHoje}</div>
              <div className="kpi-label">NOVOS HOJE</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">{stats.por_relevancia['Alta'] || stats.por_relevancia['alta'] || 0}</div>
              <div className="kpi-label">ALTA RELEVÂNCIA</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">
                TJSP: {stats.por_tribunal['TJSP'] || 0}<br/>
                TJBA: {stats.por_tribunal['TJBA'] || 0}
              </div>
              <div className="kpi-label">TRIBUNAIS</div>
            </div>
          </div>
        )}

        {/* ABAS DE FILTRO POR STATUS */}
        <div style={{
          background: 'white',
          padding: '8px',
          borderRadius: '8px',
          marginBottom: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          display: 'flex',
          gap: '8px'
        }}>
          <button
            onClick={() => handleTabChange('todos')}
            style={{
              padding: '12px 24px',
              background: activeTab === 'todos' ? '#3b82f6' : 'transparent',
              color: activeTab === 'todos' ? 'white' : '#64748b',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            📋 Todos
          </button>
          <button
            onClick={() => handleTabChange('pendente')}
            style={{
              padding: '12px 24px',
              background: activeTab === 'pendente' ? '#3b82f6' : 'transparent',
              color: activeTab === 'pendente' ? 'white' : '#64748b',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            ⏳ Pendentes
          </button>
          <button
            onClick={() => handleTabChange('interesse')}
            style={{
              padding: '12px 24px',
              background: activeTab === 'interesse' ? '#10b981' : 'transparent',
              color: activeTab === 'interesse' ? 'white' : '#64748b',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            ⭐ De Interesse
          </button>
          <button
            onClick={() => handleTabChange('descartado')}
            style={{
              padding: '12px 24px',
              background: activeTab === 'descartado' ? '#ef4444' : 'transparent',
              color: activeTab === 'descartado' ? 'white' : '#64748b',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            ❌ Descartados
          </button>
        </div>

        <AdvancedFilters onFilterChange={handleFilterChange} currentFilters={filters} />

        <div style={{ 
          background: 'white', 
          padding: '16px 24px', 
          borderRadius: '8px', 
          marginBottom: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
              {total.toLocaleString()} processo(s) encontrado(s)
            </div>
            {Object.keys(filters).filter(k => filters[k as keyof FilterValues]).length > 0 && (
              <div style={{ fontSize: '14px', color: '#64748b', marginTop: '4px' }}>
                {Object.keys(filters).filter(k => filters[k as keyof FilterValues]).length} filtro(s) ativo(s)
              </div>
            )}
          </div>
          {loading && <div style={{ color: '#3b82f6' }}>Carregando...</div>}
        </div>

        <div className="processes-grid">
          {processos.map((p) => {
            const { comarca, data } = extrairComarcaEData(p.numero_cnj, p.tribunal);
            const statusAtual = p.status || 'pendente';
            
            return (
              <div key={p.id} style={{ position: 'relative' }}>
                <Link href={`/processo/${p.id}`} className="process-card">
                  <div className="process-header">
                    <span className={`badge ${p.relevance?.toLowerCase()}`}>
                      {p.relevance}
                    </span>
                    <span className="tribunal-badge">{p.tribunal}</span>
                  </div>
                  <div className="process-number">{p.numero_cnj}</div>
                  <div className="process-info">
                    <div><strong>Tipo:</strong> {p.tipo_processo}</div>
                    <div><strong>Comarca:</strong> {comarca}</div>
                    <div><strong>Data:</strong> {data || 'N/A'}</div>
                    {p.valor_causa && (
                      <div><strong>Valor:</strong> {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(p.valor_causa)}</div>
                    )}
                  </div>
                </Link>
                
                <div style={{
                  display: 'flex',
                  gap: '8px',
                  marginTop: '12px',
                  justifyContent: 'center'
                }}>
                  <button
                    onClick={(e) => handleStatusChange(p.id, 'interesse', e)}
                    style={{
                      padding: '8px 16px',
                      background: statusAtual === 'interesse' ? '#10b981' : '#e0e7ff',
                      color: statusAtual === 'interesse' ? 'white' : '#4f46e5',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '13px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                    title={statusAtual === 'interesse' ? 'Clique para desmarcar' : 'Marcar como interesse'}
                  >
                    {statusAtual === 'interesse' ? '✓' : '⭐'} Interesse
                  </button>
                  
                  <button
                    onClick={(e) => handleStatusChange(p.id, 'descartado', e)}
                    style={{
                      padding: '8px 16px',
                      background: statusAtual === 'descartado' ? '#ef4444' : '#fee2e2',
                      color: statusAtual === 'descartado' ? 'white' : '#dc2626',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '13px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                    title={statusAtual === 'descartado' ? 'Clique para desmarcar' : 'Marcar como descartado'}
                  >
                    {statusAtual === 'descartado' ? '✓' : '❌'} Descartar
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '12px',
          marginTop: '32px',
          paddingBottom: '32px'
        }}>
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            style={{
              padding: '10px 20px',
              background: currentPage === 1 ? '#e2e8f0' : '#3b82f6',
              color: currentPage === 1 ? '#94a3b8' : 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: '600',
              cursor: currentPage === 1 ? 'not-allowed' : 'pointer'
            }}
          >
            ← Anterior
          </button>
          <div style={{
            padding: '10px 20px',
            background: 'white',
            borderRadius: '8px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center'
          }}>
            Página {currentPage} de {totalPages}
          </div>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage >= totalPages}
            style={{
              padding: '10px 20px',
              background: currentPage >= totalPages ? '#e2e8f0' : '#3b82f6',
              color: currentPage >= totalPages ? '#94a3b8' : 'white',
              border: 'none',
              borderRadius: '8px',
              fontWeight: '600',
              cursor: currentPage >= totalPages ? 'not-allowed' : 'pointer'
            }}
          >
            Próxima →
          </button>
        </div>
      </div>
    </div>
  );
}
