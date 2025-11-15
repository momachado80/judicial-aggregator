'use client';
import { useState, useEffect } from 'react';

export default function Home() {
  const [tribunaisSelecionados, setTribunaisSelecionados] = useState(['TJSP']);
  const [tiposSelecionados, setTiposSelecionados] = useState(['Inventário']);
  const [comarcasSelecionadas, setComarcasSelecionadas] = useState([]);
  const [inputComarca, setInputComarca] = useState('');
  const [quantidade, setQuantidade] = useState(500);
  const [ano, setAno] = useState('Todos');
  const [valorMin, setValorMin] = useState('100000');
  const [valorMax, setValorMax] = useState('5000000');
  const [processos, setProcessos] = useState([]);
  const [stats, setStats] = useState({ novos: 0, duplicados: 0, inativos: 0 });
  const [loading, setLoading] = useState(false);
  
  // Estados para comarcas dinâmicas
  const [tjspComarcas, setTjspComarcas] = useState([]);
  const [tjbaComarcas, setTjbaComarcas] = useState([]);
  const [comarcasLoading, setComarcasLoading] = useState(true);

  // Buscar comarcas da API ao carregar
  useEffect(() => {
    fetch('https://judicial-aggregator-production.up.railway.app/api/comarcas')
      .then(res => res.json())
      .then(data => {
        setTjspComarcas(data.TJSP || []);
        setTjbaComarcas(data.TJBA || []);
        setComarcasLoading(false);
      })
      .catch(err => {
        console.error('Erro ao carregar comarcas:', err);
        setComarcasLoading(false);
      });
  }, []);
  const [interesseIds, setInteresseIds] = useState(new Set());
  const [descartadosIds, setDescartadosIds] = useState(new Set());

  const comarcasDisponiveis = tribunaisSelecionados.includes('TJSP') 
    ? tjspComarcas 
    : tjbaComarcas;

  const adicionarComarca = (comarca) => {
    const comarcaTrimmed = comarca.trim();
    if (comarcaTrimmed && !comarcasSelecionadas.includes(comarcaTrimmed)) {
      setComarcasSelecionadas([...comarcasSelecionadas, comarcaTrimmed]);
      setInputComarca('');
    }
  };

  const removerComarca = (comarca) => {
    setComarcasSelecionadas(comarcasSelecionadas.filter(c => c !== comarca));
  };

  const marcarInteresse = async (id) => {
    await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'interesse' })
    });
    const novos = new Set(interesseIds);
    novos.add(id);
    setInteresseIds(novos);
    const desc = new Set(descartadosIds);
    desc.delete(id);
    setDescartadosIds(desc);
  };

  const marcarDescartado = async (id) => {
    await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'descartado' })
    });
    const novos = new Set(descartadosIds);
    novos.add(id);
    setDescartadosIds(novos);
    const inter = new Set(interesseIds);
    inter.delete(id);
    setInteresseIds(inter);
  };

  const buscarProcessos = async () => {
    setLoading(true);
    try {
      let todosProcessos = [];
      
      for (const trib of tribunaisSelecionados) {
        for (const tipo of tiposSelecionados) {
          const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              tribunais: [trib],
              tipos_processo: [tipo],
              comarcas: comarcasSelecionadas.length > 0 ? comarcasSelecionadas : undefined,
              valor_causa_min: valorMin ? Number(valorMin) : undefined,
              valor_causa_max: valorMax ? Number(valorMax) : undefined,
              quantidade: Math.floor(quantidade / (tribunaisSelecionados.length * tiposSelecionados.length))
            })
          });
          const data = await response.json();
          todosProcessos = [...todosProcessos, ...(Array.isArray(data) ? data : [])];
        }
      }
      
      setProcessos(todosProcessos);
      setStats({
        novos: todosProcessos.length,
        duplicados: 0,
        inativos: 0
      });
    } catch (error) {
      console.error('Erro ao buscar:', error);
      alert('Erro ao buscar processos');
    }
    setLoading(false);
  }

  const anos = [];
  for (let i = 2025; i >= 2000; i--) anos.push(i);

  const processosBusca = processos.filter(p => !interesseIds.has(p.numero) && !descartadosIds.has(p.numero));
  const processosInteresse = processos.filter(p => interesseIds.has(p.numero));
  const processosDescartados = processos.filter(p => descartadosIds.has(p.numero));

  const formatarValor = (valor) => {
    if (!valor) return 'Não informado';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  const formatarData = (data) => {
    if (!data) return 'Não informada';
    const ano = data.substring(0, 4);
    const mes = data.substring(4, 6);
    const dia = data.substring(6, 8);
    return `${dia}/${mes}/${ano}`;
  };

  const ProcessoCard = ({ processo, onInteresse, onDescartar }) => (
    <div style={{
      backgroundColor: 'white',
      padding: '24px',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      border: '1px solid #e5e7eb'
    }}>
      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Número:</p>
        <a 
          href={processo.url_tjsp} 
          target="_blank" 
          rel="noopener noreferrer"
          style={{
            color: '#2563eb',
            fontFamily: 'monospace',
            fontSize: '14px',
            fontWeight: '600',
            textDecoration: 'none'
          }}
        >
          {processo.numero}
        </a>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '12px', color: '#6b7280' }}>Tipo:</p>
        <p style={{ fontWeight: '600' }}>{processo.tipo}</p>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '12px', color: '#6b7280' }}>Comarca:</p>
        <p style={{ fontWeight: '600', color: '#7c3aed' }}>{processo.comarca}</p>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '12px', color: '#6b7280' }}>Tribunal:</p>
        <p style={{ fontWeight: '600' }}>{processo.tribunal}</p>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '12px', color: '#6b7280' }}>Valor da Causa:</p>
        <p style={{ fontWeight: '600', color: '#059669' }}>{formatarValor(processo.valor_causa)}</p>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontSize: '12px', color: '#6b7280' }}>Data Ajuizamento:</p>
        <p style={{ fontWeight: '600' }}>{formatarData(processo.data_ajuizamento)}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <button
          onClick={() => onInteresse(processo.numero)}
          style={{
            backgroundColor: '#10b981',
            color: 'white',
            padding: '12px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          ⭐ Interesse
        </button>
        <button
          onClick={() => onDescartar(processo.numero)}
          style={{
            backgroundColor: '#ef4444',
            color: 'white',
            padding: '12px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '600'
          }}
        >
          🗑️ Descartar
        </button>
      </div>
    </div>
  );

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(to bottom right, #eff6ff, #e0e7ff)' }}>
      <nav style={{
        background: 'linear-gradient(to right, #4f46e5, #7c3aed)',
        color: 'white',
        padding: '24px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h1 style={{ fontSize: '30px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
            <span>⚖️</span> Judicial Aggregator
          </h1>
        </div>
      </nav>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          padding: '32px',
          marginBottom: '32px'
        }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🔍</span> Buscar Processos Ativos
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Tribunais *</label>
              <div style={{ display: 'flex', gap: '16px' }}>
                {['TJSP', 'TJBA'].map(t => (
                  <label key={t} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={tribunaisSelecionados.includes(t)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setTribunaisSelecionados([...tribunaisSelecionados, t]);
                        } else {
                          setTribunaisSelecionados(tribunaisSelecionados.filter(x => x !== t));
                        }
                      }}
                      style={{ width: '16px', height: '16px' }}
                    />
                    <span>{t}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Tipos *</label>
              <div style={{ display: 'flex', gap: '16px' }}>
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
                      style={{ width: '16px', height: '16px' }}
                    />
                    <span>{t}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>
                Comarcas - {tjspComarcas.length} SP + {tjbaComarcas.length} BA = {tjspComarcas.length + tjbaComarcas.length} total
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  value={inputComarca}
                  onChange={(e) => setInputComarca(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && adicionarComarca(inputComarca)}
                  placeholder="Digite: Piracicaba, Americana, Salvador..."
                  style={{
                    flex: 1,
                    padding: '12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px'
                  }}
                  list="comarcas-list"
                />
                <button
                  onClick={() => adicionarComarca(inputComarca)}
                  style={{
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    padding: '0 24px',
                    borderRadius: '8px',
                    border: 'none',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  + Adicionar
                </button>
              </div>
              <datalist id="comarcas-list">
                {comarcasDisponiveis.map(c => <option key={c} value={c} />)}
              </datalist>
              
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
                {comarcasSelecionadas.map(c => (
                  <span key={c} style={{
                    backgroundColor: '#dbeafe',
                    color: '#1e40af',
                    padding: '8px 16px',
                    borderRadius: '9999px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '14px',
                    fontWeight: '600'
                  }}>
                    {c}
                    <button onClick={() => removerComarca(c)} style={{
                      color: '#dc2626',
                      fontWeight: 'bold',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '18px'
                    }}>×</button>
                  </span>
                ))}
              </div>

              {comarcasSelecionadas.length > 0 && (
                <div style={{
                  marginTop: '12px',
                  padding: '12px',
                  backgroundColor: '#dcfce7',
                  borderRadius: '8px'
                }}>
                  <p style={{ fontSize: '14px', color: '#166534', margin: 0, fontWeight: '600' }}>
                    ✅ Filtro ativo: apenas processos de {comarcasSelecionadas.join(', ')}
                  </p>
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Quantidade *</label>
                <select value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))} style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px'
                }}>
                  {[50, 100, 200, 500, 1000].map(q => <option key={q} value={q}>{q}</option>)}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Ano</label>
                <select value={ano} onChange={(e) => setAno(e.target.value)} style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px'
                }}>
                  <option>Todos</option>
                  {anos.map(a => <option key={a}>{a}</option>)}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Valor Mín (R$)</label>
                <input
                  type="number"
                  value={valorMin}
                  onChange={(e) => setValorMin(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>Valor Máx (R$)</label>
                <input
                  type="number"
                  value={valorMax}
                  onChange={(e) => setValorMax(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px'
                  }}
                />
              </div>
            </div>

            <div style={{
              backgroundColor: '#eff6ff',
              padding: '16px',
              borderRadius: '8px'
            }}>
              <p style={{ fontSize: '14px', color: '#1e40af', margin: 0 }}>
                ℹ️ Apenas processos ATIVOS (exclui extintos, suspensos, arquivados)
              </p>
            </div>

            <button
              onClick={buscarProcessos}
              disabled={loading}
              style={{
                width: '100%',
                background: 'linear-gradient(to right, #2563eb, #4f46e5)',
                color: 'white',
                padding: '16px 24px',
                borderRadius: '8px',
                border: 'none',
                fontWeight: 'bold',
                fontSize: '18px',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.5 : 1
              }}
            >
              {loading ? '⏳ Buscando...' : '🔍 BUSCAR PROCESSOS'}
            </button>
          </div>
        </div>

        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          padding: '32px'
        }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📊</span> Resultados:
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <div style={{ backgroundColor: '#f0fdf4', padding: '16px', borderRadius: '8px' }}>
              <p style={{ color: '#166534', fontWeight: '600', margin: 0 }}>
                ✅ Novos: {stats.novos}
              </p>
            </div>
            <div style={{ backgroundColor: '#eff6ff', padding: '16px', borderRadius: '8px' }}>
              <p style={{ color: '#1e40af', fontWeight: '600', margin: 0 }}>
                🔁 Duplicados: {stats.duplicados}
              </p>
            </div>
            <div style={{ backgroundColor: '#fef2f2', padding: '16px', borderRadius: '8px' }}>
              <p style={{ color: '#991b1b', fontWeight: '600', margin: 0 }}>
                ❌ Inativos: {stats.inativos}
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <button style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              padding: '12px 16px',
              borderRadius: '8px',
              border: 'none',
              fontWeight: '600',
              cursor: 'pointer'
            }}>
              📋 Busca ({processosBusca.length})
            </button>
            <button style={{
              backgroundColor: '#eab308',
              color: 'white',
              padding: '12px 16px',
              borderRadius: '8px',
              border: 'none',
              fontWeight: '600',
              cursor: 'pointer'
            }}>
              ⭐ Interesse ({processosInteresse.length})
            </button>
            <button style={{
              backgroundColor: '#6b7280',
              color: 'white',
              padding: '12px 16px',
              borderRadius: '8px',
              border: 'none',
              fontWeight: '600',
              cursor: 'pointer'
            }}>
              🗑️ Descartados ({processosDescartados.length})
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '24px'
          }}>
            {processosBusca.map(p => (
              <ProcessoCard 
                key={p.numero} 
                processo={p} 
                onInteresse={marcarInteresse}
                onDescartar={marcarDescartado}
              />
            ))}
          </div>

          {processosBusca.length === 0 && (
            <div style={{ textAlign: 'center', padding: '48px 0', color: '#6b7280' }}>
              <p style={{ fontSize: '20px', margin: 0 }}>Nenhum processo nesta aba</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
