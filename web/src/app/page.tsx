'use client';
import { useState } from 'react';

export default function Home() {
  const [tiposSelecionados, setTiposSelecionados] = useState(['Inventário', 'Divórcio Litigioso', 'Divórcio Consensual']);
  const [quantidade, setQuantidade] = useState(100);
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [interesseIds, setInteresseIds] = useState(new Set());
  const [descartadosIds, setDescartadosIds] = useState(new Set());
  const [abaAtiva, setAbaAtiva] = useState('busca');

  const buscarProcessos = async () => {
    setLoading(true);
    try {
      const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tribunais: ['TJSP'],
          tipos_processo: tiposSelecionados,
          quantidade: quantidade,
          usar_cache: false
        })
      });
      const data = await response.json();
      
      if (Array.isArray(data)) {
        setProcessos(data);
      } else {
        alert('Erro: ' + JSON.stringify(data));
      }
    } catch (error) {
      console.error('Erro ao buscar:', error);
      alert('Erro ao buscar processos: ' + error);
    }
    setLoading(false);
  };

  const marcarInteresse = (numero) => {
    const novos = new Set(interesseIds);
    novos.add(numero);
    setInteresseIds(novos);
    descartadosIds.delete(numero);
    setDescartadosIds(new Set(descartadosIds));
  };

  const marcarDescartado = (numero) => {
    const novos = new Set(descartadosIds);
    novos.add(numero);
    setDescartadosIds(novos);
    interesseIds.delete(numero);
    setInteresseIds(new Set(interesseIds));
  };

  const processosBusca = processos.filter(p => !interesseIds.has(p.numero) && !descartadosIds.has(p.numero));
  const processosInteresse = processos.filter(p => interesseIds.has(p.numero));
  const processosDescartados = processos.filter(p => descartadosIds.has(p.numero));

  const formatarData = (data) => {
    if (!data) return '-';
    const ano = data.substring(0, 4);
    const mes = data.substring(4, 6);
    const dia = data.substring(6, 8);
    return `${dia}/${mes}/${ano}`;
  };

  const ProcessoCard = ({ processo }) => (
    <div style={{
      backgroundColor: 'white',
      padding: '20px',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      border: '1px solid #e5e7eb'
    }}>
      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>Número:</p>
        <a 
          href={processo.url_tjsp} 
          target="_blank" 
          rel="noopener noreferrer"
          style={{ color: '#2563eb', fontFamily: 'monospace', fontSize: '13px', fontWeight: '600' }}
        >
          {processo.numero}
        </a>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
        <div>
          <p style={{ fontSize: '11px', color: '#6b7280' }}>Tipo:</p>
          <p style={{ fontWeight: '600', fontSize: '14px', margin: 0 }}>{processo.tipo}</p>
        </div>
        <div>
          <p style={{ fontSize: '11px', color: '#6b7280' }}>Data:</p>
          <p style={{ fontWeight: '600', fontSize: '14px', margin: 0 }}>{formatarData(processo.data_ajuizamento)}</p>
        </div>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontSize: '11px', color: '#6b7280' }}>Comarca:</p>
        <p style={{ fontWeight: '600', color: '#7c3aed', fontSize: '14px', margin: 0 }}>{processo.comarca}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <button
          onClick={() => marcarInteresse(processo.numero)}
          style={{
            backgroundColor: '#10b981',
            color: 'white',
            padding: '10px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '13px'
          }}
        >
          ⭐ Interesse
        </button>
        <button
          onClick={() => marcarDescartado(processo.numero)}
          style={{
            backgroundColor: '#ef4444',
            color: 'white',
            padding: '10px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '13px'
          }}
        >
          🗑️ Descartar
        </button>
      </div>
    </div>
  );

  const getProcessosAba = () => {
    if (abaAtiva === 'interesse') return processosInteresse;
    if (abaAtiva === 'descartados') return processosDescartados;
    return processosBusca;
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
      <nav style={{
        background: 'linear-gradient(to right, #4f46e5, #7c3aed)',
        color: 'white',
        padding: '20px 24px'
      }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>
          ⚖️ Judicial Aggregator - DataJud
        </h1>
      </nav>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
        {/* Filtros */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '24px',
          marginBottom: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '20px' }}>
            🔍 Buscar Processos (TJSP)
          </h2>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>
              Tipos de Processo:
            </label>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              {['Inventário', 'Divórcio Litigioso', 'Divórcio Consensual'].map(t => (
                <label key={t} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={tiposSelecionados.includes(t)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setTiposSelecionados([...tiposSelecionados, t]);
                      } else {
                        setTiposSelecionados(tiposSelecionados.filter(x => x !== t));
                      }
                    }}
                    style={{ width: '18px', height: '18px' }}
                  />
                  <span style={{ fontSize: '15px' }}>{t}</span>
                </label>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>
              Quantidade:
            </label>
            <select 
              value={quantidade} 
              onChange={(e) => setQuantidade(Number(e.target.value))}
              style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db', fontSize: '15px' }}
            >
              <option value={50}>50 processos</option>
              <option value={100}>100 processos</option>
              <option value={200}>200 processos</option>
              <option value={500}>500 processos</option>
              <option value={1000}>1000 processos</option>
            </select>
          </div>

          <button
            onClick={buscarProcessos}
            disabled={loading || tiposSelecionados.length === 0}
            style={{
              width: '100%',
              background: loading ? '#9ca3af' : 'linear-gradient(to right, #4f46e5, #7c3aed)',
              color: 'white',
              padding: '16px',
              borderRadius: '8px',
              border: 'none',
              fontWeight: 'bold',
              fontSize: '16px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? '⏳ Buscando...' : '🔍 BUSCAR PROCESSOS'}
          </button>
        </div>

        {/* Resultados */}
        {processos.length > 0 && (
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            {/* Stats */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(3, 1fr)', 
              gap: '16px', 
              marginBottom: '20px' 
            }}>
              <div style={{ backgroundColor: '#dcfce7', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
                <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#166534', margin: 0 }}>{processos.length}</p>
                <p style={{ fontSize: '13px', color: '#166534', margin: 0 }}>Total Encontrado</p>
              </div>
              <div style={{ backgroundColor: '#fef3c7', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
                <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#92400e', margin: 0 }}>{processosInteresse.length}</p>
                <p style={{ fontSize: '13px', color: '#92400e', margin: 0 }}>Interesse</p>
              </div>
              <div style={{ backgroundColor: '#fee2e2', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
                <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#991b1b', margin: 0 }}>{processosDescartados.length}</p>
                <p style={{ fontSize: '13px', color: '#991b1b', margin: 0 }}>Descartados</p>
              </div>
            </div>

            {/* Abas */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
              <button
                onClick={() => setAbaAtiva('busca')}
                style={{
                  padding: '12px 24px',
                  borderRadius: '8px',
                  border: 'none',
                  fontWeight: '600',
                  cursor: 'pointer',
                  backgroundColor: abaAtiva === 'busca' ? '#4f46e5' : '#e5e7eb',
                  color: abaAtiva === 'busca' ? 'white' : '#374151'
                }}
              >
                📋 Busca ({processosBusca.length})
              </button>
              <button
                onClick={() => setAbaAtiva('interesse')}
                style={{
                  padding: '12px 24px',
                  borderRadius: '8px',
                  border: 'none',
                  fontWeight: '600',
                  cursor: 'pointer',
                  backgroundColor: abaAtiva === 'interesse' ? '#eab308' : '#e5e7eb',
                  color: abaAtiva === 'interesse' ? 'white' : '#374151'
                }}
              >
                ⭐ Interesse ({processosInteresse.length})
              </button>
              <button
                onClick={() => setAbaAtiva('descartados')}
                style={{
                  padding: '12px 24px',
                  borderRadius: '8px',
                  border: 'none',
                  fontWeight: '600',
                  cursor: 'pointer',
                  backgroundColor: abaAtiva === 'descartados' ? '#6b7280' : '#e5e7eb',
                  color: abaAtiva === 'descartados' ? 'white' : '#374151'
                }}
              >
                🗑️ Descartados ({processosDescartados.length})
              </button>
            </div>

            {/* Grid de Processos */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: '16px'
            }}>
              {getProcessosAba().map(p => (
                <ProcessoCard key={p.numero} processo={p} />
              ))}
            </div>

            {getProcessosAba().length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                <p style={{ fontSize: '16px' }}>Nenhum processo nesta aba</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
