'use client';
import { useState } from 'react';

export default function Home() {
  const [processos, setProcessos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [stats, setStats] = useState(null);
  const [tribunal, setTribunal] = useState('TJSP');
  const [tipo, setTipo] = useState('Inventário');
  const [valorMin, setValorMin] = useState('');
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
          valor_causa_min: valorMin ? Number(valorMin) : undefined,
          limit: quantidade
        })
      });
      const data = await response.json();
      setProcessos(data.processos || []);
      setStats(data.stats);
    } catch (error) {
      alert('Erro ao buscar');
    }
    setLoading(false);
  }

  return (
    <div style={{minHeight: '100vh', background: '#f9fafb', padding: '2rem'}}>
      <div style={{maxWidth: '1280px', margin: '0 auto'}}>
        <h1 style={{fontSize: '2rem', fontWeight: 'bold', marginBottom: '2rem'}}>Judicial Aggregator</h1>
        
        <div style={{background: 'white', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)'}}>
          <h2 style={{fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1.5rem'}}>Buscar Processos</h2>
          
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem'}}>
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem'}}>Tribunal</label>
              <select value={tribunal} onChange={(e) => setTribunal(e.target.value)} style={{width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '4px'}}>
                <option value="TJSP">TJSP</option>
                <option value="TJBA">TJBA</option>
              </select>
            </div>
            
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem'}}>Tipo</label>
              <select value={tipo} onChange={(e) => setTipo(e.target.value)} style={{width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '4px'}}>
                <option value="Inventário">Inventário</option>
                <option value="Divórcio Litigioso">Divórcio Litigioso</option>
              </select>
            </div>
            
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem'}}>Valor Mínimo</label>
              <input type="number" value={valorMin} onChange={(e) => setValorMin(e.target.value)} placeholder="100000" style={{width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '4px'}} />
            </div>
            
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem'}}>Quantidade</label>
              <select value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))} style={{width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '4px'}}>
                <option value="50">50</option>
                <option value="500">500</option>
              </select>
            </div>
          </div>
          
          <button onClick={handleBuscar} disabled={loading} style={{width: '100%', background: loading ? '#9ca3af' : '#2563eb', color: 'white', padding: '1rem', borderRadius: '8px', fontSize: '1.125rem', fontWeight: 'bold', border: 'none', cursor: loading ? 'not-allowed' : 'pointer'}}>
            {loading ? 'Buscando...' : 'BUSCAR PROCESSOS'}
          </button>
        </div>

        {stats && (
          <div style={{background: 'white', borderRadius: '8px', padding: '1.5rem', marginBottom: '1.5rem'}}>
            <div style={{display: 'flex', gap: '1rem'}}>
              <div style={{background: '#d1fae5', padding: '0.5rem 1rem', borderRadius: '4px'}}>Novos: {stats.novos}</div>
              <div style={{background: '#dbeafe', padding: '0.5rem 1rem', borderRadius: '4px'}}>Duplicados: {stats.duplicados}</div>
              <div style={{background: '#fee2e2', padding: '0.5rem 1rem', borderRadius: '4px'}}>Inativos: {stats.inativos}</div>
            </div>
          </div>
        )}

        {!searched && !loading && (
          <div style={{background: 'white', borderRadius: '8px', padding: '3rem', textAlign: 'center'}}>
            <p style={{fontSize: '1.25rem', color: '#6b7280'}}>Use o formulário acima para buscar processos</p>
          </div>
        )}

        {loading && <div style={{textAlign: 'center', padding: '5rem', fontSize: '1.5rem'}}>Buscando...</div>}

        {processos.length > 0 && (
          <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            {processos.map((p) => (
              <div key={p.id} style={{background: p.novo ? '#eff6ff' : 'white', border: p.novo ? '2px solid #60a5fa' : '1px solid #e5e7eb', borderRadius: '8px', padding: '1.5rem'}}>
                {p.novo && <span style={{background: '#2563eb', color: 'white', padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.875rem', fontWeight: 'bold', marginRight: '0.5rem'}}>NOVO</span>}
                <h3 style={{fontSize: '1.125rem', fontWeight: 'bold', fontFamily: 'monospace'}}>{p.numero_cnj}</h3>
                <p style={{color: '#6b7280'}}>{p.tipo_processo} - {p.tribunal}</p>
              </div>
            ))}
          </div>
        )}

        {searched && processos.length === 0 && !loading && (
          <div style={{background: 'white', borderRadius: '8px', padding: '3rem', textAlign: 'center'}}>
            <p style={{fontSize: '1.25rem', color: '#6b7280'}}>Nenhum processo encontrado</p>
          </div>
        )}
      </div>
    </div>
  );
}
