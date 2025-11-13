'use client';
import { useState, useEffect } from 'react';

type Tab = 'busca' | 'interesse' | 'descartados';

export default function Home() {
  const [processos, setProcessos] = useState([]);
  const [interesseIds, setInteresseIds] = useState<Set<number>>(new Set());
  const [descartadosIds, setDescartadosIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState<Tab>('busca');
  
  const [tribunais, setTribunais] = useState({ TJSP: true, TJBA: false });
  const [tipo, setTipo] = useState('Inventário');
  const [comarcas, setComarcas] = useState<string[]>([]);
  const [comarcaInput, setComarcaInput] = useState('');
  const [valorMin, setValorMin] = useState('');
  const [valorMax, setValorMax] = useState('');
  const [ano, setAno] = useState('');
  const [quantidade, setQuantidade] = useState(500);

  useEffect(() => {
    const saved = localStorage.getItem('judicial_interesse');
    if (saved) setInteresseIds(new Set(JSON.parse(saved)));
    const desc = localStorage.getItem('judicial_descartados');
    if (desc) setDescartadosIds(new Set(JSON.parse(desc)));
  }, []);

  const salvarInteresse = (ids: Set<number>) => {
    localStorage.setItem('judicial_interesse', JSON.stringify(Array.from(ids)));
    setInteresseIds(new Set(ids));
  };

  const salvarDescartados = (ids: Set<number>) => {
    localStorage.setItem('judicial_descartados', JSON.stringify(Array.from(ids)));
    setDescartadosIds(new Set(ids));
  };

  const marcarInteresse = async (id: number) => {
    await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'interesse' })
    });
    const novos = new Set(interesseIds);
    novos.add(id);
    salvarInteresse(novos);
  };

  const descartar = async (id: number) => {
    await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'descartado' })
    });
    const novos = new Set(descartadosIds);
    novos.add(id);
    salvarDescartados(novos);
  };

  const adicionarComarca = () => {
    if (comarcaInput.trim() && !comarcas.includes(comarcaInput.trim())) {
      setComarcas([...comarcas, comarcaInput.trim()]);
      setComarcaInput('');
    }
  };

  const removerComarca = (c: string) => {
    setComarcas(comarcas.filter(x => x !== c));
  };

  async function handleBuscar() {
    setLoading(true);
    setSearched(true);
    const tribunaisSelecionados = Object.keys(tribunais).filter(k => tribunais[k]);
    
    try {
      let todosProcessos = [];
      let todosStats = { novos: 0, duplicados: 0, inativos: 0 };
      
      for (const trib of tribunaisSelecionados) {
        const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tribunal: trib,
            tipo_processo: tipo,
            valor_causa_min: valorMin ? Number(valorMin) : undefined,
            valor_causa_max: valorMax ? Number(valorMax) : undefined,
            limit: quantidade
          })
        });
        const data = await response.json();
        todosProcessos = [...todosProcessos, ...(data.processos || [])];
        todosStats.novos += data.stats?.novos || 0;
        todosStats.duplicados += data.stats?.duplicados || 0;
        todosStats.inativos += data.stats?.inativos || 0;
      }
      
      setProcessos(todosProcessos);
      setStats(todosStats);
    } catch (error) {
      alert('Erro ao buscar');
    }
    setLoading(false);
  }

  const anos = [];
  for (let i = 2025; i >= 2000; i--) anos.push(i);

  const processosFiltrados = processos.filter(p => {
    if (activeTab === 'interesse') return interesseIds.has(p.id);
    if (activeTab === 'descartados') return descartadosIds.has(p.id);
    return !descartadosIds.has(p.id);
  });

  return (
    <div style={{minHeight: '100vh', background: '#f3f4f6', padding: '2rem'}}>
      <div style={{maxWidth: '1400px', margin: '0 auto'}}>
        <h1 style={{fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '2rem'}}>⚖️ Judicial Aggregator</h1>
        
        <div style={{background: 'white', borderRadius: '12px', padding: '2rem', marginBottom: '2rem', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}>
          <h2 style={{fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '1.5rem'}}>🔍 Buscar Processos Ativos</h2>
          
          <div style={{marginBottom: '1.5rem'}}>
            <label style={{display: 'block', marginBottom: '0.75rem', fontWeight: '600', fontSize: '1rem'}}>Tribunais *</label>
            <div style={{display: 'flex', gap: '2rem'}}>
              <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
                <input type="checkbox" checked={tribunais.TJSP} onChange={(e) => setTribunais({...tribunais, TJSP: e.target.checked})} style={{width: '20px', height: '20px'}} />
                <span style={{fontSize: '1.125rem'}}>TJSP - São Paulo</span>
              </label>
              <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
                <input type="checkbox" checked={tribunais.TJBA} onChange={(e) => setTribunais({...tribunais, TJBA: e.target.checked})} style={{width: '20px', height: '20px'}} />
                <span style={{fontSize: '1.125rem'}}>TJBA - Bahia</span>
              </label>
            </div>
          </div>

          <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '1.5rem'}}>
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Tipo *</label>
              <select value={tipo} onChange={(e) => setTipo(e.target.value)} style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}}>
                <option value="Inventário">Inventário</option>
                <option value="Divórcio Litigioso">Divórcio Litigioso</option>
                <option value="Divórcio Consensual">Divórcio Consensual</option>
              </select>
            </div>
            
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Quantidade *</label>
              <select value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))} style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}}>
                <option value="50">50 processos</option>
                <option value="100">100 processos</option>
                <option value="500">500 processos</option>
                <option value="1000">1.000 processos</option>
              </select>
            </div>
            
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Ano</label>
              <select value={ano} onChange={(e) => setAno(e.target.value)} style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}}>
                <option value="">Todos</option>
                {anos.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>

            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Valor Mínimo (R$)</label>
              <input type="number" value={valorMin} onChange={(e) => setValorMin(e.target.value)} placeholder="100000" style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}} />
            </div>

            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Valor Máximo (R$)</label>
              <input type="number" value={valorMax} onChange={(e) => setValorMax(e.target.value)} placeholder="5000000" style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}} />
            </div>
          </div>

          <div style={{background: '#eff6ff', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.875rem', color: '#1e40af'}}>
            ℹ️ <strong>Filtra automaticamente:</strong> Apenas processos ATIVOS (exclui extintos, suspensos, arquivados)
          </div>
          
          <button onClick={handleBuscar} disabled={loading || (!tribunais.TJSP && !tribunais.TJBA)} style={{width: '100%', background: (loading || (!tribunais.TJSP && !tribunais.TJBA)) ? '#9ca3af' : '#2563eb', color: 'white', padding: '1.25rem', borderRadius: '10px', fontSize: '1.25rem', fontWeight: 'bold', border: 'none', cursor: (loading || (!tribunais.TJSP && !tribunais.TJBA)) ? 'not-allowed' : 'pointer'}}>
            {loading ? '🔄 Buscando...' : '🔍 BUSCAR PROCESSOS'}
          </button>
        </div>

        {stats && (
          <div style={{background: 'white', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.1)'}}>
            <h3 style={{fontWeight: 'bold', marginBottom: '1rem'}}>📊 Resultados:</h3>
            <div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap'}}>
              <div style={{background: '#d1fae5', padding: '0.75rem 1.5rem', borderRadius: '8px', fontWeight: '600'}}>✅ Novos: {stats.novos}</div>
              <div style={{background: '#dbeafe', padding: '0.75rem 1.5rem', borderRadius: '8px', fontWeight: '600'}}>🔄 Duplicados: {stats.duplicados}</div>
              <div style={{background: '#fee2e2', padding: '0.75rem 1.5rem', borderRadius: '8px', fontWeight: '600'}}>❌ Inativos: {stats.inativos}</div>
            </div>
          </div>
        )}

        {searched && (
          <div style={{marginBottom: '1.5rem', background: 'white', borderRadius: '12px', padding: '0.5rem', display: 'flex', gap: '0.5rem'}}>
            <button onClick={() => setActiveTab('busca')} style={{flex: 1, padding: '1rem', background: activeTab === 'busca' ? '#2563eb' : 'transparent', color: activeTab === 'busca' ? 'white' : '#374151', border: 'none', borderRadius: '8px', fontWeight: '600', cursor: 'pointer'}}>
              📋 Busca ({processos.filter(p => !descartadosIds.has(p.id)).length})
            </button>
            <button onClick={() => setActiveTab('interesse')} style={{flex: 1, padding: '1rem', background: activeTab === 'interesse' ? '#10b981' : 'transparent', color: activeTab === 'interesse' ? 'white' : '#374151', border: 'none', borderRadius: '8px', fontWeight: '600', cursor: 'pointer'}}>
              ⭐ Interesse ({interesseIds.size})
            </button>
            <button onClick={() => setActiveTab('descartados')} style={{flex: 1, padding: '1rem', background: activeTab === 'descartados' ? '#ef4444' : 'transparent', color: activeTab === 'descartados' ? 'white' : '#374151', border: 'none', borderRadius: '8px', fontWeight: '600', cursor: 'pointer'}}>
              🗑️ Descartados ({descartadosIds.size})
            </button>
          </div>
        )}

        {!searched && !loading && (
          <div style={{background: 'white', borderRadius: '12px', padding: '4rem', textAlign: 'center'}}>
            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>🔍</div>
            <p style={{fontSize: '1.5rem', fontWeight: '600', marginBottom: '0.5rem'}}>Pronto para buscar</p>
            <p style={{color: '#6b7280'}}>Configure os filtros e clique em BUSCAR</p>
          </div>
        )}

        {loading && (
          <div style={{textAlign: 'center', padding: '6rem'}}>
            <div style={{fontSize: '5rem', marginBottom: '1rem'}}>🔄</div>
            <p style={{fontSize: '1.75rem', fontWeight: '600'}}>Buscando processos ativos...</p>
          </div>
        )}

        {processosFiltrados.length > 0 && (
          <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            {processosFiltrados.map((p) => (
              <div key={p.id} style={{background: p.novo ? '#dbeafe' : 'white', border: p.novo ? '3px solid #3b82f6' : '1px solid #e5e7eb', borderRadius: '12px', padding: '1.75rem', boxShadow: p.novo ? '0 4px 20px rgba(59, 130, 246, 0.3)' : '0 2px 8px rgba(0,0,0,0.1)'}}>
                <div style={{marginBottom: '1rem'}}>
                  {p.novo && <span style={{background: '#3b82f6', color: 'white', padding: '0.5rem 1rem', borderRadius: '6px', fontSize: '0.875rem', fontWeight: 'bold', marginRight: '0.75rem'}}>🆕 NOVO</span>}
                  {p.valor_causa > 1000000 && <span style={{background: '#f59e0b', color: 'white', padding: '0.5rem 1rem', borderRadius: '6px', fontSize: '0.875rem', fontWeight: 'bold'}}>💎 ALTO VALOR</span>}
                </div>
                <h3 style={{fontSize: '1.25rem', fontWeight: 'bold', fontFamily: 'monospace', marginBottom: '0.75rem'}}>{p.numero_cnj}</h3>
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', color: '#6b7280', marginBottom: '1.5rem'}}>
                  <p><strong>Tipo:</strong> {p.tipo_processo}</p>
                  <p><strong>Tribunal:</strong> {p.tribunal}</p>
                </div>
                
                {activeTab === 'busca' && !interesseIds.has(p.id) && !descartadosIds.has(p.id) && (
                  <div style={{display: 'flex', gap: '1rem'}}>
                    <button onClick={() => marcarInteresse(p.id)} style={{flex: 1, background: '#10b981', color: 'white', padding: '0.875rem', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer'}}>
                      ⭐ Marcar Interesse
                    </button>
                    <button onClick={() => descartar(p.id)} style={{flex: 1, background: '#ef4444', color: 'white', padding: '0.875rem', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer'}}>
                      🗑️ Descartar
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {searched && processosFiltrados.length === 0 && !loading && (
          <div style={{background: 'white', borderRadius: '12px', padding: '4rem', textAlign: 'center'}}>
            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>📭</div>
            <p style={{fontSize: '1.5rem', fontWeight: '600'}}>Nenhum processo nesta aba</p>
          </div>
        )}
      </div>
    </div>
  );
}
