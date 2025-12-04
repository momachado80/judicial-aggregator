'use client';
import { useState, useEffect } from 'react';

interface Processo {
  numero: string;
  tipo: string;
  comarca?: string;
  codigo_comarca?: string;
  tem_imovel?: boolean;
  data_ajuizamento?: string;
  ultimo_movimento?: string;
  url_tjsp: string;
}

export default function Home() {
  const [aba, setAba] = useState<'imoveis' | 'datajud'>('imoveis');
  const [processosImoveis, setProcessosImoveis] = useState<Processo[]>([]);
  const [processosDatajud, setProcessosDatajud] = useState<Processo[]>([]);
  const [loading, setLoading] = useState(false);
  const [filtroTipo, setFiltroTipo] = useState('todos');

  // Carregar processos com imóveis ao iniciar
  useEffect(() => {
    fetch('https://judicial-aggregator-production.up.railway.app/api/processos-com-imoveis')
      .then(res => res.json())
      .then(data => setProcessosImoveis(data.processos || []))
      .catch(err => console.error(err));
  }, []);

  const buscarDatajud = async () => {
    setLoading(true);
    try {
      const res = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tribunais: ['TJSP'],
          tipos_processo: ['Inventário', 'Divórcio Litigioso', 'Divórcio Consensual'],
          quantidade: 200,
          usar_cache: false,
          incluir_extintos: false
        })
      });
      const data = await res.json();
      setProcessosDatajud(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const processosFiltrados = (aba === 'imoveis' ? processosImoveis : processosDatajud).filter(p => {
    if (filtroTipo === 'todos') return true;
    return p.tipo.toLowerCase().includes(filtroTipo.toLowerCase());
  });

  const COMARCAS: Record<string, string> = {
    '0344': 'Marília', '0482': 'Presidente Prudente', '0368': 'Monte Alto',
    '0441': 'Pereira Barreto', '0405': 'Osasco', '0451': 'Piracicaba',
    '0322': 'Lins', '0356': 'Mirandópolis', '0471': 'Porto Feliz',
    '0362': 'Mogi das Cruzes', '0268': 'Itapecerica da Serra', '0272': 'Itapetininga',
    '0281': 'Itapira', '0009': 'Vila Prudente'
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
      <nav style={{ background: 'linear-gradient(135deg, #1e40af 0%, #7c3aed 100%)', color: 'white', padding: '20px 24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>⚖️ Judicial Aggregator</h1>
        <p style={{ margin: '8px 0 0', opacity: 0.9, fontSize: '14px' }}>Processos de Inventário e Divórcio com potencial imobiliário</p>
      </nav>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
        {/* Abas principais */}
        <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
          <button onClick={() => setAba('imoveis')} style={{
            padding: '16px 32px', borderRadius: '12px', border: 'none', fontWeight: '700', fontSize: '16px', cursor: 'pointer',
            backgroundColor: aba === 'imoveis' ? '#10b981' : '#e5e7eb',
            color: aba === 'imoveis' ? 'white' : '#374151',
            boxShadow: aba === 'imoveis' ? '0 4px 12px rgba(16,185,129,0.4)' : 'none'
          }}>
            🏠 COM IMÓVEL ({processosImoveis.length})
          </button>
          <button onClick={() => { setAba('datajud'); if (processosDatajud.length === 0) buscarDatajud(); }} style={{
            padding: '16px 32px', borderRadius: '12px', border: 'none', fontWeight: '700', fontSize: '16px', cursor: 'pointer',
            backgroundColor: aba === 'datajud' ? '#3b82f6' : '#e5e7eb',
            color: aba === 'datajud' ? 'white' : '#374151',
            boxShadow: aba === 'datajud' ? '0 4px 12px rgba(59,130,246,0.4)' : 'none'
          }}>
            📊 DataJud (Todos)
          </button>
        </div>

        {/* Filtros */}
        <div style={{ backgroundColor: 'white', borderRadius: '12px', padding: '20px', marginBottom: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: '600' }}>Filtrar por tipo:</span>
            {['todos', 'inventário', 'divórcio'].map(t => (
              <button key={t} onClick={() => setFiltroTipo(t)} style={{
                padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                backgroundColor: filtroTipo === t ? '#4f46e5' : '#f3f4f6',
                color: filtroTipo === t ? 'white' : '#374151',
                fontWeight: '600', textTransform: 'capitalize'
              }}>{t}</button>
            ))}
            
            {aba === 'datajud' && (
              <button onClick={buscarDatajud} disabled={loading} style={{
                marginLeft: 'auto', padding: '10px 20px', borderRadius: '8px', border: 'none',
                backgroundColor: '#3b82f6', color: 'white', fontWeight: '600', cursor: loading ? 'not-allowed' : 'pointer'
              }}>
                {loading ? '⏳ Buscando...' : '🔄 Atualizar'}
              </button>
            )}
          </div>
        </div>

        {/* Info box para aba de imóveis */}
        {aba === 'imoveis' && (
          <div style={{ backgroundColor: '#dcfce7', borderRadius: '12px', padding: '16px 20px', marginBottom: '24px', border: '1px solid #86efac' }}>
            <p style={{ margin: 0, color: '#166534', fontWeight: '600' }}>
              🏠 Estes {processosImoveis.length} processos foram identificados nos PDFs do Diário da Justiça com menções a imóveis (matrícula, escritura, ITCMD, etc.)
            </p>
          </div>
        )}

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
          <div style={{ backgroundColor: '#dcfce7', padding: '20px', borderRadius: '12px', textAlign: 'center' }}>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#166534', margin: 0 }}>{processosFiltrados.length}</p>
            <p style={{ fontSize: '14px', color: '#166534', margin: '4px 0 0' }}>Processos</p>
          </div>
          <div style={{ backgroundColor: '#dbeafe', padding: '20px', borderRadius: '12px', textAlign: 'center' }}>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#1e40af', margin: 0 }}>
              {processosFiltrados.filter(p => p.tipo.includes('Inventário')).length}
            </p>
            <p style={{ fontSize: '14px', color: '#1e40af', margin: '4px 0 0' }}>Inventários</p>
          </div>
          <div style={{ backgroundColor: '#fef3c7', padding: '20px', borderRadius: '12px', textAlign: 'center' }}>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#92400e', margin: 0 }}>
              {processosFiltrados.filter(p => p.tipo.includes('Divórcio')).length}
            </p>
            <p style={{ fontSize: '14px', color: '#92400e', margin: '4px 0 0' }}>Divórcios</p>
          </div>
        </div>

        {/* Grid de processos */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '16px' }}>
          {processosFiltrados.map(p => (
            <div key={p.numero} style={{
              backgroundColor: 'white', padding: '20px', borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)', border: '1px solid #e5e7eb'
            }}>
              {p.tem_imovel && (
                <div style={{ backgroundColor: '#10b981', color: 'white', padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: 'bold', marginBottom: '12px', display: 'inline-block' }}>
                  🏠 IMÓVEL CONFIRMADO
                </div>
              )}
              
              <a href={p.url_tjsp} target="_blank" rel="noopener noreferrer" style={{
                display: 'block', color: '#2563eb', fontFamily: 'monospace', fontSize: '13px', fontWeight: '600',
                padding: '10px 12px', backgroundColor: '#eff6ff', borderRadius: '8px', marginBottom: '12px',
                textDecoration: 'none', border: '1px solid #bfdbfe'
              }}>
                🔗 {p.numero}
              </a>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                <div>
                  <p style={{ fontSize: '11px', color: '#6b7280', margin: '0 0 2px' }}>Tipo</p>
                  <p style={{ fontWeight: '600', margin: 0, color: p.tipo.includes('Inventário') ? '#1e40af' : '#7c3aed' }}>{p.tipo}</p>
                </div>
                <div>
                  <p style={{ fontSize: '11px', color: '#6b7280', margin: '0 0 2px' }}>Comarca</p>
                  <p style={{ fontWeight: '600', margin: 0 }}>{p.comarca || COMARCAS[p.codigo_comarca || ''] || p.codigo_comarca}</p>
                </div>
              </div>

              <a href={p.url_tjsp} target="_blank" rel="noopener noreferrer" style={{
                display: 'block', width: '100%', backgroundColor: '#3b82f6', color: 'white',
                padding: '12px', borderRadius: '8px', textAlign: 'center', textDecoration: 'none',
                fontWeight: '600', fontSize: '14px'
              }}>
                🔍 Abrir no TJSP
              </a>
            </div>
          ))}
        </div>

        {processosFiltrados.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px', color: '#6b7280' }}>
            <p style={{ fontSize: '18px' }}>Nenhum processo encontrado</p>
          </div>
        )}
      </div>
    </div>
  );
}
