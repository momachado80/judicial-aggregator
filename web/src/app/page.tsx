'use client';
import { useState, useEffect } from 'react';

interface BuscarBody {
  tribunais: string[];
  tipos_processo: string[];
  quantidade: number;
  usar_cache: boolean;
  comarcas?: string[];
}

export default function Home() {
  const [tiposSelecionados, setTiposSelecionados] = useState(['Inventário', 'Divórcio Litigioso', 'Divórcio Consensual']);
  const [quantidade, setQuantidade] = useState(100);
  const [processos, setProcessos] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [interesseIds, setInteresseIds] = useState(new Set<string>());
  const [descartadosIds, setDescartadosIds] = useState(new Set<string>());
  const [abaAtiva, setAbaAtiva] = useState('busca');
  
  const [comarcaFiltro, setComarcaFiltro] = useState('');
  const [comarcasSelecionadas, setComarcasSelecionadas] = useState<string[]>([]);
  const [comarcasDisponiveis, setComarcasDisponiveis] = useState<string[]>([]);

  useEffect(() => {
    fetch('https://judicial-aggregator-production.up.railway.app/api/comarcas')
      .then(res => res.json())
      .then(data => {
        if (data.TJSP) setComarcasDisponiveis(data.TJSP);
      })
      .catch(err => console.error('Erro:', err));
  }, []);

  const adicionarComarca = (comarca: string) => {
    if (comarca && !comarcasSelecionadas.includes(comarca)) {
      setComarcasSelecionadas([...comarcasSelecionadas, comarca]);
      setComarcaFiltro('');
    }
  };

  const removerComarca = (comarca: string) => {
    setComarcasSelecionadas(comarcasSelecionadas.filter(c => c !== comarca));
  };

  const buscarProcessos = async () => {
    setLoading(true);
    try {
      const body: BuscarBody = {
        tribunais: ['TJSP'],
        tipos_processo: tiposSelecionados,
        quantidade: quantidade,
        usar_cache: false
      };
      
      if (comarcasSelecionadas.length > 0) {
        body.comarcas = comarcasSelecionadas;
      }

      const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await response.json();
      
      if (Array.isArray(data)) {
        setProcessos(data);
      } else {
        alert('Erro: ' + JSON.stringify(data));
      }
    } catch (error) {
      console.error('Erro:', error);
      alert('Erro ao buscar');
    }
    setLoading(false);
  };

  const marcarInteresse = (numero: string) => {
    const novos = new Set(interesseIds);
    novos.add(numero);
    setInteresseIds(novos);
    const desc = new Set(descartadosIds);
    desc.delete(numero);
    setDescartadosIds(desc);
  };

  const marcarDescartado = (numero: string) => {
    const novos = new Set(descartadosIds);
    novos.add(numero);
    setDescartadosIds(novos);
    const inter = new Set(interesseIds);
    inter.delete(numero);
    setInteresseIds(inter);
  };

  const processosBusca = processos.filter(p => !interesseIds.has(p.numero) && !descartadosIds.has(p.numero));
  const processosInteresse = processos.filter(p => interesseIds.has(p.numero));
  const processosDescartados = processos.filter(p => descartadosIds.has(p.numero));

  const formatarData = (data: string) => {
    if (!data) return '-';
    return `${data.slice(6,8)}/${data.slice(4,6)}/${data.slice(0,4)}`;
  };

  const formatarNumero = (n: string) => {
    if (n?.length === 20) {
      return `${n.slice(0,7)}-${n.slice(7,9)}.${n.slice(9,13)}.${n.slice(13,14)}.${n.slice(14,16)}.${n.slice(16,20)}`;
    }
    return n;
  };

  const linkTJSP = (numero: string) => {
    const f = formatarNumero(numero);
    return `https://esaj.tjsp.jus.br/cpopg/search.do?conversationId=&dadosConsulta.localPesquisa.cdLocal=-1&cbPesquisa=NUMPROC&dadosConsulta.tipoNuProcesso=UNIFICADO&numeroDigitoAnoUnificado=${f.slice(0,15)}&foroNumeroUnificado=${f.slice(21,25)}&dadosConsulta.valorConsultaNuUnificado=${f}`;
  };

  const ProcessoCard = ({ processo }: { processo: any }) => (
    <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', border: '1px solid #e5e7eb' }}>
      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>Número:</p>
        <a href={linkTJSP(processo.numero)} target="_blank" rel="noopener noreferrer"
          style={{ color: '#2563eb', fontFamily: 'monospace', fontSize: '12px', fontWeight: '600', textDecoration: 'none', display: 'block', padding: '8px 12px', backgroundColor: '#eff6ff', borderRadius: '6px', border: '1px solid #bfdbfe' }}>
          🔗 {formatarNumero(processo.numero)}
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
        <button onClick={() => marcarInteresse(processo.numero)} style={{ backgroundColor: '#10b981', color: 'white', padding: '10px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '13px' }}>⭐ Interesse</button>
        <button onClick={() => marcarDescartado(processo.numero)} style={{ backgroundColor: '#ef4444', color: 'white', padding: '10px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '13px' }}>🗑️ Descartar</button>
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
      <nav style={{ background: 'linear-gradient(to right, #4f46e5, #7c3aed)', color: 'white', padding: '20px 24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>⚖️ Judicial Aggregator - TJSP</h1>
      </nav>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
        <div style={{ backgroundColor: 'white', borderRadius: '12px', padding: '24px', marginBottom: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '20px' }}>🔍 Buscar Processos</h2>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Tipos:</label>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              {['Inventário', 'Divórcio Litigioso', 'Divórcio Consensual'].map(t => (
                <label key={t} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={tiposSelecionados.includes(t)} onChange={(e) => {
                    if (e.target.checked) setTiposSelecionados([...tiposSelecionados, t]);
                    else setTiposSelecionados(tiposSelecionados.filter(x => x !== t));
                  }} style={{ width: '18px', height: '18px' }} />
                  <span>{t}</span>
                </label>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Comarcas (opcional):</label>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
              <input type="text" value={comarcaFiltro} onChange={(e) => setComarcaFiltro(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && adicionarComarca(comarcaFiltro)} placeholder="São Paulo, Campinas..." list="comarcas-list" style={{ flex: 1, padding: '10px 14px', borderRadius: '8px', border: '1px solid #d1d5db' }} />
              <button onClick={() => adicionarComarca(comarcaFiltro)} style={{ backgroundColor: '#3b82f6', color: 'white', padding: '10px 20px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600' }}>+ Adicionar</button>
            </div>
            <datalist id="comarcas-list">{comarcasDisponiveis.map(c => <option key={c} value={c} />)}</datalist>
            {comarcasSelecionadas.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {comarcasSelecionadas.map(c => (
                  <span key={c} style={{ backgroundColor: '#dbeafe', color: '#1e40af', padding: '6px 12px', borderRadius: '20px', fontSize: '13px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {c}<button onClick={() => removerComarca(c)} style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px', padding: 0 }}>×</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Quantidade:</label>
            <select value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))} style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
              <option value={50}>50</option><option value={100}>100</option><option value={200}>200</option><option value={500}>500</option><option value={1000}>1000</option>
            </select>
          </div>

          <button onClick={buscarProcessos} disabled={loading || tiposSelecionados.length === 0} style={{ width: '100%', background: loading ? '#9ca3af' : 'linear-gradient(to right, #4f46e5, #7c3aed)', color: 'white', padding: '16px', borderRadius: '8px', border: 'none', fontWeight: 'bold', fontSize: '16px', cursor: loading ? 'not-allowed' : 'pointer' }}>
            {loading ? '⏳ Buscando...' : '🔍 BUSCAR PROCESSOS'}
          </button>
        </div>

        {processos.length > 0 && (
          <div style={{ backgroundColor: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' }}>
              <div style={{ backgroundColor: '#dcfce7', padding: '16px', borderRadius: '8px', textAlign: 'center' }}><p style={{ fontSize: '28px', fontWeight: 'bold', color: '#166534', margin: 0 }}>{processos.length}</p><p style={{ fontSize: '13px', color: '#166534', margin: 0 }}>Total</p></div>
              <div style={{ backgroundColor: '#fef3c7', padding: '16px', borderRadius: '8px', textAlign: 'center' }}><p style={{ fontSize: '28px', fontWeight: 'bold', color: '#92400e', margin: 0 }}>{processosInteresse.length}</p><p style={{ fontSize: '13px', color: '#92400e', margin: 0 }}>Interesse</p></div>
              <div style={{ backgroundColor: '#fee2e2', padding: '16px', borderRadius: '8px', textAlign: 'center' }}><p style={{ fontSize: '28px', fontWeight: 'bold', color: '#991b1b', margin: 0 }}>{processosDescartados.length}</p><p style={{ fontSize: '13px', color: '#991b1b', margin: 0 }}>Descartados</p></div>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
              <button onClick={() => setAbaAtiva('busca')} style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer', backgroundColor: abaAtiva === 'busca' ? '#4f46e5' : '#e5e7eb', color: abaAtiva === 'busca' ? 'white' : '#374151' }}>📋 Busca ({processosBusca.length})</button>
              <button onClick={() => setAbaAtiva('interesse')} style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer', backgroundColor: abaAtiva === 'interesse' ? '#eab308' : '#e5e7eb', color: abaAtiva === 'interesse' ? 'white' : '#374151' }}>⭐ Interesse ({processosInteresse.length})</button>
              <button onClick={() => setAbaAtiva('descartados')} style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer', backgroundColor: abaAtiva === 'descartados' ? '#6b7280' : '#e5e7eb', color: abaAtiva === 'descartados' ? 'white' : '#374151' }}>🗑️ Descartados ({processosDescartados.length})</button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
              {getProcessosAba().map(p => <ProcessoCard key={p.numero} processo={p} />)}
            </div>

            {getProcessosAba().length === 0 && <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}><p>Nenhum processo nesta aba</p></div>}
          </div>
        )}
      </div>
    </div>
  );
}
