'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import {
  PieChart, Pie, Cell, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

interface Stats {
  por_tribunal: Array<{ tribunal: string; total: number }>;
  por_relevancia: Array<{ relevancia: string; total: number }>;
  por_classe: Array<{ classe: string; total: number }>;
  por_mes: Array<{ mes: string; total: number }>;
  valor_por_tribunal: Array<{ tribunal: string; valor: number }>;
  total_geral: number;
  valor_total: number;
}

const COLORS = {
  primary: '#6366f1',
  secondary: '#8b5cf6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
};

export default function AnalyticsDashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get<Stats>('http://localhost:8000/stats');
      setStats(response.data);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar estatísticas');
      console.error('Erro:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          {label && <p className="recharts-tooltip-label">{label}</p>}
          {payload.map((entry: any, index: number) => (
            <p key={index} className="recharts-tooltip-item">
              <span style={{ color: entry.color }}>{entry.name}:</span>
              <span className="recharts-tooltip-item-value">
                {typeof entry.value === 'number' && entry.value > 1000
                  ? formatCurrency(entry.value)
                  : entry.value}
              </span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <section className="analytics-section">
        <div className="section-header">
          <h2 className="section-title">📊 Analytics Dashboard</h2>
        </div>
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Carregando estatísticas...</p>
        </div>
      </section>
    );
  }

  if (error || !stats) {
    return (
      <section className="analytics-section">
        <div className="section-header">
          <h2 className="section-title">📊 Analytics Dashboard</h2>
        </div>
        <div className="error-state">
          <p>❌ {error}</p>
          <button onClick={fetchStats} className="retry-button">
            🔄 Tentar Novamente
          </button>
        </div>
      </section>
    );
  }

  const highRelevanceCount = stats.por_relevancia
    .filter(r => r.relevancia === 'Alta' || r.relevancia === 'URGENTE')
    .reduce((sum, r) => sum + r.total, 0);

  return (
    <section className="analytics-section">
      <div className="section-header">
        <h2 className="section-title">📊 Analytics Dashboard</h2>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon">📈</div>
          <div className="kpi-content">
            <div className="kpi-label">
              Total de Processos
              <span className="chart-info-icon">
                ℹ️
                <span className="info-tooltip">Número total de processos no sistema</span>
              </span>
            </div>
            <div className="kpi-value">{stats.total_geral}</div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon">💰</div>
          <div className="kpi-content">
            <div className="kpi-label">
              Valor Total em Causa
              <span className="chart-info-icon">
                ℹ️
                <span className="info-tooltip">Soma de todos os valores em causa</span>
              </span>
            </div>
            <div className="kpi-value">{formatCurrency(stats.valor_total)}</div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon">🔥</div>
          <div className="kpi-content">
            <div className="kpi-label">
              Alta Relevância
              <span className="chart-info-icon">
                ℹ️
                <span className="info-tooltip">Processos com relevância alta ou urgente</span>
              </span>
            </div>
            <div className="kpi-value">{highRelevanceCount}</div>
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3 className="chart-title">
            🏛️ Processos por Tribunal
            <span className="chart-info-icon">
              ℹ️
              <span className="info-tooltip">Distribuição por tribunal (TJSP/TJBA)</span>
            </span>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats.por_tribunal}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ tribunal, total }) => `${tribunal}: ${total}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="total"
                nameKey="tribunal"
              >
                {stats.por_tribunal.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index === 0 ? COLORS.primary : COLORS.secondary} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3 className="chart-title">
            🔥 Processos por Relevância
            <span className="chart-info-icon">
              ℹ️
              <span className="info-tooltip">Classificação por nível de urgência</span>
            </span>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.por_relevancia}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="relevancia" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="total" fill={COLORS.info} radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3 className="chart-title">
            📋 Processos por Tipo
            <span className="chart-info-icon">
              ℹ️
              <span className="info-tooltip">Divórcio vs Inventário</span>
            </span>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats.por_classe}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ classe, total }) => `${classe}: ${total}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="total"
                nameKey="classe"
              >
                {stats.por_classe.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={index === 0 ? COLORS.danger : COLORS.warning} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3 className="chart-title">
            💵 Valor em Causa por Tribunal
            <span className="chart-info-icon">
              ℹ️
              <span className="info-tooltip">Soma dos valores em causa por tribunal</span>
            </span>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.valor_por_tribunal}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="tribunal" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="valor" fill={COLORS.success} radius={[8, 8, 0, 0]} name="Valor" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card chart-card-wide">
          <h3 className="chart-title">
            📅 Timeline de Processos
            <span className="chart-info-icon">
              ℹ️
              <span className="info-tooltip">Evolução mensal dos processos</span>
            </span>
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats.por_mes}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="mes" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="total" 
                stroke={COLORS.primary} 
                strokeWidth={3}
                dot={{ fill: COLORS.primary, r: 6 }}
                activeDot={{ r: 8 }}
                name="Processos"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
