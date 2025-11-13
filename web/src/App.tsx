import { useState } from 'react'
import { SearchForm } from './components/SearchForm'
import { ProcessCard } from './components/ProcessCard'

function App() {
  const [processes, setProcesses] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<any>(null)
  const [searched, setSearched] = useState(false)

  const handleSearch = async (params: any) => {
    setLoading(true)
    setSearched(true)
    try {
      const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })
      const data = await response.json()
      setProcesses(data.processos || [])
      setStats(data.stats)
    } catch (error) {
      alert('Erro ao buscar processos')
    }
    setLoading(false)
  }

  const handleSelect = async (id: number) => {
    await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'interesse' })
    })
    alert('Marcado como interesse!')
  }

  const handleDiscard = async (id: number) => {
    await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'descartado' })
    })
    setProcesses(processes.filter(p => p.id !== id))
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-6">⚖️ Judicial Aggregator</h1>
        
        <SearchForm onSearch={handleSearch} loading={loading} />

        {stats && (
          <div className="bg-white p-4 rounded-lg shadow mb-6">
            <h3 className="font-bold mb-2">Resultados:</h3>
            <div className="flex gap-4 text-sm">
              <span className="bg-green-100 px-3 py-1 rounded">✅ Novos: {stats.novos}</span>
              <span className="bg-blue-100 px-3 py-1 rounded">🔄 Já existiam: {stats.duplicados}</span>
              <span className="bg-red-100 px-3 py-1 rounded">❌ Inativos: {stats.inativos}</span>
            </div>
          </div>
        )}

        {!searched && (
          <div className="text-center text-gray-500 py-20 bg-white rounded-lg shadow">
            <p className="text-xl mb-2">👆 Use o formulário acima para buscar processos</p>
            <p className="text-sm">Filtre por tribunal, tipo, valor e quantidade</p>
          </div>
        )}

        {loading && (
          <div className="text-center py-20">
            <div className="text-4xl mb-4">🔄</div>
            <p className="text-xl text-gray-600">Buscando processos...</p>
          </div>
        )}

        <div className="space-y-4">
          {processes.map((p: any) => (
            <ProcessCard key={p.id} process={p} onSelect={handleSelect} onDiscard={handleDiscard} />
          ))}
        </div>

        {searched && processes.length === 0 && !loading && (
          <div className="text-center text-gray-500 py-12 bg-white rounded-lg">
            Nenhum processo encontrado com esses filtros
          </div>
        )}
      </div>
    </div>
  )
}

export default App
