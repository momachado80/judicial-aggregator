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

interface Props {
  process: Process
  onSelect: (id: number) => void
  onDiscard: (id: number) => void
}

export function ProcessCard({ process, onSelect, onDiscard }: Props) {
  const formatCurrency = (value?: number) => {
    if (!value) return 'Não informado'
    return new Intl.NumberFormat('pt-BR', { 
      style: 'currency', 
      currency: 'BRL' 
    }).format(value)
  }

  return (
    <div className={`border rounded-lg p-4 mb-3 ${process.novo ? 'bg-blue-50 border-blue-300' : 'bg-white'}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {process.novo && (
              <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded font-bold">
                NOVO
              </span>
            )}
            {process.valor_causa && process.valor_causa > 1000000 && (
              <span className="bg-yellow-500 text-white text-xs px-2 py-1 rounded font-bold">
                ALTO VALOR
              </span>
            )}
          </div>
          
          <h3 className="font-mono text-sm font-bold text-gray-800 mb-1">
            {process.numero_cnj}
          </h3>
          
          <div className="text-sm text-gray-600 space-y-1">
            <p><strong>Tipo:</strong> {process.tipo_processo}</p>
            <p><strong>Tribunal:</strong> {process.tribunal}</p>
            {process.comarca && <p><strong>Comarca:</strong> {process.comarca}</p>}
            <p><strong>Valor:</strong> {formatCurrency(process.valor_causa)}</p>
          </div>
        </div>
      </div>

      <div className="flex gap-2 mt-4">
        <button
          onClick={() => onSelect(process.id)}
          className="flex-1 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700"
        >
          Selecionar
        </button>
        <button
          onClick={() => onDiscard(process.id)}
          className="flex-1 bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700"
        >
          Descartar
        </button>
        
          href={`https://judicial-aggregator-production.up.railway.app/processes/${process.id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700"
        >
          Ver
        </a>
      </div>
    </div>
  )
}
