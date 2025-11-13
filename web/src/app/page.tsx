'use client'
import { useState } from 'react'
import { SearchForm } from '../components/SearchForm'
import { ProcessCard } from '../components/ProcessCard'

export default function Home() {
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
      alert('Erro')
    }
    setLoading(false)
  }

  const handleSelect = async (id: number) => {
    await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'interesse' })
    })
    alert('Selecionado!')
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
        <h1 className="text-4xl font-bold mb-6">⚖️ Judicial Aggregator</h1>
        <SearchForm onSearch={handleSearch} loading={loading} />
        {stats && (
          <div className="bg-white p-4 rounded mb-6">
            <div className="flex gap-4">
              <span>✅ Novos: {stats.novos}</span>
              <span>🔄 Duplicados: {stats.duplicados}</span>
              <span>❌ Inativos: {stats.inativos}</span>
            </div>
          </div>
        )}
        {!searched && (
          <div className="text-center py-20 bg-white rounded">
            <p>👆 Use o formulário para buscar</p>
          </div>
        )}
        {loading && <div className="text-center py-20">🔄 Buscando...</div>}
        <div className="space-y-4">
          {processes.map((p: any) => (
            <ProcessCard key={p.id} process={p} onSelect={handleSelect} onDiscard={handleDiscard} />
          ))}
        </div>
      </div>
    </div>
  )
}
