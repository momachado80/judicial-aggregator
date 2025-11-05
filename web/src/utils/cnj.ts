export function extrairComarcaEData(numeroCNJ: string, tribunal: string) {
  const limpo = numeroCNJ.replace(/[^\d]/g, '')
  
  if (limpo.length < 20) {
    return { comarca: 'Não informado', data: null }
  }
  
  const ano = parseInt(limpo.substring(9, 13))
  const codigo = limpo.substring(limpo.length - 4)
  
  // TODAS as principais comarcas TJSP
  const comarcasTJSP: Record<string, string> = {
    '0026': 'São Paulo', '0624': 'Campinas', '0575': 'Santos', '0114': 'Guarulhos',
    '0477': 'Ribeirão Preto', '0482': 'Santo André', '0405': 'Osasco', '0506': 'São Bernardo do Campo',
    '0505': 'São José dos Campos', '0533': 'Santa Rosa de Viterbo', '0152': 'Bauru',
    '0408': 'Piracicaba', '0602': 'Sorocaba', '0063': 'Barretos', '0037': 'Araraquara',
    '0047': 'Assis', '0087': 'Bragança Paulista', '0086': 'Botucatu', '0109': 'Campinas',
    '0290': 'Jaú', '0307': 'Limeira', '0330': 'Marília', '0347': 'Mogi das Cruzes',
    '0349': 'Mogi Mirim', '0394': 'Ourinhos', '0437': 'Piracicaba', '0472': 'Presidente Prudente',
    '0491': 'Ribeirão Preto', '0546': 'Santos', '0548': 'São Bernardo do Campo', '0584': 'Sorocaba',
    '0607': 'Taubaté', '0644': 'Votuporanga', '0018': 'Americana', '0048': 'Atibaia',
    '0239': 'Indaiatuba', '0276': 'Itu', '0297': 'Jundiaí', '0632': 'Valinhos', '0639': 'Vinhedo'
  }
  
  // TODAS as principais comarcas TJBA
  const comarcasTJBA: Record<string, string> = {
    '0001': 'Salvador', '0002': 'Alagoinhas', '0003': 'Barreiras', '0004': 'Camaçari',
    '0005': 'Feira de Santana', '0006': 'Ilhéus', '0007': 'Itabuna', '0008': 'Jequié',
    '0009': 'Juazeiro', '0010': 'Lauro de Freitas', '0011': 'Paulo Afonso', '0012': 'Porto Seguro',
    '0013': 'Santo Antônio de Jesus', '0014': 'Simões Filho', '0015': 'Teixeira de Freitas',
    '0016': 'Vitória da Conquista', '0072': 'Brumado', '0077': 'Cachoeira', '0127': 'Correntina',
    '0143': 'Euclides da Cunha', '0144': 'Eunápolis', '0147': 'Feira de Santana', '0159': 'Guanambi',
    '0192': 'Itaberaba', '0202': 'Itamaraju', '0210': 'Itapetinga', '0224': 'Jacobina',
    '0225': 'Jaguaquara', '0229': 'Jequié', '0230': 'Jeremoabo', '0234': 'Juazeiro',
    '0250': 'Livramento de Nossa Senhora', '0251': 'Luís Eduardo Magalhães', '0264': 'Maracás',
    '0278': 'Morro do Chapéu', '0310': 'Paulo Afonso', '0327': 'Porto Seguro', '0352': 'Salvador',
    '0362': 'Santaluz', '0365': 'Santo Amaro', '0366': 'Santo Antônio de Jesus', '0384': 'Seabra',
    '0386': 'Senhor do Bonfim', '0391': 'Serrinha', '0404': 'Teixeira de Freitas', '0410': 'Tucano',
    '0421': 'Valença', '0429': 'Vitória da Conquista'
  }
  
  const mapa = tribunal === 'TJSP' ? comarcasTJSP : comarcasTJBA
  const comarca = mapa[codigo] || `Comarca ${codigo}`
  
  // Formatar data como DD/MM/YYYY
  const data = `01/01/${ano}`
  
  return { comarca, data }
}
