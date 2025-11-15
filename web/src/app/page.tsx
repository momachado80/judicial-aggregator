'use client';
import { useState } from 'react';

const TJSP_COMARCAS = [
  "Americana", "Araçatuba", "Araraquara", "Bauru", "Campinas", "Franca",
  "Guarulhos", "Itaquaquecetuba", "Jundiaí", "Limeira", "Marília",
  "Mogi das Cruzes", "Osasco", "Piracicaba", "Presidente Prudente",
  "Ribeirão Preto", "Santo André", "Santos", "São Bernardo do Campo",
  "São Caetano do Sul", "São José do Rio Preto", "São José dos Campos",
  "São Paulo", "Sorocaba", "Suzano", "Taboão da Serra", "Taubaté"
];

const TJBA_COMARCAS = [
  "Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari",
  "Itabuna", "Juazeiro", "Lauro de Freitas", "Ilhéus", "Jequié",
  "Teixeira de Freitas", "Alagoinhas", "Barreiras", "Paulo Afonso"
];

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
  const [interesseIds, setInteresseIds] = useState(new Set());
  const [descartadosIds, setDescartadosIds] = useState(new Set());

  const comarcasDisponiveis = tribunaisSelecionados.includes('TJSP') 
    ? TJSP_COMARCAS 
    : TJBA_COMARCAS;

  const adicionarComarca = (comarca) => {
    if (comarca && !comarcasSelecionadas.includes(comarca)) {
      setComarcasSelecionadas([...comarcasSelecionadas, comarca]);
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
      
      if (comarcasSelecionadas.length > 0) {
        todosProcessos = todosProcessos.filter(p =>
          comarcasSelecionadas.some(c => p.comarca?.toLowerCase().includes(c.toLowerCase()))
        );
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
    // Formato: 20240913215252 -> 13/09/2024
    const ano = data.substring(0, 4);
    const mes = data.substring(4, 6);
    const dia = data.substring(6, 8);
    return `${dia}/${mes}/${ano}`;
  };

  const ProcessoCard = ({ processo, onInteresse, onDescartar }) => (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-600">Número:</p>
          <a 
            href={processo.url_tjsp} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 font-mono text-sm font-semibold hover:underline"
          >
            {processo.numero}
          </a>
        </div>
        <div>
          <p className="text-sm text-gray-600">Tribunal:</p>
          <p className="font-semibold">{processo.tribunal}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-600">Tipo:</p>
          <p className="font-semibold">{processo.tipo}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Comarca:</p>
          <p className="font-semibold text-purple-700">{processo.comarca}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-600">Valor da Causa:</p>
          <p className="font-semibold text-green-700">{formatarValor(processo.valor_causa)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Data Ajuizamento:</p>
          <p className="font-semibold">{formatarData(processo.data_ajuizamento)}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mt-4">
        <button
          onClick={() => onInteresse(processo.numero)}
          className="bg-green-500 hover:bg-green-600 text-white py-3 px-4 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
        >
          <span>⭐</span> Interesse
        </button>
        <button
          onClick={() => onDescartar(processo.numero)}
          className="bg-red-500 hover:bg-red-600 text-white py-3 px-4 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
        >
          <span>🗑️</span> Descartar
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <nav className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 shadow-lg">
        <div className="container mx-auto">
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <span>⚖️</span> Judicial Aggregator
          </h1>
        </div>
      </nav>

      <div className="container mx-auto p-6">
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <span>🔍</span> Buscar Processos Ativos
          </h2>

          <div className="space-y-6">
            <div>
              <label className="block font-semibold mb-2">Tribunais *</label>
              <div className="flex gap-4">
                {['TJSP', 'TJBA'].map(t => (
                  <label key={t} className="flex items-center gap-2 cursor-pointer">
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
                      className="w-4 h-4"
                    />
                    <span>{t}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block font-semibold mb-2">Tipos *</label>
              <div className="flex gap-4">
                {['Inventário', 'Divórcio Litigioso', 'Divórcio Consensual'].map(t => (
                  <label key={t} className="flex items-center gap-2 cursor-pointer">
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
                      className="w-4 h-4"
                    />
                    <span>{t}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block font-semibold mb-2">
                Comarcas - {TJSP_COMARCAS.length} SP + {TJBA_COMARCAS.length} BA = {TJSP_COMARCAS.length + TJBA_COMARCAS.length} total
              </label>
              <input
                type="text"
                value={inputComarca}
                onChange={(e) => setInputComarca(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && adicionarComarca(inputComarca)}
                placeholder="Digite: Piracicaba, Americana, Salvador..."
                className="w-full p-3 border rounded-lg"
                list="comarcas-list"
              />
              <datalist id="comarcas-list">
                {comarcasDisponiveis.map(c => <option key={c} value={c} />)}
              </datalist>
              
              <div className="flex flex-wrap gap-2 mt-3">
                {comarcasSelecionadas.map(c => (
                  <span key={c} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full flex items-center gap-2">
                    {c}
                    <button onClick={() => removerComarca(c)} className="text-red-600 font-bold">×</button>
                  </span>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className="block font-semibold mb-2">Quantidade *</label>
                <select value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))} className="w-full p-3 border rounded-lg">
                  {[50, 100, 200, 500, 1000].map(q => <option key={q} value={q}>{q}</option>)}
                </select>
              </div>

              <div>
                <label className="block font-semibold mb-2">Ano</label>
                <select value={ano} onChange={(e) => setAno(e.target.value)} className="w-full p-3 border rounded-lg">
                  <option>Todos</option>
                  {anos.map(a => <option key={a}>{a}</option>)}
                </select>
              </div>

              <div>
                <label className="block font-semibold mb-2">Valor Mín (R$)</label>
                <input
                  type="number"
                  value={valorMin}
                  onChange={(e) => setValorMin(e.target.value)}
                  className="w-full p-3 border rounded-lg"
                />
              </div>

              <div>
                <label className="block font-semibold mb-2">Valor Máx (R$)</label>
                <input
                  type="number"
                  value={valorMax}
                  onChange={(e) => setValorMax(e.target.value)}
                  className="w-full p-3 border rounded-lg"
                />
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-sm text-blue-800">
                ℹ️ Apenas processos ATIVOS (exclui extintos, suspensos, arquivados)
              </p>
            </div>

            <button
              onClick={buscarProcessos}
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white py-4 px-6 rounded-lg font-bold text-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? '⏳ Buscando...' : '🔍 BUSCAR PROCESSOS'}
            </button>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <span>📊</span> Resultados:
          </h2>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-green-800 font-semibold flex items-center gap-2">
                <span>✅</span> Novos: {stats.novos}
              </p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-blue-800 font-semibold flex items-center gap-2">
                <span>🔁</span> Duplicados: {stats.duplicados}
              </p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <p className="text-red-800 font-semibold flex items-center gap-2">
                <span>❌</span> Inativos: {stats.inativos}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <button 
              onClick={() => {}} 
              className="bg-blue-500 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-600 transition-colors"
            >
              📋 Busca ({processosBusca.length})
            </button>
            <button 
              onClick={() => {}} 
              className="bg-yellow-500 text-white py-3 px-4 rounded-lg font-semibold hover:bg-yellow-600 transition-colors"
            >
              ⭐ Interesse ({processosInteresse.length})
            </button>
            <button 
              onClick={() => {}} 
              className="bg-gray-500 text-white py-3 px-4 rounded-lg font-semibold hover:bg-gray-600 transition-colors"
            >
              🗑️ Descartados ({processosDescartados.length})
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
            <div className="text-center py-12 text-gray-500">
              <p className="text-xl">Nenhum processo nesta aba</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
