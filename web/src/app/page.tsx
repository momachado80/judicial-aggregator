'use client';
import { useState, useEffect } from 'react';

type Tab = 'busca' | 'interesse' | 'descartados';

const COMARCAS_SP = ["Adamantina","Adolfo","Aguaí","Águas de Lindóia","Águas de Santa Bárbara","Águas de São Pedro","Agudos","Alambari","Alfredo Marcondes","Altair","Altinópolis","Alto Alegre","Alumínio","Álvares Florence","Álvares Machado","Álvaro de Carvalho","Alvinlândia","Americana","Américo Brasiliense","Américo de Campos","Amparo","Analândia","Andradina","Angatuba","Anhembi","Anhumas","Aparecida","Aparecida d'Oeste","Apiaí","Araçariguama","Araçatuba","Araçoiaba da Serra","Aramina","Arandu","Arapeí","Araraquara","Araras","Arco-Íris","Arealva","Areias","Areiópolis","Ariranha","Artur Nogueira","Arujá","Aspásia","Assis","Atibaia","Auriflama","Avaí","Avanhandava","Avaré","Bady Bassitt","Balbinos","Bálsamo","Bananal","Barão de Antonina","Barbosa","Bariri","Barra Bonita","Barra do Chapéu","Barra do Turvo","Barretos","Barrinha","Barueri","Bastos","Batatais","Bauru","Bebedouro","Bento de Abreu","Bernardino de Campos","Bertioga","Bilac","Birigui","Biritiba-Mirim","Boa Esperança do Sul","Bocaina","Bofete","Boituva","Bom Jesus dos Perdões","Bom Sucesso de Itararé","Borá","Boracéia","Borborema","Borebi","Botucatu","Bragança Paulista","Braúna","Brejo Alegre","Brodowski","Brotas","Buri","Buritama","Buritizal","Cabrália Paulista","Cabreúva","Caçapava","Cachoeira Paulista","Caconde","Cafelândia","Caiabu","Caieiras","Caiuá","Cajamar","Cajati","Cajobi","Cajuru","Campina do Monte Alegre","Campinas","Campo Limpo Paulista","Campos do Jordão","Campos Novos Paulista","Cananéia","Canas","Cândido Mota","Cândido Rodrigues","Canitar","Capão Bonito","Capela do Alto","Capivari","Caraguatatuba","Carapicuíba","Cardoso","Casa Branca","Cássia dos Coqueiros","Castilho","Catanduva","Catiguá","Cedral","Cerqueira César","Cerquilho","Cesário Lange","Charqueada","Chavantes","Clementina","Colina","Colômbia","Conchal","Conchas","Cordeirópolis","Coroados","Coronel Macedo","Corumbataí","Cosmópolis","Cosmorama","Cotia","Cravinhos","Cristais Paulista","Cruzália","Cruzeiro","Cubatão","Cunha","Descalvado","Diadema","Dirce Reis","Divinolândia","Dobrada","Dois Córregos","Dolcinópolis","Dourado","Dracena","Duartina","Dumont","Echaporã","Eldorado","Elias Fausto","Elisiário","Embaúba","Embu das Artes","Embu-Guaçu","Emilianópolis","Engenheiro Coelho","Espírito Santo do Pinhal","Espírito Santo do Turvo","Estiva Gerbi","Estrela do Norte","Estrela d'Oeste","Euclides da Cunha Paulista","Fartura","Fernando Prestes","Fernandópolis","Fernão","Ferraz de Vasconcelos","Flora Rica","Floreal","Flórida Paulista","Florínia","Franca","Francisco Morato","Franco da Rocha","Gabriel Monteiro","Gália","Garça","Gastão Vidigal","Gavião Peixoto","General Salgado","Getulina","Glicério","Guaiçara","Guaimbê","Guaíra","Guapiaçu","Guapiara","Guará","Guaraçaí","Guaraci","Guarani d'Oeste","Guarantã","Guararapes","Guararema","Guaratinguetá","Guareí","Guariba","Guarujá","Guarulhos","Guatapará","Guzolândia","Herculândia","Holambra","Hortolândia","Iacanga","Iacri","Iaras","Ibaté","Ibirá","Ibirarema","Ibitinga","Ibiúna","Icém","Iepê","Igaraçu do Tietê","Igarapava","Igaratá","Iguape","Ilha Comprida","Ilha Solteira","Ilhabela","Indaiatuba","Indiana","Indiaporã","Inúbia Paulista","Ipaussu","Iperó","Ipeúna","Ipiguá","Iporanga","Ipuã","Iracemápolis","Irapuã","Irapuru","Itaberá","Itaí","Itajobi","Itaju","Itanhaém","Itaóca","Itapecerica da Serra","Itapetininga","Itapeva","Itapevi","Itapira","Itapirapuã Paulista","Itápolis","Itaporanga","Itapuí","Itapura","Itaquaquecetuba","Itararé","Itariri","Itatiba","Itatinga","Itirapina","Itirapuã","Itobi","Itu","Itupeva","Ituverava","Jaborandi","Jaboticabal","Jacareí","Jaci","Jacupiranga","Jaguariúna","Jales","Jambeiro","Jandira","Jardinópolis","Jarinu","Jaú","Jeriquara","Joanópolis","João Ramalho","José Bonifácio","Júlio Mesquita","Jumirim","Jundiaí","Junqueirópolis","Juquiá","Juquitiba","Lagoinha","Laranjal Paulista","Lavínia","Lavrinhas","Leme","Lençóis Paulista","Limeira","Lindóia","Lins","Lorena","Lourdes","Louveira","Lucélia","Lucianópolis","Luís Antônio","Luiziânia","Lupércio","Lutécia","Macatuba","Macaubal","Macedônia","Magda","Mairinque","Mairiporã","Manduri","Marabá Paulista","Maracaí","Marapoama","Mariápolis","Marília","Marinópolis","Martinópolis","Matão","Mauá","Mendonça","Meridiano","Mesópolis","Miguelópolis","Mineiros do Tietê","Mira Estrela","Miracatu","Mirandópolis","Mirante do Paranapanema","Mirassol","Mirassolândia","Mococa","Mogi das Cruzes","Mogi Guaçu","Mogi Mirim","Mombuca","Monções","Mongaguá","Monte Alegre do Sul","Monte Alto","Monte Aprazível","Monte Azul Paulista","Monte Castelo","Monte Mor","Monteiro Lobato","Morro Agudo","Morungaba","Motuca","Murutinga do Sul","Nantes","Narandiba","Natividade da Serra","Nazaré Paulista","Neves Paulista","Nhandeara","Nipoã","Nova Aliança","Nova Campina","Nova Canaã Paulista","Nova Castilho","Nova Europa","Nova Granada","Nova Guataporanga","Nova Independência","Nova Luzitânia","Nova Odessa","Novais","Novo Horizonte","Nuporanga","Ocauçu","Óleo","Olímpia","Onda Verde","Oriente","Orindiúva","Orlândia","Osasco","Oscar Bressane","Osvaldo Cruz","Ourinhos","Ouro Verde","Ouroeste","Pacaembu","Palestina","Palmares Paulista","Palmeira d'Oeste","Palmital","Panorama","Paraguaçu Paulista","Paraibuna","Paraíso","Paranapanema","Paranapuã","Parapuã","Pardinho","Pariquera-Açu","Parisi","Patrocínio Paulista","Paulicéia","Paulínia","Paulistânia","Paulo de Faria","Pederneiras","Pedra Bela","Pedranópolis","Pedregulho","Pedreira","Pedrinhas Paulista","Pedro de Toledo","Penápolis","Pereira Barreto","Pereiras","Peruíbe","Piacatu","Piedade","Pilar do Sul","Pindamonhangaba","Pindorama","Pinhalzinho","Piquerobi","Piquete","Piracaia","Piracicaba","Piraju","Pirajuí","Pirangi","Pirapora do Bom Jesus","Pirapozinho","Pirassununga","Piratininga","Pitangueiras","Planalto","Platina","Poá","Poloni","Pompéia","Pongaí","Pontal","Pontalinda","Pontes Gestal","Populina","Porangaba","Porto Feliz","Porto Ferreira","Potim","Potirendaba","Pracinha","Pradópolis","Praia Grande","Pratânia","Presidente Alves","Presidente Bernardes","Presidente Epitácio","Presidente Prudente","Presidente Venceslau","Promissão","Quadra","Quatá","Queiroz","Queluz","Quintana","Rafard","Rancharia","Redenção da Serra","Regente Feijó","Reginópolis","Registro","Restinga","Ribeira","Ribeirão Bonito","Ribeirão Branco","Ribeirão Corrente","Ribeirão do Sul","Ribeirão dos Índios","Ribeirão Grande","Ribeirão Pires","Ribeirão Preto","Rifaina","Rincão","Rinópolis","Rio Claro","Rio das Pedras","Rio Grande da Serra","Riolândia","Riversul","Rosana","Roseira","Rubiácea","Rubinéia","Sabino","Sagres","Sales","Sales Oliveira","Salesópolis","Salmourão","Saltinho","Salto","Salto de Pirapora","Salto Grande","Sandovalina","Santa Adélia","Santa Albertina","Santa Bárbara d'Oeste","Santa Branca","Santa Clara d'Oeste","Santa Cruz da Conceição","Santa Cruz da Esperança","Santa Cruz das Palmeiras","Santa Cruz do Rio Pardo","Santa Ernestina","Santa Fé do Sul","Santa Gertrudes","Santa Isabel","Santa Lúcia","Santa Maria da Serra","Santa Mercedes","Santa Rita do Passa Quatro","Santa Rita d'Oeste","Santa Rosa de Viterbo","Santa Salete","Santana da Ponte Pensa","Santana de Parnaíba","Santo Anastácio","Santo André","Santo Antônio da Alegria","Santo Antônio de Posse","Santo Antônio do Aracanguá","Santo Antônio do Jardim","Santo Antônio do Pinhal","Santo Expedito","Santópolis do Aguapeí","Santos","São Bento do Sapucaí","São Bernardo do Campo","São Caetano do Sul","São Carlos","São Francisco","São João da Boa Vista","São João das Duas Pontes","São João de Iracema","São João do Pau d'Alho","São Joaquim da Barra","São José da Bela Vista","São José do Barreiro","São José do Rio Pardo","São José do Rio Preto","São José dos Campos","São Lourenço da Serra","São Luís do Paraitinga","São Manuel","São Miguel Arcanjo","São Paulo","São Pedro","São Pedro do Turvo","São Roque","São Sebastião","São Sebastião da Grama","São Simão","São Vicente","Sarapuí","Sarutaiá","Sebastianópolis do Sul","Serra Azul","Serra Negra","Serrana","Sertãozinho","Sete Barras","Severínia","Silveiras","Socorro","Sorocaba","Sud Mennucci","Sumaré","Suzanápolis","Suzano","Tabapuã","Tabatinga","Taboão da Serra","Taciba","Taguaí","Taiaçu","Taiúva","Tambaú","Tanabi","Tapiraí","Tapiratiba","Taquaral","Taquaritinga","Taquarituba","Taquarivaí","Tarabai","Tarumã","Tatuí","Taubaté","Tejupá","Teodoro Sampaio","Terra Roxa","Tietê","Timburi","Torre de Pedra","Torrinha","Trabiju","Tremembé","Três Fronteiras","Tuiuti","Tupã","Tupi Paulista","Turiúba","Turmalina","Ubarana","Ubatuba","Ubirajara","Uchoa","União Paulista","Urânia","Uru","Urupês","Valentim Gentil","Valinhos","Valparaíso","Vargem","Vargem Grande do Sul","Vargem Grande Paulista","Várzea Paulista","Vera Cruz","Vinhedo","Viradouro","Vista Alegre do Alto","Vitória Brasil","Votorantim","Votuporanga","Zacarias"];

