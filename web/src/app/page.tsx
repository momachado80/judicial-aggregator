'use client';
import { useState, useEffect } from 'react';

interface BuscarBody {
  tribunais: string[];
  tipos_processo: string[];
  quantidade: number;
  usar_cache: boolean;
  comarcas?: string[];
  incluir_extintos?: boolean;
}

interface Processo {
  numero: string;
  tribunal: string;
  tipo: string;
  comarca: string;
  data_ajuizamento: string;
  valor_causa: number | null;
  ultimo_movimento: string;
  data_ultimo_movimento: string;
  ativo: boolean;
  url_tjsp: string;
}

const STORAGE_KEY_EXCLUIDOS = 'judicial_processos_excluidos';
const STORAGE_KEY_INTERESSE = 'judicial_processos_interesse';

export default function Home() {
  const [tiposSelecionados, setTiposSelecionados] = useState(['Inventário', 'Divórcio Litigioso', 'Divórcio Consensual']);
  const [quantidade, setQuantidade] = useState(100);
  const [processos, setProcessos] = useState<Processo[]>([]);
  const [loading, setLoading] = useState(false);
  const [interesseIds, setInteresseIds] = useState<Set<string>>(new Set());
  const [excluidos, setExcluidos] = useState<Set<string>>(new Set());
  const [abaAtiva, setAbaAtiva] = useState('busca');
  const [paginaAtual, setPaginaAtual] = useState(1);
  const [totalBuscado, setTotalBuscado] = useState(0);
  const [ordenacao, setOrdenacao] = useState('data_desc');
  
  const [comarcaFiltro, setComarcaFiltro] = useState('');
  const [comarcasSelecionadas, setComarcasSelecionadas] = useState<string[]>([]);
  const [comarcasDisponiveis, setComarcasDisponiveis] = useState<string[]>([]);
  const [valorMinimo, setValorMinimo] = useState<number>(0);

  useEffect(() => {
    const savedExcluidos = localStorage.getItem(STORAGE_KEY_EXCLUIDOS);
    const savedInteresse = localStorage.getItem(STORAGE_KEY_INTERESSE);
    if (savedExcluidos) {
      setExcluidos(new Set(JSON.parse(savedExcluidos)));
    }
    if (savedInteresse) {
      setInteresseIds(new Set(JSON.parse(savedInteresse)));
    }
  }, []);

  useEffect(() => {
    if (excluidos.size > 0) {
      localStorage.setItem(STORAGE_KEY_EXCLUIDOS, JSON.stringify(Array.from(excluidos)));
    }
  }, [excluidos]);

  useEffect(() => {
    if (interesseIds.size > 0) {
      localStorage.setItem(STORAGE_KEY_INTERESSE, JSON.stringify(Array.from(interesseIds)));
    }
  }, [interesseIds]);

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

  const buscarProcessos = async (pagina: number = 1) => {
    setLoading(true);
    setPaginaAtual(pagina);
    try {
      const body: BuscarBody = {
        tribunais: ['TJSP'],
        tipos_processo: tiposSelecionados,
        quantidade: 1000,
        usar_cache: false,
        incluir_extintos: false
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
        const processosFiltrados = data.filter((p: Processo) => !excluidos.has(p.numero));
        setProcessos(processosFiltrados);
        setTotalBuscado(data.length);
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
    const exc = new Set(excluidos);
    exc.delete(numero);
    setExcluidos(exc);
  };

  const marcarExcluido = (numero: string) => {
    const novos = new Set(excluidos);
    novos.add(numero);
    setExcluidos(novos);
    const inter = new Set(interesseIds);
    inter.delete(numero);
    setInteresseIds(inter);
    setProcessos(processos.filter(p => p.numero !== numero));
  };

  const limparExcluidos = () => {
    if (confirm('Limpar ' + excluidos.size + ' processos excluidos? Eles voltarao nas buscas.')) {
      setExcluidos(new Set());
      localStorage.removeItem(STORAGE_KEY_EXCLUIDOS);
    }
  };

  const limparInteresse = () => {
    if (confirm('Limpar ' + interesseIds.size + ' processos de interesse?')) {
      setInteresseIds(new Set());
      localStorage.removeItem(STORAGE_KEY_INTERESSE);
    }
  };

  const exportarExcel = (lista: Processo[], nomeArquivo: string) => {
    const headers = ['Numero', 'Tipo', 'Comarca', 'Data Ajuizamento', 'Valor Causa', 'Ultimo Movimento', 'Data Movimento', 'Link TJSP'];
    const rows = lista.map(p => [
      formatarNumero(p.numero),
      p.tipo,
      p.comarca,
      formatarData(p.data_ajuizamento),
      p.valor_causa ? p.valor_causa.toString() : '',
      p.ultimo_movimento,
      p.data_ultimo_movimento,
      p.url_tjsp
    ]);
    
    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => '"' + (cell || '').replace(/"/g, '""') + '"').join(','))
      .join('\n');
    
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = nomeArquivo + '.csv';
    link.click();
  };

  const ordenarProcessos = (lista: Processo[]) => {
    const sorted = [...lista];
    switch (ordenacao) {
      case 'data_desc':
        return sorted.sort((a, b) => (b.data_ajuizamento || '').localeCompare(a.data_ajuizamento || ''));
      case 'data_asc':
        return sorted.sort((a, b) => (a.data_ajuizamento || '').localeCompare(b.data_ajuizamento || ''));
      case 'valor_desc':
        return sorted.sort((a, b) => (b.valor_causa || 0) - (a.valor_causa || 0));
      case 'valor_asc':
        return sorted.sort((a, b) => (a.valor_causa || 0) - (b.valor_causa || 0));
      case 'comarca':
        return sorted.sort((a, b) => (a.comarca || '').localeCompare(b.comarca || ''));
      case 'tipo':
        return sorted.sort((a, b) => (a.tipo || '').localeCompare(b.tipo || ''));
      default:
        return sorted;
    }
  };

  // Filtrar por valor - mantem processos sem valor informado separados
  const processosBase = processos.filter(p => !interesseIds.has(p.numero) && !excluidos.has(p.numero));
  const processosComValor = processosBase.filter(p => p.valor_causa && p.valor_causa > 0);
  const processosSemValor = processosBase.filter(p => !p.valor_causa || p.valor_causa === 0);
  
  // Aplicar filtro de valor minimo apenas nos que tem valor
  const processosComValorFiltrados = valorMinimo > 0 
    ? processosComValor.filter(p => p.valor_causa && p.valor_causa >= valorMinimo)
    : processosComValor;

  const processosBusca = ordenarProcessos([...processosComValorFiltrados, ...processosSemValor]);
  const processosInteresse = ordenarProcessos(processos.filter(p => interesseIds.has(p.numero)));

  const itensPorPagina = quantidade;
  const inicio = (paginaAtual - 1) * itensPorPagina;
  const fim = inicio + itensPorPagina;
  const processosPaginados = processosBusca.slice(inicio, fim);
  const totalPaginas = Math.ceil(processosBusca.length / itensPorPagina);

  const formatarData = (data: string) => {
    if (!data) return '-';
    return data.slice(6,8) + '/' + data.slice(4,6) + '/' + data.slice(0,4);
  };

  const formatarNumero = (n: string) => {
    if (n?.length === 20) {
      return n.slice(0,7) + '-' + n.slice(7,9) + '.' + n.slice(9,13) + '.' + n.slice(13,14) + '.' + n.slice(14,16) + '.' + n.slice(16,20);
    }
    return n;
  };

  const formatarValor = (valor: number | null) => {
    if (!valor) return null;
    return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  };

  const ProcessoCard = ({ processo }: { processo: Processo }) => {
    const temValor = processo.valor_causa && processo.valor_causa > 0;
    const temValorAlto = processo.valor_causa && processo.valor_causa >= 100000;
    
    return (
      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', border: temValorAlto ? '2px solid #10b981' : '1px solid #e5e7eb' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
          {temValorAlto && (
            <div style={{ backgroundColor: '#10b981', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>ALTO VALOR</div>
          )}
          {temValor ? (
            <div style={{ backgroundColor: '#3b82f6', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>VALOR INFORMADO</div>
          ) : (
            <div style={{ backgroundColor: '#f59e0b', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>VALOR NAO INFORMADO</div>
          )}
        </div>
        <div style={{ marginBottom: '12px' }}>
          <p style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>Numero:</p>
          <a href={processo.url_tjsp} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', fontFamily: 'monospace', fontSize: '12px', fontWeight: '600', textDecoration: 'none', display: 'block', padding: '8px 12px', backgroundColor: '#eff6ff', borderRadius: '6px', border: '1px solid #bfdbfe' }}>
            {formatarNumero(processo.numero)}
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
        <div style={{ marginBottom: '12px' }}>
          <p style={{ fontSize: '11px', color: '#6b7280' }}>Comarca:</p>
          <p style={{ fontWeight: '600', color: '#7c3aed', fontSize: '14px', margin: 0 }}>{processo.comarca}</p>
        </div>
        <div style={{ marginBottom: '12px', padding: '10px', backgroundColor: temValor ? (temValorAlto ? '#dcfce7' : '#eff6ff') : '#fef3c7', borderRadius: '8px' }}>
          <p style={{ fontSize: '11px', color: '#6b7280' }}>Valor da Causa:</p>
          {temValor ? (
            <p style={{ fontWeight: 'bold', fontSize: '16px', margin: 0, color: temValorAlto ? '#166534' : '#1e40af' }}>{formatarValor(processo.valor_causa)}</p>
          ) : (
            <p style={{ fontWeight: 'bold', fontSize: '14px', margin: 0, color: '#92400e' }}>Verificar no TJSP</p>
          )}
        </div>
        <div style={{ marginBottom: '16px' }}>
          <p style={{ fontSize: '11px', color: '#6b7280' }}>Ultimo Movimento ({processo.data_ultimo_movimento}):</p>
          <p style={{ fontSize: '13px', margin: 0, color: '#374151' }}>{processo.ultimo_movimento || '-'}</p>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
          <button onClick={() => marcarInteresse(processo.numero)} style={{ backgroundColor: '#10b981', color: 'white', padding: '10px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '12px' }}>Interesse</button>
          <a href={processo.url_tjsp} target="_blank" rel="noopener noreferrer" style={{ backgroundColor: '#3b82f6', color: 'white', padding: '10px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '12px', textAlign: 'center', textDecoration: 'none' }}>Ver TJSP</a>
          <button onClick={() => marcarExcluido(processo.numero)} style={{ backgroundColor: '#ef4444', color: 'white', padding: '10px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '12px' }}>Excluir</button>
        </div>
      </div>
    );
  };

  const processosAltoValor = processos.filter(p => p.valor_causa && p.valor_causa >= 100000).length;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
      <nav style={{ background: 'linear-gradient(to right, #4f46e5, #7c3aed)', color: 'white', padding: '20px 24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>Judicial Aggregator - TJSP</h1>
        <p style={{ fontSize: '13px', margin: '8px 0 0 0', opacity: 0.9 }}>Busque processos de Inventario e Divorcio - Verifique no TJSP se ha imoveis</p>
      </nav>
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
        <div style={{ backgroundColor: '#fef3c7', borderRadius: '12px', padding: '16px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '14px', color: '#92400e' }}><strong>{interesseIds.size}</strong> processos de interesse</span>
            <span style={{ fontSize: '14px', color: '#92400e' }}><strong>{excluidos.size}</strong> processos excluidos (nao aparecem nas buscas)</span>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {interesseIds.size > 0 && (
              <button onClick={() => exportarExcel(processosInteresse, 'processos_interesse')} style={{ backgroundColor: '#059669', color: 'white', padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '12px' }}>Exportar Excel</button>
            )}
            {interesseIds.size > 0 && (
              <button onClick={limparInteresse} style={{ backgroundColor: '#f59e0b', color: 'white', padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '12px' }}>Limpar Interesse</button>
            )}
            {excluidos.size > 0 && (
              <button onClick={limparExcluidos} style={{ backgroundColor: '#dc2626', color: 'white', padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '12px' }}>Limpar Excluidos</button>
            )}
          </div>
        </div>
        <div style={{ backgroundColor: 'white', borderRadius: '12px', padding: '24px', marginBottom: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '20px' }}>Buscar Processos</h2>
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
              <input type="text" value={comarcaFiltro} onChange={(e) => setComarcaFiltro(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && adicionarComarca(comarcaFiltro)} placeholder="Sao Paulo, Campinas..." list="comarcas-list" style={{ flex: 1, padding: '10px 14px', borderRadius: '8px', border: '1px solid #d1d5db' }} />
              <button onClick={() => adicionarComarca(comarcaFiltro)} style={{ backgroundColor: '#3b82f6', color: 'white', padding: '10px 20px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600' }}>+ Adicionar</button>
            </div>
            <datalist id="comarcas-list">{comarcasDisponiveis.map(c => <option key={c} value={c} />)}</datalist>
            {comarcasSelecionadas.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {comarcasSelecionadas.map(c => (
                  <span key={c} style={{ backgroundColor: '#dbeafe', color: '#1e40af', padding: '6px 12px', borderRadius: '20px', fontSize: '13px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {c}<button onClick={() => removerComarca(c)} style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontWeight: 'bold', fontSize: '16px', padding: 0 }}>x</button>
                  </span>
                ))}
              </div>
            )}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Quantidade por pagina:</label>
              <select value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))} style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
                <option value={500}>500</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Valor minimo da causa:</label>
              <select value={valorMinimo} onChange={(e) => setValorMinimo(Number(e.target.value))} style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
                <option value={0}>Todos os valores</option>
                <option value={50000}>Acima de R$ 50.000</option>
                <option value={100000}>Acima de R$ 100.000</option>
                <option value={200000}>Acima de R$ 200.000</option>
                <option value={500000}>Acima de R$ 500.000</option>
                <option value={1000000}>Acima de R$ 1.000.000</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Ordenar por:</label>
              <select value={ordenacao} onChange={(e) => setOrdenacao(e.target.value)} style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
                <option value="data_desc">Data (mais recentes)</option>
                <option value="data_asc">Data (mais antigos)</option>
                <option value="valor_desc">Valor (maior primeiro)</option>
                <option value="valor_asc">Valor (menor primeiro)</option>
                <option value="comarca">Comarca (A-Z)</option>
                <option value="tipo">Tipo (A-Z)</option>
              </select>
            </div>
          </div>
          <button onClick={() => buscarProcessos(1)} disabled={loading || tiposSelecionados.length === 0} style={{ width: '100%', background: loading ? '#9ca3af' : 'linear-gradient(to right, #4f46e5, #7c3aed)', color: 'white', padding: '16px', borderRadius: '8px', border: 'none', fontWeight: 'bold', fontSize: '16px', cursor: loading ? 'not-allowed' : 'pointer' }}>
            {loading ? 'Buscando...' : 'BUSCAR PROCESSOS'}
          </button>
        </div>
        {processos.length > 0 && (
          <div style={{ backgroundColor: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px', marginBottom: '20px' }}>
              <div style={{ backgroundColor: '#dcfce7', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
                <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#166534', margin: 0 }}>{processosBusca.length}</p>
                <p style={{ fontSize: '13px', color: '#166534', margin: 0 }}>Para Analisar</p>
              </div>
              <div style={{ backgroundColor: '#dbeafe', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
                <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#1e40af', margin: 0 }}>{processosComValorFiltrados.length}</p>
                <p style={{ fontSize: '13px', color: '#1e40af', margin: 0 }}>Com Valor Informado</p>
              </div>
              <div style={{ backgroundColor: '#fef3c7', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
                <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#92400e', margin: 0 }}>{processosSemValor.length}</p>
                <p style={{ fontSize: '13px', color: '#92400e', margin: 0 }}>Sem Valor Informado</p>
              </div>
              <div style={{ backgroundColor: '#d1fae5', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
                <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#065f46', margin: 0 }}>{processosAltoValor}</p>
                <p style={{ fontSize: '13px', color: '#065f46', margin: 0 }}>Alto Valor (100k+)</p>
              </div>
              <div style={{ backgroundColor: '#fce7f3', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
                <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#9d174d', margin: 0 }}>{processosInteresse.length}</p>
                <p style={{ fontSize: '13px', color: '#9d174d', margin: 0 }}>Com Interesse</p>
              </div>
            </div>
            
            {valorMinimo > 0 && (
              <div style={{ backgroundColor: '#eff6ff', padding: '12px', borderRadius: '8px', marginBottom: '20px', border: '1px solid #bfdbfe' }}>
                <p style={{ margin: 0, fontSize: '14px', color: '#1e40af' }}>
                  Filtro ativo: mostrando <strong>{processosComValorFiltrados.length}</strong> processos com valor acima de {formatarValor(valorMinimo)} + <strong>{processosSemValor.length}</strong> processos sem valor informado (precisam verificar no TJSP)
                </p>
              </div>
            )}

            <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button onClick={() => setAbaAtiva('busca')} style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer', backgroundColor: abaAtiva === 'busca' ? '#4f46e5' : '#e5e7eb', color: abaAtiva === 'busca' ? 'white' : '#374151' }}>
                  Para Analisar ({processosBusca.length})
                </button>
                <button onClick={() => setAbaAtiva('interesse')} style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer', backgroundColor: abaAtiva === 'interesse' ? '#10b981' : '#e5e7eb', color: abaAtiva === 'interesse' ? 'white' : '#374151' }}>
                  Com Interesse ({processosInteresse.length})
                </button>
              </div>
              {processosBusca.length > 0 && abaAtiva === 'busca' && (
                <button onClick={() => exportarExcel(processosBusca, 'processos_busca')} style={{ padding: '10px 16px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer', backgroundColor: '#059669', color: 'white', fontSize: '13px' }}>
                  Exportar Lista ({processosBusca.length})
                </button>
              )}
            </div>
            {abaAtiva === 'busca' && (
              <>
                {totalPaginas > 1 && (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginBottom: '20px', padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
                    <button onClick={() => setPaginaAtual(p => Math.max(1, p - 1))} disabled={paginaAtual === 1} style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: paginaAtual === 1 ? '#e5e7eb' : '#4f46e5', color: paginaAtual === 1 ? '#9ca3af' : 'white', cursor: paginaAtual === 1 ? 'not-allowed' : 'pointer', fontWeight: '600' }}>
                      Anterior
                    </button>
                    <span style={{ fontSize: '14px', fontWeight: '600' }}>Pagina {paginaAtual} de {totalPaginas} ({processosBusca.length} processos)</span>
                    <button onClick={() => setPaginaAtual(p => Math.min(totalPaginas, p + 1))} disabled={paginaAtual === totalPaginas} style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: paginaAtual === totalPaginas ? '#e5e7eb' : '#4f46e5', color: paginaAtual === totalPaginas ? '#9ca3af' : 'white', cursor: paginaAtual === totalPaginas ? 'not-allowed' : 'pointer', fontWeight: '600' }}>
                      Proxima
                    </button>
                  </div>
                )}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>
                  {processosPaginados.map(p => <ProcessoCard key={p.numero} processo={p} />)}
                </div>
                {totalPaginas > 1 && (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginTop: '20px', padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
                    <button onClick={() => setPaginaAtual(p => Math.max(1, p - 1))} disabled={paginaAtual === 1} style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: paginaAtual === 1 ? '#e5e7eb' : '#4f46e5', color: paginaAtual === 1 ? '#9ca3af' : 'white', cursor: paginaAtual === 1 ? 'not-allowed' : 'pointer', fontWeight: '600' }}>
                      Anterior
                    </button>
                    <span style={{ fontSize: '14px', fontWeight: '600' }}>Pagina {paginaAtual} de {totalPaginas}</span>
                    <button onClick={() => setPaginaAtual(p => Math.min(totalPaginas, p + 1))} disabled={paginaAtual === totalPaginas} style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: paginaAtual === totalPaginas ? '#e5e7eb' : '#4f46e5', color: paginaAtual === totalPaginas ? '#9ca3af' : 'white', cursor: paginaAtual === totalPaginas ? 'not-allowed' : 'pointer', fontWeight: '600' }}>
                      Proxima
                    </button>
                  </div>
                )}
              </>
            )}
            {abaAtiva === 'interesse' && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>
                {processosInteresse.map(p => <ProcessoCard key={p.numero} processo={p} />)}
              </div>
            )}
            {((abaAtiva === 'busca' && processosPaginados.length === 0) || (abaAtiva === 'interesse' && processosInteresse.length === 0)) && (
              <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}><p>Nenhum processo nesta aba</p></div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
