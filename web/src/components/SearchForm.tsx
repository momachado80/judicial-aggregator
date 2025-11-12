import { useState } from 'react'

interface SearchParams {
  tribunal: 'TJSP' | 'TJBA'
  tipo_processo: 'Inventário' | 'Divórcio Litigioso' | 'Divórcio Consensual'
  valor_causa_min?: number
  valor_causa_max?: number
  limit: number
}

interface Props {
  onSearch: (params: SearchParams) => void
  loading: boolean
}

export function SearchForm({ onSearch, loading }: Props) {
  const [params, setParams] = useState<SearchParams>({
    tribunal: 'TJSP',
    tipo_processo: 'Inventário',
    limit: 500
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(params)
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h2 className="text-2xl font-bold mb-4">Buscar Processos</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block mb-2">Tribunal</label>
            <select className="w-full p-3 border rounded" value={params.tribunal} onChange={(e) => setParams({...params, tribunal: e.target.value as any})}>
              <option value="TJSP">TJSP</option>
              <option value="TJBA">TJBA</option>
            </select>
          </div>
          
          <div>
            <label className="block mb-2">Tipo</label>
            <select className="w-full p-3 border rounded" value={params.tipo_processo} onChange={(e) => setParams({...params, tipo_processo: e.target.value as any})}>
              <option value="Inventário">Inventário</option>
              <option value="Divórcio Litigioso">Divórcio Litigioso</option>
            </select>
          </div>
          
          <div>
            <label className="block mb-2">Valor Mínimo</label>
            <input type="number" className="w-full p-3 border rounded" placeholder="100000" onChange={(e) => setParams({...params, valor_causa_min: e.target.value ? Number(e.target.value) : undefined})} />
          </div>
          
          <div>
            <label className="block mb-2">Quantidade</label>
            <select className="w-full p-3 border rounded" value={params.limit} onChange={(e) => setParams({...params, limit: Number(e.target.value)})}>
              <option value="50">50</option>
              <option value="500">500</option>
            </select>
          </div>
        </div>

        <button type="submit" disabled={loading} className="w-full bg-blue-600 text-white py-3 rounded hover:bg-blue-700">
          {loading ? 'Buscando...' : 'BUSCAR PROCESSOS'}
        </button>
      </form>
    </div>
  )
}
