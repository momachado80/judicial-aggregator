'use client';
import { useState, useEffect } from 'react';

export default function DJESearch() {
  const [tiposSelecionados, setTiposSelecionados] = useState(['Inventário', 'Divórcio']);
  const [comarcasSelecionadas, setComarcasSelecionadas] = useState<string[]>([]);
  const [inputComarca, setInputComarca] = useState('');
  const [apenasImoveis, setApenasImoveis] = useState(true);
  const [apenasAtivos, setApenasAtivos] = useState(true);
  const [limitePdfs, setLimitePdfs] = useState(50);
  const [valorMin, setValorMin] = useState('');
  const [valorMax, setValorMax] = useState('');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');
  const [processos, setProcessos] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [interesseIds, setInteresseIds] = useState(new Set<string>());
  const [descartadosIds, setDescartadosIds] = useState(new Set<string>());
  const [abaAtiva, setAbaAtiva] = useState<'busca' | 'interesse' | 'descartados'>('busca');
  const [comarcasDisponiveis, setComarcasDisponiveis] = useState<string[]>([]);
  const [comarcasCarregando, setComarcasCarregando] = useState(true);
  const [ordenarPor, setOrdenarPor] = useState('relevancia_desc');

  // Paginação - 10 processos por página
  const [paginaBusca, setPaginaBusca] = useState(1);
  const [paginaInteresse, setPaginaInteresse] = useState(1);
  const [paginaDescartados, setPaginaDescartados] = useState(1);
  const PROCESSOS_POR_PAGINA = 10;

  // Carregar comarcas do backend
  useEffect(() => {
    const fallbackComarcas = [
      'São Paulo', 'Guarulhos', 'Campinas', 'Santos', 'São Bernardo do Campo',
      'Santo André', 'Osasco', 'Ribeirão Preto', 'Sorocaba', 'Mogi das Cruzes',
      'Piracicaba', 'Bauru', 'São José dos Campos', 'Jundiaí', 'Franca',
      'Presidente Prudente', 'Araraquara', 'Americana', 'Araçatuba', 'Suzano',
      'Limeira', 'Diadema', 'Taboão da Serra', 'Mauá', 'Carapicuíba',
      'Itaquaquecetuba', 'Barueri', 'Embu das Artes', 'Jacareí', 'Praia Grande',
      'Indaiatuba', 'Cotia', 'São Carlos', 'Marília', 'Taubaté'
    ];

    const carregarComarcas = async () => {
      try {
        const response = await fetch('/api/processes/comarcas');
        const data = await response.json();
        // Pegar apenas comarcas TJSP (DJE é só TJSP)
        if (data.TJSP && data.TJSP.length > 0) {
          setComarcasDisponiveis(data.TJSP);
        } else {
          setComarcasDisponiveis(fallbackComarcas);
        }
      } catch (error) {
        console.error('Erro ao carregar comarcas:', error);
        setComarcasDisponiveis(fallbackComarcas);
      } finally {
        setComarcasCarregando(false);
      }
    };

    carregarComarcas();
  }, []);

  const adicionarComarca = (comarca: string) => {
    const comarcaTrimmed = comarca.trim();
    if (comarcaTrimmed && !comarcasSelecionadas.includes(comarcaTrimmed)) {
      setComarcasSelecionadas([...comarcasSelecionadas, comarcaTrimmed]);
      setInputComarca('');
    }
  };

  const removerComarca = (comarca: string) => {
    setComarcasSelecionadas(comarcasSelecionadas.filter(c => c !== comarca));
  };

  const buscarProcessosDJE = async () => {
    setLoading(true);
    // Reset pagination on new search
    setPaginaBusca(1);
    setPaginaInteresse(1);
    setPaginaDescartados(1);
    try {
      const body: any = {
        tipos_processo: tiposSelecionados,
        apenas_imoveis: apenasImoveis,
        apenas_ativos: apenasAtivos
      };

      if (comarcasSelecionadas.length > 0) {
        body.comarcas = comarcasSelecionadas;
      }

      if (valorMin) {
        body.valor_min = Number(valorMin);
      }

      if (valorMax) {
        body.valor_max = Number(valorMax);
      }

      if (dataInicio) {
        body.data_inicio = dataInicio;
      }

      if (dataFim) {
        body.data_fim = dataFim;
      }

      // Adicionar ordenação
      body.ordenar_por = ordenarPor;

      const response = await fetch(
        `https://judicial-aggregator-production.up.railway.app/api/dje/buscar-cache-instantaneo`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        }
      );

      const data = await response.json();

      // DEBUG: Ver primeiros 2 processos
      console.log('🔍 PRIMEIROS 2 PROCESSOS:', JSON.stringify(data.processos?.slice(0, 2), null, 2));

      if (data.processos) {
        setProcessos(data.processos);
        setStats({
          total: data.total_processos,
          pdfsProcessados: data.pdfs_processados_sucesso,
          pdfsTotal: data.pdfs_disponiveis_total,
          estatisticas: data.estatisticas
        });
      } else {
        alert('Erro: ' + (data.detail || 'Resposta inválida'));
      }
    } catch (error) {
      console.error('Erro ao buscar:', error);
      alert('Erro ao buscar processos DJE');
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

  // Paginação - calcular quais processos mostrar
  const getTotalPaginas = (total: number) => Math.ceil(total / PROCESSOS_POR_PAGINA);

  const processosBuscaPaginados = processosBusca.slice(
    (paginaBusca - 1) * PROCESSOS_POR_PAGINA,
    paginaBusca * PROCESSOS_POR_PAGINA
  );

  const processosInteressePaginados = processosInteresse.slice(
    (paginaInteresse - 1) * PROCESSOS_POR_PAGINA,
    paginaInteresse * PROCESSOS_POR_PAGINA
  );

  const processosDescartadosPaginados = processosDescartados.slice(
    (paginaDescartados - 1) * PROCESSOS_POR_PAGINA,
    paginaDescartados * PROCESSOS_POR_PAGINA
  );

  const formatarValor = (valor: number | null) => {
    if (!valor) return 'Não informado';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  };

  const copiarNumeroProcesso = (numeroProcesso: string) => {
    navigator.clipboard.writeText(numeroProcesso);
    // Copia silenciosamente, sem popup
  };

  const gerarUrlTJSP = (numeroProcesso: string) => {
    // O TJSP não permite links diretos para processos específicos
    // Retorna a página de busca geral
    return `https://esaj.tjsp.jus.br/cpopg/open.do`;
  };

  // Componente de paginação
  const Paginacao = ({ paginaAtual, totalPaginas, onChange }: { paginaAtual: number, totalPaginas: number, onChange: (pagina: number) => void }) => {
    if (totalPaginas <= 1) return null;

    const paginas = [];
    for (let i = 1; i <= totalPaginas; i++) {
      paginas.push(i);
    }

    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: '8px',
        marginTop: '24px',
        flexWrap: 'wrap'
      }}>
        <button
          onClick={() => onChange(paginaAtual - 1)}
          disabled={paginaAtual === 1}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: '1px solid #d1d5db',
            backgroundColor: paginaAtual === 1 ? '#f3f4f6' : 'white',
            cursor: paginaAtual === 1 ? 'not-allowed' : 'pointer',
            fontWeight: '600',
            color: paginaAtual === 1 ? '#9ca3af' : '#374151'
          }}
        >
          ← Anterior
        </button>

        {paginas.map(num => (
          <button
            key={num}
            onClick={() => onChange(num)}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: paginaAtual === num ? '2px solid #3b82f6' : '1px solid #d1d5db',
              backgroundColor: paginaAtual === num ? '#3b82f6' : 'white',
              cursor: 'pointer',
              fontWeight: '600',
              color: paginaAtual === num ? 'white' : '#374151',
              minWidth: '40px'
            }}
          >
            {num}
          </button>
        ))}

        <button
          onClick={() => onChange(paginaAtual + 1)}
          disabled={paginaAtual === totalPaginas}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: '1px solid #d1d5db',
            backgroundColor: paginaAtual === totalPaginas ? '#f3f4f6' : 'white',
            cursor: paginaAtual === totalPaginas ? 'not-allowed' : 'pointer',
            fontWeight: '600',
            color: paginaAtual === totalPaginas ? '#9ca3af' : '#374151'
          }}
        >
          Próxima →
        </button>
      </div>
    );
  };

  const ProcessoDJECard = ({ processo }: { processo: any }) => (
    <div style={{
      backgroundColor: 'white',
      padding: '24px',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      border: processo.tem_imovel ? '2px solid #10b981' : '1px solid #e5e7eb'
    }}>
      <div style={{ marginBottom: '16px' }}>
        <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Número:</p>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{
            fontFamily: 'monospace',
            fontSize: '14px',
            fontWeight: '600',
            color: '#374151'
          }}>
            {processo.numero}
          </span>
          <button
            onClick={() => copiarNumeroProcesso(processo.numero)}
            style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '4px 12px',
              fontSize: '11px',
              cursor: 'pointer',
              fontWeight: '500'
            }}
            title="Copiar número e abrir TJSP"
          >
            📋 Copiar
          </button>
          <a
            href={gerarUrlTJSP(processo.numero)}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              backgroundColor: '#10b981',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '4px 12px',
              fontSize: '11px',
              cursor: 'pointer',
              fontWeight: '500',
              textDecoration: 'none'
            }}
            title="Abrir site do TJSP"
          >
            🔗 TJSP
          </a>
        </div>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '12px', color: '#6b7280' }}>Tipo:</p>
        <p style={{ fontWeight: '600', margin: 0 }}>{processo.tipo || processo.classe}</p>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <p style={{ fontSize: '12px', color: '#6b7280' }}>Comarca:</p>
        <p style={{ fontWeight: '600', color: '#7c3aed', margin: 0 }}>{processo.comarca}</p>
      </div>

      {processo.valor_causa && (
        <div style={{ marginBottom: '12px' }}>
          <p style={{ fontSize: '12px', color: '#6b7280' }}>Valor da Causa:</p>
          <p style={{ fontWeight: '600', color: '#059669', margin: 0 }}>
            {formatarValor(processo.valor_causa)}
          </p>
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '8px',
        marginTop: '16px'
      }}>
        {processo.tem_imovel && (
          <span style={{
            backgroundColor: '#dcfce7',
            color: '#166534',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            textAlign: 'center'
          }}>
            🏠 Imóvel
          </span>
        )}
        {processo.esta_ativo && (
          <span style={{
            backgroundColor: '#dbeafe',
            color: '#1e40af',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            textAlign: 'center'
          }}>
            ✅ Ativo
          </span>
        )}
      </div>

      {processo.relevancia && (
        <div style={{ marginTop: '12px' }}>
          <p style={{ fontSize: '12px', color: '#6b7280' }}>Relevância:</p>
          <div style={{
            backgroundColor: processo.relevancia === 'Altíssima' ? '#fee2e2' :
                           processo.relevancia === 'Alta' ? '#fef3c7' : '#f3f4f6',
            color: processo.relevancia === 'Altíssima' ? '#991b1b' :
                   processo.relevancia === 'Alta' ? '#92400e' : '#374151',
            padding: '8px',
            borderRadius: '6px',
            fontWeight: '600',
            fontSize: '14px',
            textAlign: 'center'
          }}>
            {processo.relevancia}
          </div>
        </div>
      )}

      {processo.partes && processo.partes.length > 0 && (
        <div style={{ marginTop: '12px' }}>
          <p style={{ fontSize: '12px', color: '#6b7280' }}>Partes:</p>
          <div style={{ fontSize: '13px' }}>
            {processo.partes.slice(0, 2).map((parte: string, i: number) => (
              <p key={i} style={{ margin: '4px 0', color: '#374151' }}>{parte}</p>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: '12px', fontSize: '11px', color: '#9ca3af' }}>
        Página DJE: {processo.pagina_dje}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '16px' }}>
        <button
          onClick={() => marcarInteresse(processo.numero)}
          style={{
            backgroundColor: '#10b981',
            color: 'white',
            padding: '12px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '14px'
          }}
        >
          ⭐ Interesse
        </button>
        <button
          onClick={() => marcarDescartado(processo.numero)}
          style={{
            backgroundColor: '#ef4444',
            color: 'white',
            padding: '12px',
            borderRadius: '8px',
            border: 'none',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '14px'
          }}
        >
          🗑️ Descartar
        </button>
      </div>
    </div>
  );

  return (
    <div>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '16px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        padding: '32px',
        marginBottom: '32px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '24px'
        }}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: 'bold',
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span>📄</span> Buscar no DJE (Diário de Justiça Eletrônico)
          </h2>
          <span style={{
            backgroundColor: '#dcfce7',
            color: '#166534',
            padding: '4px 12px',
            borderRadius: '9999px',
            fontSize: '12px',
            fontWeight: '600'
          }}>
            ✨ NOVO
          </span>
        </div>

        <div style={{
          backgroundColor: '#fef3c7',
          padding: '16px',
          borderRadius: '8px',
          marginBottom: '24px'
        }}>
          <p style={{ fontSize: '14px', color: '#92400e', margin: 0 }}>
            💡 <strong>Precisão Absoluta:</strong> Sistema DJE busca processos diretamente nas publicações oficiais do TJSP com detecção automática de imóveis (30+ palavras-chave) e filtro de processos ativos.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>
              Tipos de Processo *
            </label>
            <div style={{ display: 'flex', gap: '16px' }}>
              {['Inventário', 'Divórcio'].map(t => (
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
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '4px' }}>
              Comarcas (opcional)
            </label>
            <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>
              {comarcasCarregando ? (
                'Carregando comarcas...'
              ) : (
                `${comarcasDisponiveis.length} comarcas disponíveis (TJSP)`
              )}
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={inputComarca}
                onChange={(e) => setInputComarca(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && adicionarComarca(inputComarca)}
                placeholder="Digite: São Paulo, Piracicaba, Campinas..."
                style={{
                  flex: 1,
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  fontSize: '14px'
                }}
                list="comarcas-dje-list"
                disabled={comarcasCarregando}
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
                disabled={comarcasCarregando}
              >
                + Adicionar
              </button>
            </div>
            <datalist id="comarcas-dje-list">
              {comarcasDisponiveis.map(c => (
                <option key={c} value={c} />
              ))}
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
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>
                📅 Data Início (DJE)
              </label>
              <input
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                min="2021-01-01"
                max={new Date().toISOString().split('T')[0]}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>
                📅 Data Fim (DJE)
              </label>
              <input
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                min="2021-01-01"
                max={new Date().toISOString().split('T')[0]}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px'
                }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>
                Valor Mínimo (R$)
              </label>
              <input
                type="number"
                value={valorMin}
                onChange={(e) => setValorMin(e.target.value)}
                placeholder="Ex: 100000"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>
                Valor Máximo (R$)
              </label>
              <input
                type="number"
                value={valorMax}
                onChange={(e) => setValorMax(e.target.value)}
                placeholder="Ex: 5000000"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px'
                }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '16px',
              backgroundColor: apenasImoveis ? '#dcfce7' : '#f3f4f6',
              borderRadius: '8px',
              cursor: 'pointer',
              border: apenasImoveis ? '2px solid #10b981' : '2px solid #e5e7eb'
            }}>
              <input
                type="checkbox"
                checked={apenasImoveis}
                onChange={(e) => setApenasImoveis(e.target.checked)}
                style={{ width: '20px', height: '20px' }}
              />
              <div>
                <p style={{ fontWeight: '600', margin: 0 }}>🏠 Apenas com Imóveis</p>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                  Detecta 30+ palavras-chave
                </p>
              </div>
            </label>

            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '16px',
              backgroundColor: apenasAtivos ? '#dbeafe' : '#f3f4f6',
              borderRadius: '8px',
              cursor: 'pointer',
              border: apenasAtivos ? '2px solid #3b82f6' : '2px solid #e5e7eb'
            }}>
              <input
                type="checkbox"
                checked={apenasAtivos}
                onChange={(e) => setApenasAtivos(e.target.checked)}
                style={{ width: '20px', height: '20px' }}
              />
              <div>
                <p style={{ fontWeight: '600', margin: 0 }}>✅ Apenas Ativos</p>
                <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                  Exclui extintos/arquivados
                </p>
              </div>
            </label>
          </div>

          <div>
            <label style={{ display: 'block', fontWeight: '600', marginBottom: '8px' }}>
              Ordenar resultados por:
            </label>
            <select
              value={ordenarPor}
              onChange={(e) => setOrdenarPor(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '14px',
                backgroundColor: 'white'
              }}
            >
              <option value="relevancia_desc">🔥 Alta relevância primeiro</option>
              <option value="relevancia_asc">📉 Baixa relevância primeiro</option>
              <option value="data_desc">📅 Mais recentes primeiro</option>
              <option value="data_asc">📅 Mais antigos primeiro</option>
              <option value="valor_desc">💰 Maior valor primeiro</option>
              <option value="valor_asc">💰 Menor valor primeiro</option>
            </select>
          </div>

          <button
            onClick={buscarProcessosDJE}
            disabled={loading || tiposSelecionados.length === 0}
            style={{
              width: '100%',
              background: loading ? '#9ca3af' : 'linear-gradient(to right, #10b981, #059669)',
              color: 'white',
              padding: '16px 24px',
              borderRadius: '8px',
              border: 'none',
              fontWeight: 'bold',
              fontSize: '18px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? '⏳ Processando PDFs...' : '📄 BUSCAR NO DJE'}
          </button>
        </div>
      </div>

      {stats && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          padding: '32px',
          marginBottom: '32px'
        }}>
          <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '16px' }}>
            📊 Estatísticas
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <div style={{ backgroundColor: '#dcfce7', padding: '16px', borderRadius: '8px' }}>
              <p style={{ fontSize: '12px', color: '#166534', marginBottom: '4px' }}>Total Encontrado</p>
              <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#166534', margin: 0 }}>
                {stats.total}
              </p>
            </div>
            <div style={{ backgroundColor: '#dbeafe', padding: '16px', borderRadius: '8px' }}>
              <p style={{ fontSize: '12px', color: '#1e40af', marginBottom: '4px' }}>PDFs Processados</p>
              <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#1e40af', margin: 0 }}>
                {stats.pdfsProcessados}
              </p>
            </div>
            <div style={{ backgroundColor: '#fef3c7', padding: '16px', borderRadius: '8px' }}>
              <p style={{ fontSize: '12px', color: '#92400e', marginBottom: '4px' }}>PDFs Disponíveis</p>
              <p style={{ fontSize: '28px', fontWeight: 'bold', color: '#92400e', margin: 0 }}>
                {stats.pdfsTotal}
              </p>
            </div>
          </div>

          {stats.estatisticas && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {stats.estatisticas.por_tipo && Object.keys(stats.estatisticas.por_tipo).length > 0 && (
                <div style={{ padding: '16px', backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
                  <p style={{ fontWeight: '600', marginBottom: '8px' }}>Por Tipo:</p>
                  {Object.entries(stats.estatisticas.por_tipo).map(([tipo, count]) => (
                    <p key={tipo} style={{ fontSize: '14px', margin: '4px 0' }}>
                      {tipo}: <strong>{count as number}</strong>
                    </p>
                  ))}
                </div>
              )}
              {stats.estatisticas.por_relevancia && Object.keys(stats.estatisticas.por_relevancia).length > 0 && (
                <div style={{ padding: '16px', backgroundColor: '#f3f4f6', borderRadius: '8px' }}>
                  <p style={{ fontWeight: '600', marginBottom: '8px' }}>Por Relevância:</p>
                  {Object.entries(stats.estatisticas.por_relevancia).map(([rel, count]) => (
                    <p key={rel} style={{ fontSize: '14px', margin: '4px 0' }}>
                      {rel}: <strong>{count as number}</strong>
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {processos.length > 0 && (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '16px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          padding: '32px'
        }}>
          {/* Abas de Navegação */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <button
              onClick={() => setAbaAtiva('busca')}
              style={{
                backgroundColor: abaAtiva === 'busca' ? '#3b82f6' : 'white',
                color: abaAtiva === 'busca' ? 'white' : '#6b7280',
                padding: '12px 16px',
                borderRadius: '8px',
                border: abaAtiva === 'busca' ? 'none' : '2px solid #e5e7eb',
                fontWeight: '600',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              📋 Busca ({processosBusca.length})
            </button>
            <button
              onClick={() => setAbaAtiva('interesse')}
              style={{
                backgroundColor: abaAtiva === 'interesse' ? '#eab308' : 'white',
                color: abaAtiva === 'interesse' ? 'white' : '#6b7280',
                padding: '12px 16px',
                borderRadius: '8px',
                border: abaAtiva === 'interesse' ? 'none' : '2px solid #e5e7eb',
                fontWeight: '600',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              ⭐ Interesse ({processosInteresse.length})
            </button>
            <button
              onClick={() => setAbaAtiva('descartados')}
              style={{
                backgroundColor: abaAtiva === 'descartados' ? '#6b7280' : 'white',
                color: abaAtiva === 'descartados' ? 'white' : '#6b7280',
                padding: '12px 16px',
                borderRadius: '8px',
                border: abaAtiva === 'descartados' ? 'none' : '2px solid #e5e7eb',
                fontWeight: '600',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              🗑️ Descartados ({processosDescartados.length})
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
            gap: '24px'
          }}>
            {abaAtiva === 'busca' && processosBuscaPaginados.map((p, idx) => (
              <ProcessoDJECard key={idx} processo={p} />
            ))}
            {abaAtiva === 'interesse' && processosInteressePaginados.map((p, idx) => (
              <ProcessoDJECard key={idx} processo={p} />
            ))}
            {abaAtiva === 'descartados' && processosDescartadosPaginados.map((p, idx) => (
              <ProcessoDJECard key={idx} processo={p} />
            ))}
          </div>

          {/* Paginação */}
          {abaAtiva === 'busca' && processosBusca.length > 0 && (
            <div>
              <p style={{ textAlign: 'center', color: '#6b7280', marginTop: '16px', fontSize: '14px' }}>
                Mostrando {((paginaBusca - 1) * PROCESSOS_POR_PAGINA) + 1} - {Math.min(paginaBusca * PROCESSOS_POR_PAGINA, processosBusca.length)} de {processosBusca.length} processos
              </p>
              <Paginacao
                paginaAtual={paginaBusca}
                totalPaginas={getTotalPaginas(processosBusca.length)}
                onChange={setPaginaBusca}
              />
            </div>
          )}

          {abaAtiva === 'interesse' && processosInteresse.length > 0 && (
            <div>
              <p style={{ textAlign: 'center', color: '#6b7280', marginTop: '16px', fontSize: '14px' }}>
                Mostrando {((paginaInteresse - 1) * PROCESSOS_POR_PAGINA) + 1} - {Math.min(paginaInteresse * PROCESSOS_POR_PAGINA, processosInteresse.length)} de {processosInteresse.length} processos
              </p>
              <Paginacao
                paginaAtual={paginaInteresse}
                totalPaginas={getTotalPaginas(processosInteresse.length)}
                onChange={setPaginaInteresse}
              />
            </div>
          )}

          {abaAtiva === 'descartados' && processosDescartados.length > 0 && (
            <div>
              <p style={{ textAlign: 'center', color: '#6b7280', marginTop: '16px', fontSize: '14px' }}>
                Mostrando {((paginaDescartados - 1) * PROCESSOS_POR_PAGINA) + 1} - {Math.min(paginaDescartados * PROCESSOS_POR_PAGINA, processosDescartados.length)} de {processosDescartados.length} processos
              </p>
              <Paginacao
                paginaAtual={paginaDescartados}
                totalPaginas={getTotalPaginas(processosDescartados.length)}
                onChange={setPaginaDescartados}
              />
            </div>
          )}

          {abaAtiva === 'busca' && processosBusca.length === 0 && (
            <div style={{ textAlign: 'center', padding: '48px 0', color: '#6b7280' }}>
              <p style={{ fontSize: '18px', margin: 0 }}>Nenhum processo nesta aba</p>
            </div>
          )}
          {abaAtiva === 'interesse' && processosInteresse.length === 0 && (
            <div style={{ textAlign: 'center', padding: '48px 0', color: '#6b7280' }}>
              <p style={{ fontSize: '18px', margin: 0 }}>Nenhum processo marcado como interesse</p>
            </div>
          )}
          {abaAtiva === 'descartados' && processosDescartados.length === 0 && (
            <div style={{ textAlign: 'center', padding: '48px 0', color: '#6b7280' }}>
              <p style={{ fontSize: '18px', margin: 0 }}>Nenhum processo descartado</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