const COMARCAS_BA = ["Abaíra","Abaré","Acajutiba","Adustina","Água Fria","Aiquara","Alagoinhas","Alcobaça","Almadina","Amargosa","Amélia Rodrigues","América Dourada","Anagé","Andaraí","Andorinha","Angical","Anguera","Antas","Antônio Cardoso","Antônio Gonçalves","Aporá","Apuarema","Aracatu","Araci","Aramari","Arataca","Aratuípe","Aurelino Leal","Baianópolis","Baixa Grande","Banzaê","Barra","Barra da Estiva","Barra do Choça","Barra do Mendes","Barra do Rocha","Barreiras","Barro Alto","Barrocas","Belmonte","Belo Campo","Biritinga","Boa Nova","Boa Vista do Tupim","Bom Jesus da Lapa","Bom Jesus da Serra","Boninal","Bonito","Boquira","Botuporã","Brejões","Brejolândia","Brotas de Macaúbas","Brumado","Buerarema","Buritirama","Caatiba","Cabaceiras do Paraguaçu","Cachoeira","Caculé","Caém","Caetanos","Caetité","Cafarnaum","Cairu","Caldeirão Grande","Camacan","Camaçari","Camamu","Campo Alegre de Lourdes","Campo Formoso","Canápolis","Canarana","Canavieiras","Candeal","Candeias","Candiba","Cândido Sales","Cansanção","Canudos","Capela do Alto Alegre","Capim Grosso","Caraíbas","Caravelas","Cardeal da Silva","Carinhanha","Casa Nova","Castro Alves","Catolândia","Catu","Caturama","Central","Chorrochó","Cícero Dantas","Cipó","Coaraci","Cocos","Conceição da Feira","Conceição do Almeida","Conceição do Coité","Conceição do Jacuípe","Conde","Condeúba","Contendas do Sincorá","Coração de Maria","Cordeiros","Coribe","Coronel João Sá","Correntina","Cotegipe","Cravolândia","Crisópolis","Cristópolis","Cruz das Almas","Curaçá","Dário Meira","Dias d'Ávila","Dom Basílio","Dom Macedo Costa","Elísio Medrado","Encruzilhada","Entre Rios","Esplanada","Euclides da Cunha","Eunápolis","Fátima","Feira da Mata","Feira de Santana","Filadélfia","Firmino Alves","Floresta Azul","Formosa do Rio Preto","Gandu","Gavião","Gentio do Ouro","Glória","Gongogi","Governador Mangabeira","Guajeru","Guanambi","Guaratinga","Heliópolis","Iaçu","Ibiassucê","Ibicaraí","Ibicoara","Ibicuí","Ibipeba","Ibipitanga","Ibiquera","Ibirapitanga","Ibirapuã","Ibirataia","Ibitiara","Ibititá","Ibotirama","Ichu","Igaporã","Igrapiúna","Iguaí","Ilhéus","Inhambupe","Ipecaetá","Ipiaú","Ipirá","Ipupiara","Irajuba","Iramaia","Iraquara","Irará","Irecê","Itabela","Itaberaba","Itabuna","Itacaré","Itaeté","Itagi","Itagibá","Itagimirim","Itaguaçu da Bahia","Itaju do Colônia","Itajuípe","Itamaraju","Itamari","Itambé","Itanagra","Itanhém","Itaparica","Itapé","Itapebi","Itapetinga","Itapicuru","Itapitanga","Itaquara","Itarantim","Itatim","Itiruçu","Itiúba","Itororó","Ituaçu","Ituberá","Iuiú","Jaborandi","Jacaraci","Jacobina","Jaguaquara","Jaguarari","Jaguaripe","Jandaíra","Jequié","Jeremoabo","Jiquiriçá","Jitaúna","João Dourado","Juazeiro","Jucuruçu","Jussara","Jussari","Jussiape","Lafaiete Coutinho","Lagoa Real","Laje","Lajedão","Lajedinho","Lajedo do Tabocal","Lamarão","Lapão","Lauro de Freitas","Lençóis","Licínio de Almeida","Livramento de Nossa Senhora","Luís Eduardo Magalhães","Macajuba","Macarani","Macaúbas","Macururé","Madre de Deus","Maetinga","Maiquinique","Mairi","Malhada","Malhada de Pedras","Manoel Vitorino","Mansidão","Maracás","Maragogipe","Maraú","Marcionílio Souza","Mascote","Mata de São João","Matina","Medeiros Neto","Miguel Calmon","Milagres","Mirangaba","Mirante","Monte Santo","Morpará","Morro do Chapéu","Mortugaba","Mucugê","Mucuri","Mulungu do Morro","Mundo Novo","Muniz Ferreira","Muquém do São Francisco","Muritiba","Mutuípe","Nazaré","Nilo Peçanha","Nordestina","Nova Canaã","Nova Fátima","Nova Ibiá","Nova Itarana","Nova Redenção","Nova Soure","Nova Viçosa","Novo Horizonte","Novo Triunfo","Olindina","Oliveira dos Brejinhos","Ouriçangas","Ourolândia","Palmas de Monte Alto","Palmeiras","Paramirim","Paratinga","Paripiranga","Pau Brasil","Paulo Afonso","Pé de Serra","Pedrão","Pedro Alexandre","Piatã","Pilão Arcado","Pindaí","Pindobaçu","Pintadas","Piraí do Norte","Piripá","Piritiba","Planaltino","Planalto","Poções","Pojuca","Ponto Novo","Porto Seguro","Potiraguá","Prado","Presidente Dutra","Presidente Jânio Quadros","Presidente Tancredo Neves","Queimadas","Quijingue","Quixabeira","Rafael Jambeiro","Remanso","Retirolândia","Riachão das Neves","Riachão do Jacuípe","Riacho de Santana","Ribeira do Amparo","Ribeira do Pombal","Ribeirão do Largo","Rio de Contas","Rio do Antônio","Rio do Pires","Rio Real","Rodelas","Ruy Barbosa","Salinas da Margarida","Salvador","Santa Bárbara","Santa Brígida","Santa Cruz Cabrália","Santa Cruz da Vitória","Santa Inês","Santa Luzia","Santa Maria da Vitória","Santa Rita de Cássia","Santa Teresinha","Santaluz","Santana","Santanópolis","Santo Amaro","Santo Antônio de Jesus","Santo Estêvão","São Desidério","São Domingos","São Felipe","São Félix","São Félix do Coribe","São Francisco do Conde","São Gabriel","São Gonçalo dos Campos","São José da Vitória","São José do Jacuípe","São Miguel das Matas","São Sebastião do Passé","Sapeaçu","Sátiro Dias","Saubara","Saúde","Seabra","Sebastião Laranjeiras","Senhor do Bonfim","Sento Sé","Serra do Ramalho","Serra Dourada","Serra Preta","Serrinha","Serrolândia","Simões Filho","Sítio do Mato","Sítio do Quinto","Sobradinho","Souto Soares","Tabocas do Brejo Velho","Tanhaçu","Tanque Novo","Tanquinho","Taperoá","Tapiramutá","Teixeira de Freitas","Teodoro Sampaio","Teofilândia","Teolândia","Terra Nova","Tremedal","Tucano","Uauá","Ubaíra","Ubaitaba","Ubatã","Uibaí","Umburanas","Una","Urandi","Uruçuca","Utinga","Valença","Valente","Várzea da Roça","Várzea do Poço","Várzea Nova","Varzedo","Vera Cruz","Vereda","Vitória da Conquista","Wagner","Wanderley","Wenceslau Guimarães","Xique-Xique"];

