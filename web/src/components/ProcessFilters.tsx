import { useState } from 'react'

interface Filters {
  tribunal?: string
  comarca?: string
  status?: string
  relevancia?: string
}

interface Props {
  onFilterChange: (filters: Filters) => void
}

export function ProcessFilters({ onFilterChange }: Props) {
  const [filters, setFilters] = useState<Filters>({})

  const handleChange = (key: keyof Filters, value: string) => {
    const newFilters = { ...filters, [key]: value || undefined }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm mb-6">
      <h3 className="text-lg font-semibold mb-4">Filtros Avançados</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Tribunal */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tribunal
          </label>
          <select
            className="w-full p-2 border rounded"
            onChange={(e) => handleChange('tribunal', e.target.value)}
          >
            <option value="">Todos</option>
            <option value="TJSP">TJSP</option>
            <option value="TJBA">TJBA</option>
          </select>
        </div>

        {/* Comarca */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Comarca
          </label>
          <input
            type="text"
            placeholder="Ex: São Paulo"
            className="w-full p-2 border rounded"
            onChange={(e) => handleChange('comarca', e.target.value)}
          />
        </div>

        {/* Status */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Status
          </label>
          <select
            className="w-full p-2 border rounded"
            onChange={(e) => handleChange('status', e.target.value)}
          >
            <option value="">Todos</option>
            <option value="pendente">Pendente</option>
            <option value="interesse">Interesse</option>
            <option value="descartado">Descartado</option>
          </select>
        </div>

        {/* NOVO: Relevância */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            🔥 Relevância
          </label>
          <select
            className="w-full p-2 border rounded font-semibold"
            onChange={(e) => handleChange('relevancia', e.target.value)}
          >
            <option value="">Todas</option>
            <option value="Altíssima">🔥 Altíssima</option>
            <option value="Alta">⭐ Alta</option>
            <option value="Média">📊 Média</option>
          </select>
        </div>
      </div>
    </div>
  )
}
