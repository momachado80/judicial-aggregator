'use client';

import { useState, useEffect } from 'react';

interface AdvancedFiltersProps {
  onFilterChange: (filters: FilterValues) => void;
  currentFilters: FilterValues;
}

export interface FilterValues {
  tribunal?: string;
  relevancia?: string;
  tipo_processo?: string;
  data_ajuizamento_inicio?: string;
  data_ajuizamento_fim?: string;
  valor_causa_min?: string;
  valor_causa_max?: string;
  comarca?: string;
  numero_processo?: string;
}

export default function AdvancedFilters({ onFilterChange, currentFilters }: AdvancedFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [filters, setFilters] = useState<FilterValues>(currentFilters);
  const [comarcas, setComarcas] = useState<string[]>([]);

  useEffect(() => {
    loadComarcas();
  }, []);

  const loadComarcas = async () => {
    try {
      const res = await fetch('/api/processes/comarcas');
      const data = await res.json();
      setComarcas(data.comarcas || []);
    } catch (error) {
      console.error('Erro:', error);
    }
  };

  const handleFilterChange = (key: keyof FilterValues, value: string) => {
    setFilters({ ...filters, [key]: value || undefined });
  };

  const applyFilters = () => {
    onFilterChange(filters);
    setIsExpanded(false);
  };

  const clearFilters = () => {
    setFilters({});
    onFilterChange({});
  };

  const activeCount = Object.values(filters).filter(v => v).length;

  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    borderRadius: '8px',
    border: '2px solid #e2e8f0',
    fontSize: '14px',
    transition: 'all 0.2s',
    backgroundColor: 'white'
  };

  const labelStyle = {
    display: 'block',
    fontSize: '13px',
    fontWeight: '600' as const,
    marginBottom: '8px',
    color: '#475569'
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '16px',
      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      marginBottom: '24px',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px 24px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{ fontSize: '24px' }}>🔍</span>
          <div>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '700', color: 'white' }}>
              Filtros Avançados
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'rgba(255,255,255,0.8)' }}>
              Refine sua busca por processos
            </p>
          </div>
          {activeCount > 0 && (
            <span style={{
              background: '#fbbf24',
              color: '#78350f',
              fontSize: '12px',
              fontWeight: '700',
              padding: '4px 12px',
              borderRadius: '12px',
              marginLeft: '8px'
            }}>
              {activeCount} {activeCount === 1 ? 'filtro' : 'filtros'}
            </span>
          )}
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          style={{
            background: 'rgba(255,255,255,0.2)',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            padding: '10px 20px',
            borderRadius: '8px',
            transition: 'all 0.2s',
            backdropFilter: 'blur(10px)'
          }}
          onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.3)'}
          onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
        >
          {isExpanded ? '▲ Ocultar' : '▼ Mostrar Filtros'}
        </button>
      </div>

      {/* Filtros */}
      {isExpanded && (
        <div style={{ padding: '24px' }}>
          {/* Linha 1: Filtros Básicos */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginBottom: '20px'
          }}>
            <div>
              <label style={labelStyle}>🏛️ Tribunal</label>
              <select value={filters.tribunal || ''} onChange={(e) => handleFilterChange('tribunal', e.target.value)} style={inputStyle}>
                <option value="">Todos os tribunais</option>
                <option value="8.13">TJSP - São Paulo</option>
                <option value="8.05">TJBA - Bahia</option>
              </select>
            </div>

            <div>
              <label style={labelStyle}>⚠️ Relevância</label>
              <select value={filters.relevancia || ''} onChange={(e) => handleFilterChange('relevancia', e.target.value)} style={inputStyle}>
                <option value="">Todas</option>
                <option value="alta">🔴 Alta</option>
                <option value="media">🟡 Média</option>
                <option value="baixa">🟢 Baixa</option>
              </select>
            </div>

            <div>
              <label style={labelStyle}>📋 Tipo de Processo</label>
              <select value={filters.tipo_processo || ''} onChange={(e) => handleFilterChange('tipo_processo', e.target.value)} style={inputStyle}>
                <option value="">Todos os tipos</option>
                <option value="inventario">Inventário</option>
                <option value="divorcio">Divórcio</option>
              </select>
            </div>
          </div>

          {/* Linha 2: Datas */}
          <div style={{
            background: 'linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%)',
            padding: '16px',
            borderRadius: '12px',
            marginBottom: '20px'
          }}>
            <label style={{ ...labelStyle, marginBottom: '12px' }}>📅 Período de Ajuizamento</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <input
                  type="date"
                  value={filters.data_ajuizamento_inicio || ''}
                  onChange={(e) => handleFilterChange('data_ajuizamento_inicio', e.target.value)}
                  style={inputStyle}
                />
                <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>Data inicial</p>
              </div>
              <div>
                <input
                  type="date"
                  value={filters.data_ajuizamento_fim || ''}
                  onChange={(e) => handleFilterChange('data_ajuizamento_fim', e.target.value)}
                  style={inputStyle}
                />
                <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>Data final</p>
              </div>
            </div>
          </div>

          {/* Linha 3: Valores */}
          <div style={{
            background: 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)',
            padding: '16px',
            borderRadius: '12px',
            marginBottom: '20px'
          }}>
            <label style={{ ...labelStyle, marginBottom: '12px' }}>💰 Valor da Causa (R$)</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <input
                  type="number"
                  value={filters.valor_causa_min || ''}
                  onChange={(e) => handleFilterChange('valor_causa_min', e.target.value)}
                  placeholder="Valor mínimo"
                  style={inputStyle}
                  min="0"
                  step="1000"
                />
                <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>Valor mínimo</p>
              </div>
              <div>
                <input
                  type="number"
                  value={filters.valor_causa_max || ''}
                  onChange={(e) => handleFilterChange('valor_causa_max', e.target.value)}
                  placeholder="Valor máximo"
                  style={inputStyle}
                  min="0"
                  step="1000"
                />
                <p style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>Valor máximo</p>
              </div>
            </div>
          </div>

          {/* Linha 4: Localização e Busca */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
            <div>
              <label style={labelStyle}>📍 Comarca</label>
              <select value={filters.comarca || ''} onChange={(e) => handleFilterChange('comarca', e.target.value)} style={inputStyle}>
                <option value="">Todas as comarcas</option>
                {comarcas.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={labelStyle}>🔢 Número do Processo</label>
              <input
                type="text"
                value={filters.numero_processo || ''}
                onChange={(e) => handleFilterChange('numero_processo', e.target.value)}
                placeholder="Ex: 1015229-77.2023"
                style={inputStyle}
              />
            </div>
          </div>

          {/* Botões */}
          <div style={{ display: 'flex', gap: '12px', paddingTop: '20px', borderTop: '2px solid #f1f5f9' }}>
            <button
              onClick={applyFilters}
              style={{
                flex: 1,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                border: 'none',
                padding: '14px',
                borderRadius: '10px',
                fontWeight: '700',
                fontSize: '15px',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.5)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
              }}
            >
              🔍 Aplicar Filtros
            </button>
            <button
              onClick={clearFilters}
              style={{
                flex: 1,
                background: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
                color: 'white',
                border: 'none',
                padding: '14px',
                borderRadius: '10px',
                fontWeight: '700',
                fontSize: '15px',
                cursor: 'pointer',
                boxShadow: '0 4px 12px rgba(107, 114, 128, 0.3)',
                transition: 'all 0.2s'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(107, 114, 128, 0.4)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(107, 114, 128, 0.3)';
              }}
            >
              🗑️ Limpar Tudo
            </button>
          </div>
        </div>
      )}

      {/* Tags de filtros ativos (quando recolhido) */}
      {!isExpanded && activeCount > 0 && (
        <div style={{ padding: '16px 24px', borderTop: '1px solid #f1f5f9' }}>
          <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px', fontWeight: '600' }}>FILTROS ATIVOS:</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {Object.entries(filters).map(([key, value]) => {
              if (!value) return null;
              
              const labels: Record<string, string> = {
                tribunal: '🏛️ Tribunal',
                relevancia: '⚠️ Relevância',
                tipo_processo: '📋 Tipo',
                data_ajuizamento_inicio: '📅 Data início',
                data_ajuizamento_fim: '📅 Data fim',
                valor_causa_min: '💰 Valor mín',
                valor_causa_max: '💰 Valor máx',
                comarca: '📍 Comarca',
                numero_processo: '🔢 Processo'
              };
              
              return (
                <span
                  key={key}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    fontSize: '12px',
                    fontWeight: '600',
                    padding: '6px 12px',
                    borderRadius: '20px',
                    boxShadow: '0 2px 6px rgba(102, 126, 234, 0.3)'
                  }}
                >
                  {labels[key]}: {value}
                  <button
                    onClick={() => handleFilterChange(key as keyof FilterValues, '')}
                    style={{
                      background: 'rgba(255,255,255,0.3)',
                      border: 'none',
                      color: 'white',
                      cursor: 'pointer',
                      width: '18px',
                      height: '18px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      padding: 0
                    }}
                  >
                    ×
                  </button>
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
