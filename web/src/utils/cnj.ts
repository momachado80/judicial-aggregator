export function extrairComarcaEData(numeroCNJ: string, tribunal: string) {
  const limpo = numeroCNJ.replace(/[^\d]/g, '')
  
  if (limpo.length < 20) {
    return { comarca: 'Não informado', ano: null }
  }
  
  const ano = parseInt(limpo.substring(9, 13))
  const codigo = limpo.substring(limpo.length - 4)
  
  const comarcasTJSP: Record<string, string> = {
    '0026': 'São Paulo',
    '0624': 'Campinas', 
    '0575': 'Santos',
    '0114': 'Guarulhos',
    '0477': 'Ribeirão Preto',
    '0482': 'Santo André',
    '0405': 'Osasco',
    '0506': 'São Bernardo do Campo',
    '0505': 'São José dos Campos',
    '0533': 'Santa Rosa de Viterbo'
  }
  
  const comarcasTJBA: Record<string, string> = {
    '0001': 'Salvador',
    '0005': 'Feira de Santana',
    '0007': 'Itabuna'
  }
  
  const mapa = tribunal === 'TJSP' ? comarcasTJSP : comarcasTJBA
  const comarca = mapa[codigo] || 'Comarca ' + codigo
  
  return { comarca, ano }
}

