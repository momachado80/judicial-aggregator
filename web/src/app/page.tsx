'use client';
import { useState, useEffect } from 'react';

const Tooltip = ({ texto, children }: { texto: string; children: React.ReactNode }) => {
  const [mostrar, setMostrar] = useState(false);
  return (
    <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
      {children}
      <span
        onMouseEnter={() => setMostrar(true)}
        onMouseLeave={() => setMostrar(false)}
        style={{ cursor: 'help', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '16px', height: '16px', borderRadius: '50%', backgroundColor: '#6b7280', color: 'white', fontSize: '11px', fontWeight: 'bold' }}
      >
        ?
      </span>
      {mostrar && (
        <span style={{ position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '8px', padding: '8px 12px', backgroundColor: '#1f2937', color: 'white', fontSize: '12px', borderRadius: '6px', whiteSpace: 'normal', width: '250px', zIndex: 1000, boxShadow: '0 4px 12px rgba(0,0,0,0.3)', lineHeight: '1.4' }}>
          {texto}
          <span style={{ position: 'absolute', top: '100%', left: '50%', transform: 'translateX(-50%)', borderWidth: '6px', borderStyle: 'solid', borderColor: '#1f2937 transparent transparent transparent' }}></span>
        </span>
      )}
    </span>
  );
};

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

interface VerificacaoImovel {
  tem_imovel: boolean;
  confianca: 'alta' | 'media' | 'baixa';
  termos_encontrados: { termo: string; ocorrencias: number }[];
  total_ocorrencias: number;
  erro?: string;
}

const STORAGE_KEY_EXCLUIDOS = 'judicial_processos_excluidos';
const STORAGE_KEY_INTERESSE = 'judicial_processos_interesse';
const STORAGE_KEY_NOTAS = 'judicial_processos_notas';
const STORAGE_KEY_VERIFICACOES = 'judicial_verificacoes_imoveis';

