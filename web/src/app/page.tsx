'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import Link from 'next/link';
import AnalyticsDashboard from './components/AnalyticsDashboard';

interface Process {
  id: number;
  numero_cnj: string;
  tribunal: string;
  classe_tpu: string;
  comarca: string;
  vara: string;
  valor_causa: number | null;
  relevance: string;
}

interface ProcessResponse {
  items: Process[];
  total: number;
}

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const [processes, setProcesses] = useState<Process[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(false);
  
  const [searchCNJ, setSearchCNJ] = useState('');
  const [selectedTribunal, setSelectedTribunal] = useState('');
  const [selectedClasse, setSelectedClasse] = useState('');
  const [selectedRelevance, setSelectedRelevance] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const pageSize = 20;

  const [isExporting, setIsExporting] = useState(false);
  const [isExportingExcel, setIsExportingExcel] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProcesses();
    }, 500);
    return () => clearTimeout(timer);
  }, [searchCNJ, selectedTribunal, selectedClasse, selectedRelevance, currentPage]);

  const checkHealth = async () => {
    try {
      await axios.get('http://localhost:8000/health');
      setIsOnline(true);
    } catch {
      setIsOnline(false);
    }
  };

  const fetchProcesses = async () => {
    try {
      setIsSearching(true);
      setLoading(true);
      
      const params: any = {
        page: currentPage,
        page_size: pageSize,
      };
      
      if (searchCNJ) params.numero_cnj = searchCNJ;
      if (selectedTribunal) params.tribunal = selectedTribunal;
      if (selectedClasse) params.classe_tpu = selectedClasse;
      if (selectedRelevance) params.relevance = selectedRelevance;
      
      const response = await axios.get<ProcessResponse>('http://localhost:8000/processes', { params });
      
      setProcesses(response.data.items);
      setTotalResults(response.data.total);
      setTotalPages(Math.ceil(response.data.total / pageSize));
      setError(null);
    } catch (err) {
      setError('Erro ao carregar processos');
      console.error('Erro:', err);
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  const handleExportPDF = async () => {
    try {
      setIsExporting(true);
      
      const params: any = {};
      if (searchCNJ) params.numero_cnj = searchCNJ;
      if (selectedTribunal) params.tribunal = selectedTribunal;
      if (selectedClasse) params.classe_tpu = selectedClasse;
      if (selectedRelevance) params.relevance = selectedRelevance;
      
      const queryString = new URLSearchParams(params).toString();
      const url = `http://localhost:8000/export/pdf${queryString ? '?' + queryString : ''}`;
      
      const response = await axios.get(url, {
        responseType: 'blob',
      });
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      link.download = `processos_${timestamp}.pdf`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
    } catch (err) {
      console.error('Erro ao exportar PDF:', err);
      alert('Erro ao gerar PDF. Tente novamente.');
    } finally {
      setIsExporting(false);
    }
  };


  const handleExportExcel = async () => {
    try {
      setIsExportingExcel(true);
      
      const params: any = {};
      if (searchCNJ) params.numero_cnj = searchCNJ;
      if (selectedTribunal) params.tribunal = selectedTribunal;
      if (selectedClasse) params.classe_tpu = selectedClasse;
      if (selectedRelevance) params.relevance = selectedRelevance;
      
      const queryString = new URLSearchParams(params).toString();
      const url = `http://localhost:8000/export/excel${queryString ? '?' + queryString : ''}`;
      
      const response = await axios.get(url, {
        responseType: 'blob',
      });
      
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      link.download = `processos_${timestamp}.xlsx`;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      
    } catch (err) {
      console.error('Erro ao exportar Excel:', err);
      alert('Erro ao gerar Excel. Tente novamente.');
    } finally {
      setIsExportingExcel(false);
    }
  };

  const handleFilterChange = () => {
    setCurrentPage(1);
  };

  const formatCurrency = (value: number | null) => {
    if (!value) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const getClasseLabel = (classe: string) => {
    return classe === '8015' ? 'Divórcio' : 'Inventário';
  };

  const urgentProcesses = processes.filter(p => p.relevance === 'URGENTE');
  const otherProcesses = processes.filter(p => p.relevance !== 'URGENTE');

  if (!mounted) {
    return null;
  }

  if (loading && processes.length === 0) {
    return (
      <div className="container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Carregando processos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo">⚖️</div>
            <div>
              <h1 className="header-title">Judicial Aggregator</h1>
              <p className="header-subtitle">Monitoramento Inteligente de Processos</p>
            </div>
          </div>
          <div className={`status-indicator ${isOnline ? 'online' : 'offline'}`}>
            <span className="status-dot"></span>
            {isOnline ? 'Online' : 'Offline'}
          </div>
        </div>
      </header>

      <AnalyticsDashboard />

      <main className="main-content">
        <section className="search-section">
          <h2 className="section-title">🔍 Buscar Processos</h2>
          
          <div className="filters-grid">
            <div className="filter-group">
              <label>🔎 Buscar por CNJ:</label>
              <div className="search-input-wrapper">
                <input
                  type="text"
                  className="filter-input"
                  placeholder="Digite o número CNJ..."
                  value={searchCNJ}
                  onChange={(e) => {
                    setSearchCNJ(e.target.value);
                    handleFilterChange();
                  }}
                />
                {isSearching && <div className="input-spinner"></div>}
              </div>
            </div>

            <div className="filter-group">
              <label>🏛️ Tribunal:</label>
              <select
                className="filter-select"
                value={selectedTribunal}
                onChange={(e) => {
                  setSelectedTribunal(e.target.value);
                  handleFilterChange();
                }}
              >
                <option value="">Todos</option>
                <option value="TJSP">TJSP</option>
                <option value="TJBA">TJBA</option>
              </select>
            </div>

            <div className="filter-group">
              <label>📋 Tipo de Processo:</label>
              <select
                className="filter-select"
                value={selectedClasse}
                onChange={(e) => {
                  setSelectedClasse(e.target.value);
                  handleFilterChange();
                }}
              >
                <option value="">Todos</option>
                <option value="8015">Divórcio</option>
                <option value="8019">Inventário</option>
              </select>
            </div>

            <div className="filter-group">
              <label>🔥 Relevância:</label>
              <select
                className="filter-select"
                value={selectedRelevance}
                onChange={(e) => {
                  setSelectedRelevance(e.target.value);
                  handleFilterChange();
                }}
              >
                <option value="">Todas</option>
                <option value="Alta">Alta</option>
                <option value="Média">Média</option>
                <option value="Baixa">Baixa</option>
              </select>
            </div>
          </div>

          <div className="results-count">
            📊 Mostrando <strong>{processes.length}</strong> de <strong>{totalResults}</strong> processos
          </div>

          <div className="export-section">
            <button 
              className="export-btn export-btn-excel"
              onClick={handleExportExcel}
              disabled={isExportingExcel || processes.length === 0}
            >
              {isExportingExcel ? (
                <>
                  <span className="btn-spinner"></span>
                  Gerando Excel...
                </>
              ) : (
                <>
                  📊 Exportar Excel
                </>
              )}
            </button>
            <button 
              className="export-btn"
              onClick={handleExportPDF}
              disabled={isExporting || processes.length === 0}
            >
              {isExporting ? (
                <>
                  <span className="btn-spinner"></span>
                  Gerando PDF...
                </>
              ) : (
                <>
                  📄 Exportar PDF
                </>
              )}
            </button>
          </div>
        </section>

        <section className="processes-section">
          {urgentProcesses.length > 0 && (
            <div className="urgent-section">
              <h2 className="urgent-title">🚨 Processos Urgentes</h2>
              <div className="processes-grid">
                {urgentProcesses.map((process) => (
                  <Link 
                    href={`/processes/${process.id}`} 
                    key={process.id}
                    className="process-card"
                  >
                    <div className="process-header">
                      <span className="process-number">{process.numero_cnj}</span>
                      <span className={`relevance-badge ${process.relevance}`}>
                        {process.relevance}
                      </span>
                    </div>
                    <div className="process-info">
                      <div className="info-row">
                        <span className="info-label">🏛️ Tribunal:</span>
                        <span className="info-value">{process.tribunal}</span>
                      </div>
                      <div className="info-row">
                        <span className="info-label">📋 Tipo:</span>
                        <span className="info-value">{getClasseLabel(process.classe_tpu)}</span>
                      </div>
                      <div className="info-row">
                        <span className="info-label">📍 Comarca:</span>
                        <span className="info-value">{process.comarca}</span>
                      </div>
                      <div className="info-row">
                        <span className="info-label">⚖️ Vara:</span>
                        <span className="info-value">{process.vara}</span>
                      </div>
                      <div className="info-row">
                        <span className="info-label">💰 Valor:</span>
                        <span className="info-value">{formatCurrency(process.valor_causa)}</span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          <h2 className="section-subtitle">📁 Todos os Processos</h2>
          {error && (
            <div className="no-results">
              <p>❌ {error}</p>
            </div>
          )}

          {!error && otherProcesses.length === 0 && (
            <div className="no-results">
              <p>Nenhum processo encontrado</p>
              <p className="no-results-hint">Tente ajustar os filtros</p>
            </div>
          )}

          {otherProcesses.length > 0 && (
            <div className="processes-grid">
              {otherProcesses.map((process) => (
                <Link 
                  href={`/processes/${process.id}`} 
                  key={process.id}
                  className="process-card"
                >
                  <div className="process-header">
                    <span className="process-number">{process.numero_cnj}</span>
                    <span className={`relevance-badge ${process.relevance}`}>
                      {process.relevance}
                    </span>
                  </div>
                  <div className="process-info">
                    <div className="info-row">
                      <span className="info-label">🏛️ Tribunal:</span>
                      <span className="info-value">{process.tribunal}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">📋 Tipo:</span>
                      <span className="info-value">{getClasseLabel(process.classe_tpu)}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">📍 Comarca:</span>
                      <span className="info-value">{process.comarca}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">⚖️ Vara:</span>
                      <span className="info-value">{process.vara}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">💰 Valor:</span>
                      <span className="info-value">{formatCurrency(process.valor_causa)}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="pagination-btn"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                ← Anterior
              </button>

              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }

                return (
                  <button
                    key={pageNum}
                    className={`pagination-btn ${currentPage === pageNum ? 'active' : ''}`}
                    onClick={() => setCurrentPage(pageNum)}
                  >
                    {pageNum}
                  </button>
                );
              })}

              {totalPages > 5 && currentPage < totalPages - 2 && (
                <span className="pagination-dots">...</span>
              )}

              <button
                className="pagination-btn"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Próxima →
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
