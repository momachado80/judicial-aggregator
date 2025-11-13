'use client';
import { useState } from 'react';

export default function Home() {
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [stats, setStats] = useState(null);
  
  const [tribunal, setTribunal] = useState('TJSP');
  const [tipo, setTipo] = useState('Inventário');
  const [comarca, setComarca] = useState('');
  const [valorMin, setValorMin] = useState('');
  const [valorMax, setValorMax] = useState('');
  const [ano, setAno] = useState('');
  const [quantidade, setQuantidade] = useState(500);

  async function handleBuscar() {
    setLoading(true);
    setSearched(true);
    try {
      const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tribunal,
          tipo_processo: tipo,
          comarca: comarca || undefined,
          valor_causa_min: valorMin ? Number(valorMin) : undefined,
          valor_causa_max: valorMax ? Number(valorMax) : undefined,
          ano: ano || undefined,
          limit: quantidade
        })
      });
      const data = await response.json();
      setProcessos(data.processos || []);
      setStats(data.stats);
    } catch (error) {
      alert('Erro ao buscar processos');
    }
    setLoading(false);
  }

  const anos = [];
  for (let i = 2025; i >= 2000; i--) {
    anos.push(i);
  }

  return (
    <div style={{minHeight: '100vh', background: '#f9fafb', padding: '2rem'}}>
      <div style={{maxWidth: '1400px', margin: '0 auto'}}>
        <h1 style={{fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '2rem'}}>⚖️ Judicial Aggregator</h1>
        
        <div style={{background: 'white', borderRadius: '12px', padding: '2rem', marginBottom: '2rem', boxShadow: '0 2px 8px rgba(0,0,0,0.1)'}}>
          <h2 style={{fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '1.5rem'}}>🔍 Buscar Processos Ativos</h2>
          
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '1.5rem'}}>
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Tribunal *</label>
              <select value={tribunal} onChange={(e) => setTribunal(e.target.value)} style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}}>
                <option value="TJSP">TJSP - São Paulo</option>
                <option value="TJBA">TJBA - Bahia</option>
              </select>
            </div>
            
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Tipo de Processo *</label>
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
                <option value="200">200 processos</option>
                <option value="500">500 processos</option>
                <option value="1000">1.000 processos</option>
              </select>
            </div>

            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Comarca (opcional)</label>
              <input type="text" value={comarca} onChange={(e) => setComarca(e.target.value)} placeholder="Ex: São Paulo, Salvador..." style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}} />
            </div>
            
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Ano (opcional)</label>
              <select value={ano} onChange={(e) => setAno(e.target.value)} style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}}>
                <option value="">Todos os anos</option>
                {anos.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Valor Mínimo (R$)</label>
              <input type="number" value={valorMin} onChange={(e) => setValorMin(e.target.value)} placeholder="Ex: 100000" style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}} />
            </div>

            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Valor Máximo (R$)</label>
              <input type="number" value={valorMax} onChange={(e) => setValorMax(e.target.value)} placeholder="Ex: 5000000" style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}} />
            </div>
          </div>

          <div style={{background: '#eff6ff', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem'}}>
            <p style={{fontSize: '0.875rem', color: '#1e40af'}}>
              ℹ️ <strong>Sistema filtra automaticamente:</strong> Apenas processos ATIVOS (exclui extintos, suspensos e arquivados)
            </p>
          </div>
          
          <button onClick={handleBuscar} disabled={loading} style={{width: '100%', background: loading ? '#9ca3af' : '#2563eb', color: 'white', padding: '1.25rem', borderRadius: '10px', fontSize: '1.25rem', fontWeight: 'bold', border: 'none', cursor: loading ? 'not-allowed' : 'pointer', transition: 'all 0.2s'}}>
            {loading ? '🔄 Buscando processos...' : '🔍 BUSCAR PROCESSOS'}
          </button>
        </div>

        {stats && (
          <div style={{background: 'white', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.1)'}}>
            <h3 style={{fontWeight: 'bold', marginBottom: '1rem', fontSize: '1.125rem'}}>📊 Resultados da Busca:</h3>
            <div style={{display: 'flex', gap: '1rem', flexWrap: 'wrap'}}>
              <div style={{background: '#d1fae5', padding: '0.75rem 1.5rem', borderRadius: '8px', fontWeight: '600'}}>
                ✅ Novos: <strong>{stats.novos}</strong>
              </div>
              <div style={{background: '#dbeafe', padding: '0.75rem 1.5rem', borderRadius: '8px', fontWeight: '600'}}>
                🔄 Já existiam: <strong>{stats.duplicados}</strong>
              </div>
              <div style={{background: '#fee2e2', padding: '0.75rem 1.5rem', borderRadius: '8px', fontWeight: '600'}}>
                ❌ Inativos filtrados: <strong>{stats.inativos}</strong>
              </div>
            </div>
          </div>
        )}

        {!searched && !loading && (
          <div style={{background: 'white', borderRadius: '12px', padding: '4rem', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.1)'}}>
            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>🔍</div>
            <p style={{fontSize: '1.5rem', color: '#374151', marginBottom: '0.5rem', fontWeight: '600'}}>
              Pronto para buscar processos
            </p>
            <p style={{fontSize: '1rem', color: '#6b7280'}}>
              Configure os filtros acima e clique em BUSCAR PROCESSOS
            </p>
          </div>
        )}

        {loading && (
          <div style={{textAlign: 'center', padding: '6rem'}}>
            <div style={{fontSize: '5rem', marginBottom: '1rem', animation: 'spin 2s linear infinite'}}>🔄</div>
            <p style={{fontSize: '1.75rem', color: '#374151', fontWeight: '600'}}>Buscando processos ativos...</p>
            <p style={{fontSize: '1rem', color: '#6b7280', marginTop: '0.5rem'}}>Isso pode levar alguns segundos</p>
          </div>
        )}

        {processos.length > 0 && (
          <div>
            <h3 style={{fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem'}}>
              📋 {processos.length} processo(s) encontrado(s)
            </h3>
            <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
              {processos.map((p) => (
                <div key={p.id} style={{background: p.novo ? '#eff6ff' : 'white', border: p.novo ? '3px solid #3b82f6' : '1px solid #e5e7eb', borderRadius: '12px', padding: '1.75rem', boxShadow: '0 2px 8px rgba(0,0,0,0.1)'}}>
                  <div style={{marginBottom: '1rem'}}>
                    {p.novo && (
                      <span style={{background: '#2563eb', color: 'white', padding: '0.375rem 1rem', borderRadius: '6px', fontSize: '0.875rem', fontWeight: 'bold', marginRight: '0.75rem'}}>
                        🆕 NOVO
                      </span>
                    )}
                    {p.valor_causa > 1000000 && (
                      <span style={{background: '#f59e0b', color: 'white', padding: '0.375rem 1rem', borderRadius: '6px', fontSize: '0.875rem', fontWeight: 'bold'}}>
                        💎 ALTO VALOR
                      </span>
                    )}
                  </div>
                  <h3 style={{fontSize: '1.25rem', fontWeight: 'bold', fontFamily: 'monospace', marginBottom: '0.75rem', color: '#111827'}}>
                    {p.numero_cnj}
                  </h3>
                  <div style={{display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', color: '#6b7280'}}>
                    <p><strong>Tipo:</strong> {p.tipo_processo}</p>
                    <p><strong>Tribunal:</strong> {p.tribunal}</p>
                    {p.comarca && <p><strong>Comarca:</strong> {p.comarca}</p>}
                    {p.valor_causa && (
                      <p><strong>Valor:</strong> {new Intl.NumberFormat('pt-BR', {style: 'currency', currency: 'BRL'}).format(p.valor_causa)}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {searched && processos.length === 0 && !loading && (
          <div style={{background: 'white', borderRadius: '12px', padding: '4rem', textAlign: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.1)'}}>
            <div style={{fontSize: '4rem', marginBottom: '1rem'}}>🔍</div>
            <p style={{fontSize: '1.5rem', color: '#374151', fontWeight: '600'}}>Nenhum processo encontrado</p>
            <p style={{fontSize: '1rem', color: '#6b7280', marginTop: '0.5rem'}}>
              Tente ajustar os filtros ou aumentar a quantidade
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