export default function Home() {
  const [tiposSelecionados, setTiposSelecionados] = useState(['Inventário', 'Divórcio Litigioso', 'Divórcio Consensual']);
  const [quantidade, setQuantidade] = useState(100);
  const [processos, setProcessos] = useState<Processo[]>([]);
  const [loading, setLoading] = useState(false);
  const [interesseIds, setInteresseIds] = useState<Set<string>>(new Set());
  const [excluidos, setExcluidos] = useState<Set<string>>(new Set());
  const [notas, setNotas] = useState<Record<string, string>>({});
  const [abaAtiva, setAbaAtiva] = useState('busca');
  const [paginaAtual, setPaginaAtual] = useState(1);
  const [totalBuscado, setTotalBuscado] = useState(0);
  const [ordenacao, setOrdenacao] = useState('data_desc');
  const [tempoBusca, setTempoBusca] = useState<number | null>(null);
  
  const [comarcaFiltro, setComarcaFiltro] = useState('');
  const [comarcasSelecionadas, setComarcasSelecionadas] = useState<string[]>([]);
  const [comarcasDisponiveis, setComarcasDisponiveis] = useState<string[]>([]);
  const [valorMinimo, setValorMinimo] = useState<number>(0);
  const [periodoFiltro, setPeriodoFiltro] = useState<number>(0);

  const [verificacoes, setVerificacoes] = useState<Record<string, VerificacaoImovel>>({});
  const [verificandoLote, setVerificandoLote] = useState(false);
  const [progressoVerificacao, setProgressoVerificacao] = useState({ atual: 0, total: 0 });
  const [filtroImovel, setFiltroImovel] = useState<'todos' | 'com_imovel' | 'sem_imovel' | 'nao_verificado'>('todos');

  useEffect(() => {
    const savedExcluidos = localStorage.getItem(STORAGE_KEY_EXCLUIDOS);
    const savedInteresse = localStorage.getItem(STORAGE_KEY_INTERESSE);
    const savedNotas = localStorage.getItem(STORAGE_KEY_NOTAS);
    const savedVerificacoes = localStorage.getItem(STORAGE_KEY_VERIFICACOES);
    if (savedExcluidos) setExcluidos(new Set(JSON.parse(savedExcluidos)));
    if (savedInteresse) setInteresseIds(new Set(JSON.parse(savedInteresse)));
    if (savedNotas) setNotas(JSON.parse(savedNotas));
    if (savedVerificacoes) setVerificacoes(JSON.parse(savedVerificacoes));
  }, []);

  useEffect(() => { if (excluidos.size > 0) localStorage.setItem(STORAGE_KEY_EXCLUIDOS, JSON.stringify(Array.from(excluidos))); }, [excluidos]);
  useEffect(() => { if (interesseIds.size > 0) localStorage.setItem(STORAGE_KEY_INTERESSE, JSON.stringify(Array.from(interesseIds))); }, [interesseIds]);
  useEffect(() => { if (Object.keys(notas).length > 0) localStorage.setItem(STORAGE_KEY_NOTAS, JSON.stringify(notas)); }, [notas]);
  useEffect(() => { if (Object.keys(verificacoes).length > 0) localStorage.setItem(STORAGE_KEY_VERIFICACOES, JSON.stringify(verificacoes)); }, [verificacoes]);

  useEffect(() => {
    fetch('https://judicial-aggregator-production.up.railway.app/api/comarcas')
      .then(res => res.json())
      .then(data => { if (data.TJSP) setComarcasDisponiveis(data.TJSP); })
      .catch(err => console.error('Erro:', err));
  }, []);

  const adicionarComarca = (comarca: string) => {
    if (comarca && !comarcasSelecionadas.includes(comarca)) {
      setComarcasSelecionadas([...comarcasSelecionadas, comarca]);
      setComarcaFiltro('');
    }
  };
  const removerComarca = (comarca: string) => setComarcasSelecionadas(comarcasSelecionadas.filter(c => c !== comarca));

  const buscarProcessos = async (pagina: number = 1) => {
    setLoading(true);
    setPaginaAtual(pagina);
    setTempoBusca(null);
    const inicio = Date.now();
    try {
      const body: BuscarBody = { tribunais: ['TJSP'], tipos_processo: tiposSelecionados, quantidade: quantidade, usar_cache: false, incluir_extintos: false };
      if (comarcasSelecionadas.length > 0) body.comarcas = comarcasSelecionadas;
      const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
      });
      const data = await response.json();
      if (Array.isArray(data)) {
        setProcessos(data.filter((p: Processo) => !excluidos.has(p.numero)));
        setTotalBuscado(data.length);
        setTempoBusca((Date.now() - inicio) / 1000);
      } else alert('Erro: ' + JSON.stringify(data));
    } catch (error) { console.error('Erro:', error); alert('Erro ao buscar'); }
    setLoading(false);
  };

  const verificarImovelUnico = async (numero: string): Promise<VerificacaoImovel | null> => {
    try {
      const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/verificar-imovel', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ numero })
      });
      return await response.json();
    } catch (error) { console.error('Erro ao verificar:', error); return null; }
  };

  const verificarLote = async () => {
    const processosParaVerificar = processosPaginados.filter(p => !verificacoes[p.numero]);
    if (processosParaVerificar.length === 0) { alert('Todos os processos desta página já foram verificados!'); return; }
    setVerificandoLote(true);
    setProgressoVerificacao({ atual: 0, total: processosParaVerificar.length });
    const novasVerificacoes = { ...verificacoes };
    for (let i = 0; i < processosParaVerificar.length; i++) {
      const processo = processosParaVerificar[i];
      setProgressoVerificacao({ atual: i + 1, total: processosParaVerificar.length });
      const resultado = await verificarImovelUnico(processo.numero);
      if (resultado) { novasVerificacoes[processo.numero] = resultado; setVerificacoes({ ...novasVerificacoes }); }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    setVerificandoLote(false);
    setProgressoVerificacao({ atual: 0, total: 0 });
  };

  const limparVerificacoes = () => { if (confirm('Limpar todas as verificações?')) { setVerificacoes({}); localStorage.removeItem(STORAGE_KEY_VERIFICACOES); } };
  const marcarInteresse = (numero: string) => { const novos = new Set(interesseIds); novos.add(numero); setInteresseIds(novos); const exc = new Set(excluidos); exc.delete(numero); setExcluidos(exc); };
  const marcarExcluido = (numero: string) => { const novos = new Set(excluidos); novos.add(numero); setExcluidos(novos); const inter = new Set(interesseIds); inter.delete(numero); setInteresseIds(inter); setProcessos(processos.filter(p => p.numero !== numero)); };
  const salvarNota = (numero: string, nota: string) => { const novasNotas = { ...notas }; if (nota.trim()) novasNotas[numero] = nota; else delete novasNotas[numero]; setNotas(novasNotas); };
  const limparExcluidos = () => { if (confirm('Limpar ' + excluidos.size + ' processos excluidos?')) { setExcluidos(new Set()); localStorage.removeItem(STORAGE_KEY_EXCLUIDOS); } };
  const limparInteresse = () => { if (confirm('Limpar ' + interesseIds.size + ' processos de interesse?')) { setInteresseIds(new Set()); localStorage.removeItem(STORAGE_KEY_INTERESSE); } };

  const exportarExcel = (lista: Processo[], nomeArquivo: string) => {
    const headers = ['Numero', 'Tipo', 'Comarca', 'Data Ajuizamento', 'Valor Causa', 'Tem Imovel', 'Confianca', 'Termos', 'Ultimo Movimento', 'Data Movimento', 'Notas', 'Link TJSP'];
    const rows = lista.map(p => {
      const verif = verificacoes[p.numero];
      return [formatarNumero(p.numero), p.tipo, p.comarca, formatarData(p.data_ajuizamento), p.valor_causa?.toString() || '', verif ? (verif.tem_imovel ? 'SIM' : 'NAO') : '', verif?.confianca || '', verif?.termos_encontrados?.map(t => t.termo).join(', ') || '', p.ultimo_movimento, p.data_ultimo_movimento, notas[p.numero] || '', p.url_tjsp];
    });
    const csvContent = [headers, ...rows].map(row => row.map(cell => '"' + (cell || '').replace(/"/g, '""') + '"').join(',')).join('\n');
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = nomeArquivo + '.csv'; link.click();
  };

  const ordenarProcessos = (lista: Processo[]) => {
    const sorted = [...lista];
    switch (ordenacao) {
      case 'data_desc': return sorted.sort((a, b) => (b.data_ajuizamento || '').localeCompare(a.data_ajuizamento || ''));
      case 'data_asc': return sorted.sort((a, b) => (a.data_ajuizamento || '').localeCompare(b.data_ajuizamento || ''));
      case 'valor_desc': return sorted.sort((a, b) => (b.valor_causa || 0) - (a.valor_causa || 0));
      case 'valor_asc': return sorted.sort((a, b) => (a.valor_causa || 0) - (b.valor_causa || 0));
      case 'comarca': return sorted.sort((a, b) => (a.comarca || '').localeCompare(b.comarca || ''));
      case 'tipo': return sorted.sort((a, b) => (a.tipo || '').localeCompare(b.tipo || ''));
      case 'imovel': return sorted.sort((a, b) => { const verifA = verificacoes[a.numero]; const verifB = verificacoes[b.numero]; if (verifA?.tem_imovel && !verifB?.tem_imovel) return -1; if (!verifA?.tem_imovel && verifB?.tem_imovel) return 1; return 0; });
      default: return sorted;
    }
  };

  const filtrarPorPeriodo = (lista: Processo[]) => {
    if (periodoFiltro === 0) return lista;
    const hoje = new Date(); const dataLimite = new Date(); dataLimite.setDate(hoje.getDate() - periodoFiltro);
    const limiteStr = dataLimite.toISOString().slice(0, 10).replace(/-/g, '');
    return lista.filter(p => p.data_ajuizamento && p.data_ajuizamento >= limiteStr);
  };

  const filtrarPorImovel = (lista: Processo[]) => {
    if (filtroImovel === 'todos') return lista;
    return lista.filter(p => {
      const verif = verificacoes[p.numero];
      switch (filtroImovel) {
        case 'com_imovel': return verif?.tem_imovel === true;
        case 'sem_imovel': return verif?.tem_imovel === false;
        case 'nao_verificado': return !verif;
        default: return true;
      }
    });
  };

  const processosBase = processos.filter(p => !interesseIds.has(p.numero) && !excluidos.has(p.numero));
  const processosComPeriodo = filtrarPorPeriodo(processosBase);
  const processosComValor = processosComPeriodo.filter(p => p.valor_causa && p.valor_causa > 0);
  const processosSemValor = processosComPeriodo.filter(p => !p.valor_causa || p.valor_causa === 0);
  const processosComValorFiltrados = valorMinimo > 0 ? processosComValor.filter(p => p.valor_causa && p.valor_causa >= valorMinimo) : processosComValor;
  const processosPreImovel = ordenarProcessos([...processosComValorFiltrados, ...processosSemValor]);
  const processosBusca = filtrarPorImovel(processosPreImovel);
  const processosInteresse = ordenarProcessos(processos.filter(p => interesseIds.has(p.numero)));

  const itensPorPagina = quantidade;
  const inicio = (paginaAtual - 1) * itensPorPagina;
  const processosPaginados = processosBusca.slice(inicio, inicio + itensPorPagina);
  const totalPaginas = Math.ceil(processosBusca.length / itensPorPagina);

  const formatarData = (data: string) => data ? data.slice(6,8) + '/' + data.slice(4,6) + '/' + data.slice(0,4) : '-';
  const formatarNumero = (n: string) => n?.length === 20 ? n.slice(0,7) + '-' + n.slice(7,9) + '.' + n.slice(9,13) + '.' + n.slice(13,14) + '.' + n.slice(14,16) + '.' + n.slice(16,20) : n;
  const formatarValor = (valor: number | null) => valor ? valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : null;

  const estatisticasVerificacao = {
    total: Object.keys(verificacoes).length,
    comImovel: Object.values(verificacoes).filter(v => v.tem_imovel).length,
    semImovel: Object.values(verificacoes).filter(v => !v.tem_imovel).length,
  };

  const processosNaoVerificadosPagina = processosPaginados.filter(p => !verificacoes[p.numero]).length;

  const ProcessoCard = ({ processo }: { processo: Processo }) => {
    const [notaLocal, setNotaLocal] = useState(notas[processo.numero] || '');
    const [editandoNota, setEditandoNota] = useState(false);
    const [verificandoIndividual, setVerificandoIndividual] = useState(false);
    const temValor = processo.valor_causa && processo.valor_causa > 0;
    const temValorAlto = processo.valor_causa && processo.valor_causa >= 100000;
    const temNota = notas[processo.numero]?.trim().length > 0;
    const verificacao = verificacoes[processo.numero];
    
    const handleSalvarNota = () => { salvarNota(processo.numero, notaLocal); setEditandoNota(false); };
    const handleVerificarIndividual = async () => {
      setVerificandoIndividual(true);
      const resultado = await verificarImovelUnico(processo.numero);
      if (resultado) setVerificacoes(prev => ({ ...prev, [processo.numero]: resultado }));
      setVerificandoIndividual(false);
    };

    const corBordaImovel = verificacao?.tem_imovel ? (verificacao.confianca === 'alta' ? '#22c55e' : '#84cc16') : verificacao?.tem_imovel === false ? '#ef4444' : undefined;

    return (
      <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', border: corBordaImovel ? `3px solid ${corBordaImovel}` : temValorAlto ? '2px solid #10b981' : temNota ? '2px solid #8b5cf6' : '1px solid #e5e7eb' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
          {verificacao && (verificacao.tem_imovel ? (
            <div style={{ backgroundColor: verificacao.confianca === 'alta' ? '#22c55e' : '#84cc16', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>🏠 TEM IMÓVEL ({verificacao.confianca.toUpperCase()})</div>
          ) : (
            <div style={{ backgroundColor: '#ef4444', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>❌ SEM IMÓVEL</div>
          ))}
          {temValorAlto && <div style={{ backgroundColor: '#10b981', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>ALTO VALOR</div>}
          {temValor ? <div style={{ backgroundColor: '#3b82f6', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>VALOR INFORMADO</div> : <div style={{ backgroundColor: '#f59e0b', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>VALOR NAO INFORMADO</div>}
          {temNota && <div style={{ backgroundColor: '#8b5cf6', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold' }}>TEM NOTA</div>}
        </div>
        {verificacao?.tem_imovel && verificacao.termos_encontrados.length > 0 && (
          <div style={{ backgroundColor: '#f0fdf4', padding: '8px 12px', borderRadius: '6px', marginBottom: '12px', border: '1px solid #bbf7d0' }}>
            <p style={{ fontSize: '11px', color: '#166534', margin: 0, fontWeight: '600' }}>Termos: {verificacao.termos_encontrados.map(t => `${t.termo} (${t.ocorrencias})`).join(', ')}</p>
          </div>
        )}
        <div style={{ marginBottom: '12px' }}>
          <p style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>Numero:</p>
          <a href={processo.url_tjsp} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', fontFamily: 'monospace', fontSize: '12px', fontWeight: '600', textDecoration: 'none', display: 'block', padding: '8px 12px', backgroundColor: '#eff6ff', borderRadius: '6px', border: '1px solid #bfdbfe' }}>{formatarNumero(processo.numero)}</a>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
          <div><p style={{ fontSize: '11px', color: '#6b7280' }}>Tipo:</p><p style={{ fontWeight: '600', fontSize: '14px', margin: 0 }}>{processo.tipo}</p></div>
          <div><p style={{ fontSize: '11px', color: '#6b7280' }}>Data:</p><p style={{ fontWeight: '600', fontSize: '14px', margin: 0 }}>{formatarData(processo.data_ajuizamento)}</p></div>
        </div>
        <div style={{ marginBottom: '12px' }}><p style={{ fontSize: '11px', color: '#6b7280' }}>Comarca:</p><p style={{ fontWeight: '600', color: '#7c3aed', fontSize: '14px', margin: 0 }}>{processo.comarca}</p></div>
        <div style={{ marginBottom: '12px', padding: '10px', backgroundColor: temValor ? (temValorAlto ? '#dcfce7' : '#eff6ff') : '#fef3c7', borderRadius: '8px' }}>
          <p style={{ fontSize: '11px', color: '#6b7280' }}>Valor da Causa:</p>
          {temValor ? <p style={{ fontWeight: 'bold', fontSize: '16px', margin: 0, color: temValorAlto ? '#166534' : '#1e40af' }}>{formatarValor(processo.valor_causa)}</p> : <p style={{ fontWeight: 'bold', fontSize: '14px', margin: 0, color: '#92400e' }}>Verificar no TJSP</p>}
        </div>
        <div style={{ marginBottom: '12px' }}><p style={{ fontSize: '11px', color: '#6b7280' }}>Ultimo Movimento ({processo.data_ultimo_movimento}):</p><p style={{ fontSize: '13px', margin: 0, color: '#374151' }}>{processo.ultimo_movimento || '-'}</p></div>
        <div style={{ marginBottom: '16px', padding: '10px', backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <p style={{ fontSize: '11px', color: '#6b7280', margin: 0 }}>Notas:</p>
            {!editandoNota && <button onClick={() => setEditandoNota(true)} style={{ fontSize: '11px', color: '#6366f1', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>{temNota ? 'Editar' : '+ Adicionar'}</button>}
          </div>
          {editandoNota ? (
            <div>
              <textarea value={notaLocal} onChange={(e) => setNotaLocal(e.target.value)} placeholder="Ex: Ligar segunda..." style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '13px', minHeight: '60px', resize: 'vertical', boxSizing: 'border-box' }} />
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button onClick={handleSalvarNota} style={{ flex: 1, backgroundColor: '#6366f1', color: 'white', padding: '6px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>Salvar</button>
                <button onClick={() => { setNotaLocal(notas[processo.numero] || ''); setEditandoNota(false); }} style={{ flex: 1, backgroundColor: '#e5e7eb', color: '#374151', padding: '6px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>Cancelar</button>
              </div>
            </div>
          ) : <p style={{ fontSize: '13px', margin: 0, color: temNota ? '#374151' : '#9ca3af', fontStyle: temNota ? 'normal' : 'italic' }}>{temNota ? notas[processo.numero] : 'Nenhuma nota'}</p>}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
          <button onClick={() => marcarInteresse(processo.numero)} style={{ backgroundColor: '#10b981', color: 'white', padding: '10px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '12px' }}>✓ Interesse</button>
          <button onClick={() => marcarExcluido(processo.numero)} style={{ backgroundColor: '#ef4444', color: 'white', padding: '10px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '12px' }}>✗ Excluir</button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <a href={processo.url_tjsp} target="_blank" rel="noopener noreferrer" style={{ backgroundColor: '#3b82f6', color: 'white', padding: '10px', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '600', fontSize: '12px', textAlign: 'center', textDecoration: 'none' }}>🔗 Ver TJSP</a>
          <button onClick={handleVerificarIndividual} disabled={verificandoIndividual} style={{ backgroundColor: verificandoIndividual ? '#9ca3af' : verificacao ? '#6b7280' : '#8b5cf6', color: 'white', padding: '10px', borderRadius: '8px', border: 'none', cursor: verificandoIndividual ? 'not-allowed' : 'pointer', fontWeight: '600', fontSize: '12px' }}>
            {verificandoIndividual ? '⏳...' : verificacao ? '🔄 Re-verificar' : '🏠 Verificar'}
          </button>
        </div>
      </div>
    );
  };

  const processosAltoValor = processos.filter(p => p.valor_causa && p.valor_causa >= 100000).length;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
      <nav style={{ background: 'linear-gradient(to right, #4f46e5, #7c3aed)', color: 'white', padding: '20px 24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>Judicial Aggregator - TJSP</h1>
        <p style={{ fontSize: '13px', margin: '8px 0 0 0', opacity: 0.9 }}>Busque processos de Inventario e Divorcio - Verifique automaticamente se há imóveis</p>
      </nav>
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '24px' }}>
        <div style={{ backgroundColor: '#fef3c7', borderRadius: '12px', padding: '16px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '14px', color: '#92400e' }}><strong>{interesseIds.size}</strong> interesse</span>
            <span style={{ fontSize: '14px', color: '#92400e' }}><strong>{excluidos.size}</strong> excluidos</span>
            <span style={{ fontSize: '14px', color: '#166534' }}><strong>{estatisticasVerificacao.comImovel}</strong> com imóvel</span>
            <span style={{ fontSize: '14px', color: '#dc2626' }}><strong>{estatisticasVerificacao.semImovel}</strong> sem imóvel</span>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {interesseIds.size > 0 && <button onClick={() => exportarExcel(processosInteresse, 'processos_interesse')} style={{ backgroundColor: '#059669', color: 'white', padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '12px' }}>Exportar</button>}
            {interesseIds.size > 0 && <button onClick={limparInteresse} style={{ backgroundColor: '#f59e0b', color: 'white', padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '12px' }}>Limpar Interesse</button>}
            {excluidos.size > 0 && <button onClick={limparExcluidos} style={{ backgroundColor: '#dc2626', color: 'white', padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '12px' }}>Limpar Excluidos</button>}
            {estatisticasVerificacao.total > 0 && <button onClick={limparVerificacoes} style={{ backgroundColor: '#7c3aed', color: 'white', padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', fontSize: '12px' }}>Limpar Verificações</button>}
          </div>
        </div>
        <div style={{ backgroundColor: 'white', borderRadius: '12px', padding: '24px', marginBottom: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '20px' }}>Buscar Processos</h2>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}><Tooltip texto="Tipos de processo a buscar.">Tipos:</Tooltip></label>
            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
              {['Inventário', 'Divórcio Litigioso', 'Divórcio Consensual'].map(t => (
                <label key={t} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input type="checkbox" checked={tiposSelecionados.includes(t)} onChange={(e) => { if (e.target.checked) setTiposSelecionados([...tiposSelecionados, t]); else setTiposSelecionados(tiposSelecionados.filter(x => x !== t)); }} style={{ width: '18px', height: '18px' }} />
                  <span>{t}</span>
                </label>
              ))}
            </div>
          </div>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}><Tooltip texto="Filtra por cidade/regiao.">Comarcas (opcional):</Tooltip></label>
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
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}><Tooltip texto="Processos por pagina.">Quantidade:</Tooltip></label>
              <select value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))} style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
                <option value={50}>50</option><option value={100}>100</option><option value={200}>200</option><option value={500}>500</option><option value={1000}>1000</option><option value={2000}>2000</option><option value={5000}>5000</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}><Tooltip texto="Valor minimo da causa.">Valor minimo:</Tooltip></label>
              <select value={valorMinimo} onChange={(e) => setValorMinimo(Number(e.target.value))} style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
                <option value={0}>Todos</option><option value={50000}>R$ 50.000+</option><option value={100000}>R$ 100.000+</option><option value={200000}>R$ 200.000+</option><option value={500000}>R$ 500.000+</option><option value={1000000}>R$ 1.000.000+</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}><Tooltip texto="Periodo de ajuizamento.">Periodo:</Tooltip></label>
              <select value={periodoFiltro} onChange={(e) => setPeriodoFiltro(Number(e.target.value))} style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
                <option value={0}>Todos</option><option value={30}>30 dias</option><option value={60}>60 dias</option><option value={90}>90 dias</option><option value={180}>6 meses</option><option value={365}>1 ano</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}><Tooltip texto="Ordenacao dos resultados.">Ordenar:</Tooltip></label>
              <select value={ordenacao} onChange={(e) => setOrdenacao(e.target.value)} style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid #d1d5db' }}>
                <option value="data_desc">Data (recentes)</option><option value="data_asc">Data (antigos)</option><option value="valor_desc">Valor (maior)</option><option value="valor_asc">Valor (menor)</option><option value="imovel">Com imóvel primeiro</option><option value="comarca">Comarca</option><option value="tipo">Tipo</option>
              </select>
            </div>
          </div>
          <button onClick={() => buscarProcessos(1)} disabled={loading || tiposSelecionados.length === 0} style={{ width: '100%', background: loading ? '#9ca3af' : 'linear-gradient(to right, #4f46e5, #7c3aed)', color: 'white', padding: '16px', borderRadius: '8px', border: 'none', fontWeight: 'bold', fontSize: '16px', cursor: loading ? 'not-allowed' : 'pointer' }}>
            {loading ? 'Buscando...' : 'BUSCAR PROCESSOS'}
          </button>
          {tempoBusca !== null && <p style={{ textAlign: 'center', marginTop: '12px', fontSize: '13px', color: '#6b7280' }}>Busca concluida em {tempoBusca.toFixed(1)}s</p>}
        </div>
        {processos.length > 0 && (
          <div style={{ backgroundColor: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '16px', marginBottom: '20px' }}>
              <div style={{ backgroundColor: '#dcfce7', padding: '16px', borderRadius: '8px', textAlign: 'center' }}><p style={{ fontSize: '28px', fontWeight: 'bold', color: '#166534', margin: 0 }}>{processosBusca.length}</p><p style={{ fontSize: '13px', color: '#166534', margin: 0 }}>Para Analisar</p></div>
              <div style={{ backgroundColor: '#dbeafe', padding: '16px', borderRadius: '8px', textAlign: 'center' }}><p style={{ fontSize: '28px', fontWeight: 'bold', color: '#1e40af', margin: 0 }}>{processosComValorFiltrados.length}</p><p style={{ fontSize: '13px', color: '#1e40af', margin: 0 }}>Com Valor</p></div>
              <div style={{ backgroundColor: '#fef3c7', padding: '16px', borderRadius: '8px', textAlign: 'center' }}><p style={{ fontSize: '28px', fontWeight: 'bold', color: '#92400e', margin: 0 }}>{processosSemValor.length}</p><p style={{ fontSize: '13px', color: '#92400e', margin: 0 }}>Sem Valor</p></div>
              <div style={{ backgroundColor: '#d1fae5', padding: '16px', borderRadius: '8px', textAlign: 'center' }}><p style={{ fontSize: '28px', fontWeight: 'bold', color: '#065f46', margin: 0 }}>{processosAltoValor}</p><p style={{ fontSize: '13px', color: '#065f46', margin: 0 }}>Alto Valor</p></div>
              <div style={{ backgroundColor: '#bbf7d0', padding: '16px', borderRadius: '8px', textAlign: 'center' }}><p style={{ fontSize: '28px', fontWeight: 'bold', color: '#166534', margin: 0 }}>{estatisticasVerificacao.comImovel}</p><p style={{ fontSize: '13px', color: '#166534', margin: 0 }}>🏠 Com Imóvel</p></div>
              <div style={{ backgroundColor: '#fce7f3', padding: '16px', borderRadius: '8px', textAlign: 'center' }}><p style={{ fontSize: '28px', fontWeight: 'bold', color: '#9d174d', margin: 0 }}>{processosInteresse.length}</p><p style={{ fontSize: '13px', color: '#9d174d', margin: 0 }}>Interesse</p></div>
            </div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button onClick={() => setAbaAtiva('busca')} style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer', backgroundColor: abaAtiva === 'busca' ? '#4f46e5' : '#e5e7eb', color: abaAtiva === 'busca' ? 'white' : '#374151' }}>Para Analisar ({processosBusca.length})</button>
                <button onClick={() => setAbaAtiva('interesse')} style={{ padding: '12px 24px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer', backgroundColor: abaAtiva === 'interesse' ? '#10b981' : '#e5e7eb', color: abaAtiva === 'interesse' ? 'white' : '#374151' }}>Com Interesse ({processosInteresse.length})</button>
              </div>
              {processosBusca.length > 0 && abaAtiva === 'busca' && (
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <button onClick={verificarLote} disabled={verificandoLote || processosNaoVerificadosPagina === 0} style={{ padding: '10px 16px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: verificandoLote || processosNaoVerificadosPagina === 0 ? 'not-allowed' : 'pointer', backgroundColor: verificandoLote ? '#9ca3af' : '#8b5cf6', color: 'white', fontSize: '13px' }}>
                    {verificandoLote ? `🔄 Verificando ${progressoVerificacao.atual}/${progressoVerificacao.total}...` : `🏠 Verificar Página (${processosNaoVerificadosPagina})`}
                  </button>
                  <button onClick={() => exportarExcel(processosBusca, 'processos_busca')} style={{ padding: '10px 16px', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer', backgroundColor: '#059669', color: 'white', fontSize: '13px' }}>📥 Exportar ({processosBusca.length})</button>
                </div>
              )}
            </div>
            {abaAtiva === 'busca' && estatisticasVerificacao.total > 0 && (
              <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
                <span style={{ fontSize: '14px', fontWeight: '600', color: '#374151' }}>Filtrar:</span>
                <button onClick={() => setFiltroImovel('todos')} style={{ padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', backgroundColor: filtroImovel === 'todos' ? '#4f46e5' : '#e5e7eb', color: filtroImovel === 'todos' ? 'white' : '#374151', fontSize: '12px', fontWeight: '500' }}>Todos</button>
                <button onClick={() => setFiltroImovel('com_imovel')} style={{ padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', backgroundColor: filtroImovel === 'com_imovel' ? '#22c55e' : '#e5e7eb', color: filtroImovel === 'com_imovel' ? 'white' : '#374151', fontSize: '12px', fontWeight: '500' }}>🏠 Com Imóvel ({estatisticasVerificacao.comImovel})</button>
                <button onClick={() => setFiltroImovel('sem_imovel')} style={{ padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', backgroundColor: filtroImovel === 'sem_imovel' ? '#ef4444' : '#e5e7eb', color: filtroImovel === 'sem_imovel' ? 'white' : '#374151', fontSize: '12px', fontWeight: '500' }}>❌ Sem Imóvel ({estatisticasVerificacao.semImovel})</button>
                <button onClick={() => setFiltroImovel('nao_verificado')} style={{ padding: '6px 12px', borderRadius: '6px', border: 'none', cursor: 'pointer', backgroundColor: filtroImovel === 'nao_verificado' ? '#f59e0b' : '#e5e7eb', color: filtroImovel === 'nao_verificado' ? 'white' : '#374151', fontSize: '12px', fontWeight: '500' }}>⏳ Não Verificados</button>
              </div>
            )}
            {abaAtiva === 'busca' && (
              <>
                {totalPaginas > 1 && (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginBottom: '20px', padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
                    <button onClick={() => setPaginaAtual(p => Math.max(1, p - 1))} disabled={paginaAtual === 1} style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: paginaAtual === 1 ? '#e5e7eb' : '#4f46e5', color: paginaAtual === 1 ? '#9ca3af' : 'white', cursor: paginaAtual === 1 ? 'not-allowed' : 'pointer', fontWeight: '600' }}>Anterior</button>
                    <span style={{ fontSize: '14px', fontWeight: '600' }}>Pagina {paginaAtual} de {totalPaginas}</span>
                    <button onClick={() => setPaginaAtual(p => Math.min(totalPaginas, p + 1))} disabled={paginaAtual === totalPaginas} style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: paginaAtual === totalPaginas ? '#e5e7eb' : '#4f46e5', color: paginaAtual === totalPaginas ? '#9ca3af' : 'white', cursor: paginaAtual === totalPaginas ? 'not-allowed' : 'pointer', fontWeight: '600' }}>Proxima</button>
                  </div>
                )}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>{processosPaginados.map(p => <ProcessoCard key={p.numero} processo={p} />)}</div>
                {totalPaginas > 1 && (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', marginTop: '20px', padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px' }}>
                    <button onClick={() => setPaginaAtual(p => Math.max(1, p - 1))} disabled={paginaAtual === 1} style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: paginaAtual === 1 ? '#e5e7eb' : '#4f46e5', color: paginaAtual === 1 ? '#9ca3af' : 'white', cursor: paginaAtual === 1 ? 'not-allowed' : 'pointer', fontWeight: '600' }}>Anterior</button>
                    <span style={{ fontSize: '14px', fontWeight: '600' }}>Pagina {paginaAtual} de {totalPaginas}</span>
                    <button onClick={() => setPaginaAtual(p => Math.min(totalPaginas, p + 1))} disabled={paginaAtual === totalPaginas} style={{ padding: '10px 20px', borderRadius: '8px', border: 'none', backgroundColor: paginaAtual === totalPaginas ? '#e5e7eb' : '#4f46e5', color: paginaAtual === totalPaginas ? '#9ca3af' : 'white', cursor: paginaAtual === totalPaginas ? 'not-allowed' : 'pointer', fontWeight: '600' }}>Proxima</button>
                  </div>
                )}
              </>
            )}
            {abaAtiva === 'interesse' && <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>{processosInteresse.map(p => <ProcessoCard key={p.numero} processo={p} />)}</div>}
            {((abaAtiva === 'busca' && processosPaginados.length === 0) || (abaAtiva === 'interesse' && processosInteresse.length === 0)) && <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}><p>Nenhum processo nesta aba</p></div>}
          </div>
        )}
      </div>
    </div>
  );
}