export default function Home() {
  const [processos, setProcessos] = useState([]);
  const [interesseIds, setInteresseIds] = useState<Set<number>>(new Set());
  const [descartadosIds, setDescartadosIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState<Tab>('busca');
  
  const [tribunais, setTribunais] = useState({ TJSP: true, TJBA: false });
  const [tipos, setTipos] = useState({ 'Inventário': true, 'Divórcio Litigioso': false, 'Divórcio Consensual': false });
  const [comarcasInput, setComarcasInput] = useState('');
  const [comarcasSelecionadas, setComarcasSelecionadas] = useState<string[]>([]);
  const [sugestoes, setSugestoes] = useState<string[]>([]);
  const [valorMin, setValorMin] = useState('');
  const [valorMax, setValorMax] = useState('');
  const [ano, setAno] = useState('');
  const [quantidade, setQuantidade] = useState(500);

  const todasComarcas = [...COMARCAS_SP, ...COMARCAS_BA];

  useEffect(() => {
    const saved = localStorage.getItem('judicial_interesse');
    if (saved) setInteresseIds(new Set(JSON.parse(saved)));
    const desc = localStorage.getItem('judicial_descartados');
    if (desc) setDescartadosIds(new Set(JSON.parse(desc)));
  }, []);

  const handleComarcaInput = (value: string) => {
    setComarcasInput(value);
    if (value.trim().length > 1) {
      const filtradas = todasComarcas.filter(c => 
        c.toLowerCase().includes(value.toLowerCase())
      ).slice(0, 15);
      setSugestoes(filtradas);
    } else {
      setSugestoes([]);
    }
  };

  const adicionarComarca = (comarca: string) => {
    if (!comarcasSelecionadas.includes(comarca)) {
      setComarcasSelecionadas([...comarcasSelecionadas, comarca]);
    }
    setComarcasInput('');
    setSugestoes([]);
  };

  const removerComarca = (comarca: string) => {
    setComarcasSelecionadas(comarcasSelecionadas.filter(c => c !== comarca));
  };

  const marcarInteresse = async (id: number) => {
    await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'interesse' })
    });
    const novos = new Set(interesseIds);
              comarcas: comarcasSelecionadas.length > 0 ? comarcasSelecionadas : undefined,
    novos.add(id);
    localStorage.setItem('judicial_interesse', JSON.stringify(Array.from(novos)));
    setInteresseIds(novos);
  };

  const descartar = async (id: number) => {
    await fetch(`https://judicial-aggregator-production.up.railway.app/processes/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'descartado' })
    });
    const novos = new Set(descartadosIds);
              comarcas: comarcasSelecionadas.length > 0 ? comarcasSelecionadas : undefined,
    novos.add(id);
    localStorage.setItem('judicial_descartados', JSON.stringify(Array.from(novos)));
    setDescartadosIds(novos);
  };

  async function handleBuscar() {
    setLoading(true);
    setSearched(true);
    const tribunaisSelecionados = Object.keys(tribunais).filter(k => tribunais[k]);
    const tiposSelecionados = Object.keys(tipos).filter(k => tipos[k]);
    
    try {
      let todosProcessos = [];
      let todosStats = { novos: 0, duplicados: 0, inativos: 0 };
      
      for (const trib of tribunaisSelecionados) {
        for (const tipo of tiposSelecionados) {
          const response = await fetch('https://judicial-aggregator-production.up.railway.app/api/buscar-processos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              tribunal: trib,
              tipo_processo: tipo,
              comarcas: comarcasSelecionadas.length > 0 ? comarcasSelecionadas : undefined,
              valor_causa_min: valorMin ? Number(valorMin) : undefined,
              valor_causa_max: valorMax ? Number(valorMax) : undefined,
              limit: Math.floor(quantidade / (tribunaisSelecionados.length * tiposSelecionados.length))
            })
          });
          const data = await response.json();
          todosProcessos = [...todosProcessos, ...(data.processos || [])];
          todosStats.novos += data.stats?.novos || 0;
          todosStats.duplicados += data.stats?.duplicados || 0;
          todosStats.inativos += data.stats?.inativos || 0;
        }
      }
      
      if (comarcasSelecionadas.length > 0) {
        todosProcessos = todosProcessos.filter(p => 
          comarcasSelecionadas.some(c => p.comarca?.toLowerCase().includes(c.toLowerCase()))
        );
      }
      
      setProcessos(todosProcessos);
      setStats(todosStats);
    } catch (error) {
      alert('Erro ao buscar');
    }
    setLoading(false);
  }

  const anos = [];
  for (let i = 2025; i >= 2000; i--) anos.push(i);

  const processosFiltrados = processos.filter(p => {
    if (activeTab === 'interesse') return interesseIds.has(p.id);
    if (activeTab === 'descartados') return descartadosIds.has(p.id);
    return !descartadosIds.has(p.id);
  });

  const algumTribunalSelecionado = tribunais.TJSP || tribunais.TJBA;
  const algumTipoSelecionado = tipos['Inventário'] || tipos['Divórcio Litigioso'] || tipos['Divórcio Consensual'];

  return (
    <div style={{minHeight: '100vh', background: '#f3f4f6', padding: '2rem'}}>
      <div style={{maxWidth: '1400px', margin: '0 auto'}}>
        <h1 style={{fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '2rem'}}>⚖️ Judicial Aggregator</h1>
        
        <div style={{background: 'white', borderRadius: '12px', padding: '2rem', marginBottom: '2rem', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}>
          <h2 style={{fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '1.5rem'}}>🔍 Buscar Processos Ativos</h2>
          
          <div style={{marginBottom: '1.5rem'}}>
            <label style={{display: 'block', marginBottom: '0.75rem', fontWeight: '600'}}>Tribunais *</label>
            <div style={{display: 'flex', gap: '2rem'}}>
              <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
                <input type="checkbox" checked={tribunais.TJSP} onChange={(e) => setTribunais({...tribunais, TJSP: e.target.checked})} style={{width: '20px', height: '20px'}} />
                <span style={{fontSize: '1.125rem'}}>TJSP</span>
              </label>
              <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
                <input type="checkbox" checked={tribunais.TJBA} onChange={(e) => setTribunais({...tribunais, TJBA: e.target.checked})} style={{width: '20px', height: '20px'}} />
                <span style={{fontSize: '1.125rem'}}>TJBA</span>
              </label>
            </div>
          </div>

          <div style={{marginBottom: '1.5rem'}}>
            <label style={{display: 'block', marginBottom: '0.75rem', fontWeight: '600'}}>Tipos *</label>
            <div style={{display: 'flex', gap: '2rem'}}>
              <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
                <input type="checkbox" checked={tipos['Inventário']} onChange={(e) => setTipos({...tipos, 'Inventário': e.target.checked})} style={{width: '20px', height: '20px'}} />
                <span>Inventário</span>
              </label>
              <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
                <input type="checkbox" checked={tipos['Divórcio Litigioso']} onChange={(e) => setTipos({...tipos, 'Divórcio Litigioso': e.target.checked})} style={{width: '20px', height: '20px'}} />
                <span>Divórcio Litigioso</span>
              </label>
              <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
                <input type="checkbox" checked={tipos['Divórcio Consensual']} onChange={(e) => setTipos({...tipos, 'Divórcio Consensual': e.target.checked})} style={{width: '20px', height: '20px'}} />
                <span>Divórcio Consensual</span>
              </label>
            </div>
          </div>

          <div style={{marginBottom: '1.5rem'}}>
            <label style={{display: 'block', marginBottom: '0.75rem', fontWeight: '600'}}>
              Comarcas - {COMARCAS_SP.length} SP + {COMARCAS_BA.length} BA = {todasComarcas.length} total
            </label>
            <div style={{position: 'relative'}}>
              <input 
                type="text" 
                value={comarcasInput}
                onChange={(e) => handleComarcaInput(e.target.value)}
                placeholder="Digite: Piracicaba, Americana, Salvador..."
                style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px', fontSize: '1rem'}}
              />
              {sugestoes.length > 0 && (
                <div style={{position: 'absolute', top: '100%', left: 0, right: 0, background: 'white', border: '2px solid #e5e7eb', borderTop: 'none', borderRadius: '0 0 8px 8px', maxHeight: '250px', overflowY: 'auto', zIndex: 10, boxShadow: '0 4px 12px rgba(0,0,0,0.15)'}}>
                  {sugestoes.map(comarca => (
                    <div 
                      key={comarca}
                      onClick={() => adicionarComarca(comarca)}
                      style={{padding: '0.875rem', cursor: 'pointer', borderBottom: '1px solid #f3f4f6'}}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#eff6ff'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                    >
                      {comarca}
                    </div>
                  ))}
                </div>
              )}
            </div>
            {comarcasSelecionadas.length > 0 && (
              <div style={{marginTop: '0.75rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem'}}>
                {comarcasSelecionadas.map(comarca => (
                  <span key={comarca} style={{background: '#dbeafe', padding: '0.5rem 1rem', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                    {comarca}
                    <button onClick={() => removerComarca(comarca)} style={{background: 'transparent', border: 'none', cursor: 'pointer', fontSize: '1.25rem', color: '#ef4444', fontWeight: 'bold'}}>
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '1.5rem'}}>
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Quantidade *</label>
              <select value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))} style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px'}}>
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="500">500</option>
                <option value="1000">1000</option>
              </select>
            </div>
            
            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Ano</label>
              <select value={ano} onChange={(e) => setAno(e.target.value)} style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px'}}>
                <option value="">Todos</option>
                {anos.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>

            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Valor Mín (R$)</label>
              <input type="number" value={valorMin} onChange={(e) => setValorMin(e.target.value)} placeholder="100000" style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px'}} />
            </div>

            <div>
              <label style={{display: 'block', marginBottom: '0.5rem', fontWeight: '600'}}>Valor Máx (R$)</label>
              <input type="number" value={valorMax} onChange={(e) => setValorMax(e.target.value)} placeholder="5000000" style={{width: '100%', padding: '0.875rem', border: '2px solid #e5e7eb', borderRadius: '8px'}} />
            </div>
          </div>

          <div style={{background: '#eff6ff', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', fontSize: '0.875rem', color: '#1e40af'}}>
            ℹ️ Apenas processos ATIVOS (exclui extintos, suspensos, arquivados)
          </div>
          
          <button onClick={handleBuscar} disabled={loading || !algumTribunalSelecionado || !algumTipoSelecionado} style={{width: '100%', background: (loading || !algumTribunalSelecionado || !algumTipoSelecionado) ? '#9ca3af' : '#2563eb', color: 'white', padding: '1.25rem', borderRadius: '10px', fontSize: '1.25rem', fontWeight: 'bold', border: 'none', cursor: (loading || !algumTribunalSelecionado || !algumTipoSelecionado) ? 'not-allowed' : 'pointer'}}>
            {loading ? '🔄 Buscando...' : '🔍 BUSCAR PROCESSOS'}
          </button>
        </div>

        {stats && (
          <div style={{background: 'white', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem'}}>
            <h3 style={{fontWeight: 'bold', marginBottom: '1rem'}}>📊 Resultados:</h3>
            <div style={{display: 'flex', gap: '1rem'}}>
              <div style={{background: '#d1fae5', padding: '0.75rem 1.5rem', borderRadius: '8px', fontWeight: '600'}}>✅ Novos: {stats.novos}</div>
              <div style={{background: '#dbeafe', padding: '0.75rem 1.5rem', borderRadius: '8px', fontWeight: '600'}}>🔄 Duplicados: {stats.duplicados}</div>
              <div style={{background: '#fee2e2', padding: '0.75rem 1.5rem', borderRadius: '8px', fontWeight: '600'}}>❌ Inativos: {stats.inativos}</div>
            </div>
          </div>
        )}

        {searched && (
          <div style={{marginBottom: '1.5rem', background: 'white', borderRadius: '12px', padding: '0.5rem', display: 'flex', gap: '0.5rem'}}>
            <button onClick={() => setActiveTab('busca')} style={{flex: 1, padding: '1rem', background: activeTab === 'busca' ? '#2563eb' : 'transparent', color: activeTab === 'busca' ? 'white' : '#374151', border: 'none', borderRadius: '8px', fontWeight: '600', cursor: 'pointer'}}>
              📋 Busca ({processos.filter(p => !descartadosIds.has(p.id)).length})
            </button>
            <button onClick={() => setActiveTab('interesse')} style={{flex: 1, padding: '1rem', background: activeTab === 'interesse' ? '#10b981' : 'transparent', color: activeTab === 'interesse' ? 'white' : '#374151', border: 'none', borderRadius: '8px', fontWeight: '600', cursor: 'pointer'}}>
              ⭐ Interesse ({interesseIds.size})
            </button>
            <button onClick={() => setActiveTab('descartados')} style={{flex: 1, padding: '1rem', background: activeTab === 'descartados' ? '#ef4444' : 'transparent', color: activeTab === 'descartados' ? 'white' : '#374151', border: 'none', borderRadius: '8px', fontWeight: '600', cursor: 'pointer'}}>
              🗑️ Descartados ({descartadosIds.size})
            </button>
          </div>
        )}

        {!searched && !loading && (
          <div style={{background: 'white', borderRadius: '12px', padding: '4rem', textAlign: 'center'}}>
            <div style={{fontSize: '4rem'}}>🔍</div>
            <p style={{fontSize: '1.5rem', fontWeight: '600'}}>Pronto para buscar</p>
          </div>
        )}

        {loading && <div style={{textAlign: 'center', padding: '6rem', fontSize: '5rem'}}>🔄</div>}

        {processosFiltrados.length > 0 && (
          <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            {processosFiltrados.map((p) => (
              <div key={p.id} style={{background: p.novo ? '#dbeafe' : 'white', border: p.novo ? '3px solid #3b82f6' : '1px solid #e5e7eb', borderRadius: '12px', padding: '1.75rem', boxShadow: p.novo ? '0 4px 20px rgba(59, 130, 246, 0.3)' : '0 2px 8px rgba(0,0,0,0.1)'}}>
                <div style={{marginBottom: '1rem'}}>
                  {p.novo && <span style={{background: '#3b82f6', color: 'white', padding: '0.5rem 1rem', borderRadius: '6px', fontSize: '0.875rem', fontWeight: 'bold', marginRight: '0.75rem'}}>🆕 NOVO</span>}
                  {p.valor_causa > 1000000 && <span style={{background: '#f59e0b', color: 'white', padding: '0.5rem 1rem', borderRadius: '6px', fontSize: '0.875rem', fontWeight: 'bold'}}>💎 ALTO VALOR</span>}
                </div>
                <h3 style={{fontSize: '1.25rem', fontWeight: 'bold', fontFamily: 'monospace', marginBottom: '0.75rem'}}>{p.numero_cnj}</h3>
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', color: '#6b7280', marginBottom: '1.5rem'}}>
                  <p><strong>Tipo:</strong> {p.tipo_processo}</p>
                  <p><strong>Tribunal:</strong> {p.tribunal}</p>
                  {p.comarca && <p><strong>Comarca:</strong> {p.comarca}</p>}
                </div>
                
                {activeTab === 'busca' && !interesseIds.has(p.id) && (
                  <div style={{display: 'flex', gap: '1rem'}}>
                    <button onClick={() => marcarInteresse(p.id)} style={{flex: 1, background: '#10b981', color: 'white', padding: '0.875rem', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer'}}>
                      ⭐ Interesse
                    </button>
                    <button onClick={() => descartar(p.id)} style={{flex: 1, background: '#ef4444', color: 'white', padding: '0.875rem', borderRadius: '8px', border: 'none', fontWeight: '600', cursor: 'pointer'}}>
                      🗑️ Descartar
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {searched && processosFiltrados.length === 0 && !loading && (
          <div style={{background: 'white', borderRadius: '12px', padding: '4rem', textAlign: 'center'}}>
            <p style={{fontSize: '1.5rem', fontWeight: '600'}}>Nenhum processo nesta aba</p>
          </div>
        )}
      </div>
    </div>
  );
}
