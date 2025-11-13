interface Props {
  process: any
  onSelect: (id: number) => void
  onDiscard: (id: number) => void
}

export function ProcessCard({ process, onSelect, onDiscard }: Props) {
  const formatCurrency = (value?: number) => {
    if (!value) return 'Não informado'
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
  }

  return (
    <div className={process.novo ? 'bg-blue-50 border-2 border-blue-300 rounded-lg p-4 mb-3' : 'bg-white border rounded-lg p-4 mb-3'}>
      <div className="flex items-center gap-2 mb-2">
        {process.novo && <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded font-bold">NOVO</span>}
        {process.valor_causa > 1000000 && <span className="bg-yellow-500 text-white text-xs px-2 py-1 rounded font-bold">ALTO VALOR</span>}
      </div>
      
      <h3 className="font-mono text-sm font-bold mb-2">{process.numero_cnj}</h3>
      
      <div className="text-sm text-gray-600 space-y-1 mb-4">
        <p><strong>Tipo:</strong> {process.tipo_processo}</p>
        <p><strong>Tribunal:</strong> {process.tribunal}</p>
        <p><strong>Valor:</strong> {formatCurrency(process.valor_causa)}</p>
      </div>

      <div className="flex gap-2">
        <button onClick={() => onSelect(process.id)} className="flex-1 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700">
          Selecionar
        </button>
        <button onClick={() => onDiscard(process.id)} className="flex-1 bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700">
          Descartar
        </button>
      </div>
    </div>
  )
}
