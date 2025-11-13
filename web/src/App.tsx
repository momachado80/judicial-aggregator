import { useState } from 'react'
import { SearchForm } from './components/SearchForm'
import { ProcessCard } from './components/ProcessCard'

interface SearchParams {
  tribunal: 'TJSP' | 'TJBA'
  tipo_processo: string
  valor_causa_min?: number
  valor_causa_max?: number
  limit: number
}

interface Process {
  id: number
  numero_cnj: string
  tribunal: string
  tipo_processo: string
  comarca?: string
  valor_causa?: number
  novo: boolean
  status: string
}

function App() {
  const [processes, setProcesses] = useState<Process[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<any>(null)

  const handleSearch = async (params: SearchParams) => {
    setLoading(true)
    try {
      const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })
      const data = await response.json()
      setProcesses(data.processos)
      setStats(data.stats)
    } catch (error) {
      console.error('Erro:', error)
      alert('Erro ao buscar processos')
    }
    setLoading(false)
  }

  const handleSelect = async (id: number) => {
    try {
      await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'interesse' })
      })
      alert('Processo marcado como interesse!')
    } catch (error) {
      console.error('Erro:', error)
    }
  }

  const handleDiscard = async (id: number) => {
    try {
      await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'descartado' })
      })
      setProcesses(processes.filter(p => p.id !== id))
      alert('Processo descartado!')
    } catch (error) {
      console.error('Erro:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-800 mb-6">
          ⚖️ Judicial Aggregator
        </h1>

        <SearchForm onSearch={handleSearch} loading={loading} />

        {stats && (
          <div className="bg-white p-4 rounded-lg shadow mb-6">
            <h3 className="font-bold mb-2">Resultados da Busca:</h3>
            <div className="flex gap-4 text-sm">
              <span>✅ Novos: {stats.novos}</span>
              <span>🔄 Duplicados: {stats.duplicados}</span>
              <span>❌ Inativos: {stats.inativos}</span>
            </div>
          </div>
        )}

        <div className="space-y-4">
          {processes.map(process => (
            <ProcessCard
              key={process.id}
              process={process}
              onSelect={handleSelect}
              onDiscard={handleDiscard}
            />
          ))}
        </div>

        {processes.length === 0 && !loading && (
          <div className="text-center text-gray-500 py-12">
            Use o formulário acima para buscar processos
          </div>
        )}
      </div>
    </div>
  )
}

export default App
