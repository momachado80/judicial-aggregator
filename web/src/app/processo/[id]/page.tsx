'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function ProcessoPage() {
  const params = useParams();
  const router = useRouter();
  const [processo, setProcesso] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [mostrarOpcoesTJBA, setMostrarOpcoesTJBA] = useState(false);

  useEffect(() => {
    fetch(`http://localhost:8000/processes/${params.id}`)
      .then(res => res.json())
      .then(data => { setProcesso(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [params.id]);

  const getAnoProcesso = () => {
    if (!processo?.numero_cnj) return null;
    const match = processo.numero_cnj.match(/\d{7}-\d{2}\.(\d{4})\./);
    return match ? parseInt(match[1]) : null;
  };

  const getSistemaSugerido = () => {
    const ano = getAnoProcesso();
    if (!ano) return { sistema: 'pje', nome: 'PJe', cor: '#3b82f6' };
    if (ano >= 2020) return { sistema: 'pje', nome: 'PJe', cor: '#3b82f6' };
    if (ano >= 2010) return { sistema: 'projudi', nome: 'Projudi', cor: '#8b5cf6' };
    return { sistema: 'saj', nome: 'e-SAJ', cor: '#06b6d4' };
  };

  const copiarNumero = async () => {
    await navigator.clipboard.writeText(processo.numero_cnj);
  };

  const abrirNoTribunal = async (sistema?: string) => {
    if (processo.tribunal === 'TJBA') {
      await copiarNumero();
      
      let link = '';
      let nomeSistema = '';
      
      if (sistema === 'pje') {
        link = 'https://pje.tjba.jus.br/pje/ConsultaPublica/listView.seam';
        nomeSistema = 'PJe';
      } else if (sistema === 'projudi') {
        link = 'https://projudi.tjba.jus.br/projudi/';
        nomeSistema = 'Projudi';
      } else if (sistema === 'saj') {
        link = 'https://esaj.tjba.jus.br/cpopg/open.do';
        nomeSistema = 'e-SAJ';
      } else {
        setMostrarOpcoesTJBA(true);
        return;
      }
      
      alert(`✅ Número copiado!\n\n📋 ${processo.numero_cnj}\n\n🔍 Abrindo ${nomeSistema}...\n\n💡 Dica: Se não encontrar, tente os outros sistemas!`);
      window.open(link, '_blank');
      setMostrarOpcoesTJBA(false);
    } else {
      const res = await fetch(`http://localhost:8000/processes/${params.id}/link`);
      const data = await res.json();
      if (data.link) window.open(data.link, '_blank');
    }
  };

  if (loading) return <div style={{padding:'40px',textAlign:'center'}}>⚖️ Carregando...</div>;
  if (!processo) return <div style={{padding:'40px',textAlign:'center'}}>❌ Processo não encontrado</div>;

  const sugestao = getSistemaSugerido();
  const ano = getAnoProcesso();

  return (
    <div style={{padding:'40px',maxWidth:'1000px',margin:'0 auto',background:'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',minHeight:'100vh'}}>
      <button onClick={() => router.push('/')} style={{marginBottom:'20px',padding:'10px 20px',cursor:'pointer',background:'white',border:'2px solid #3b82f6',borderRadius:'8px',fontWeight:'600'}}>
        ← Voltar ao Dashboard
      </button>
      
      <div style={{background:'white',padding:'40px',borderRadius:'20px',boxShadow:'0 8px 24px rgba(0,0,0,0.12)'}}>
        <div style={{marginBottom:'32px',display:'flex',alignItems:'center',gap:'16px',flexWrap:'wrap'}}>
          <div>
            <h1 style={{margin:'0 0 8px 0',fontSize:'28px'}}>📋 Detalhes do Processo</h1>
            <div style={{display:'flex',gap:'8px',alignItems:'center',flexWrap:'wrap'}}>
              <span style={{
                display:'inline-block',
                padding:'6px 16px',
                background: processo.relevance === 'Alta' ? '#fecaca' : processo.relevance === 'Média' ? '#fed7aa' : '#d1fae5',
                color: processo.relevance === 'Alta' ? '#991b1b' : processo.relevance === 'Média' ? '#9a3412' : '#065f46',
                borderRadius:'12px',
                fontSize:'14px',
                fontWeight:'700'
              }}>
                {processo.relevance}
              </span>
              
              {processo.tribunal === 'TJBA' && (
                <span style={{
                  display:'inline-block',
                  padding:'6px 16px',
                  background: sugestao.cor,
                  color: 'white',
                  borderRadius:'12px',
                  fontSize:'13px',
                  fontWeight:'700'
                }}>
                  💡 Sugestão: {sugestao.nome}
                </span>
              )}
            </div>
          </div>
        </div>

        <div style={{marginBottom:'32px'}}>
          {processo.tribunal === 'TJSP' ? (
            <button 
              onClick={() => abrirNoTribunal()}
              style={{
                padding:'14px 24px',
                background:'#3b82f6',
                color:'white',
                border:'none',
                borderRadius:'12px',
                fontSize:'16px',
                fontWeight:'700',
                cursor:'pointer',
                display:'inline-flex',
                alignItems:'center',
                gap:'8px',
                boxShadow:'0 4px 12px rgba(59,130,246,0.3)'
              }}
            >
              🔗 Abrir no TJSP
            </button>
          ) : (
            <>
              {!mostrarOpcoesTJBA && (
                <div style={{marginBottom:'16px',padding:'20px',background:'linear-gradient(135deg, #dbeafe 0%, #ede9fe 100%)',borderRadius:'16px',border:'2px solid #818cf8'}}>
                  <div style={{fontSize:'15px',color:'#3730a3',fontWeight:'700',marginBottom:'8px',display:'flex',alignItems:'center',gap:'8px'}}>
                    <span>💡</span>
                    <span>Sistema recomendado para processo de {ano}</span>
                  </div>
                  <div style={{fontSize:'14px',color:'#4338ca',lineHeight:'1.6'}}>
                    {ano >= 2020 && '• Processos de 2020 em diante → PJe (mais provável)'}
                    {ano >= 2010 && ano < 2020 && '• Processos de 2010-2019 → Projudi (mais provável)'}
                    {ano < 2010 && '• Processos anteriores a 2010 → e-SAJ (mais provável)'}
                    <br />
                    <span style={{fontSize:'13px',opacity:0.8}}>
                      ⚠️ Se não encontrar, tente os outros sistemas!
                    </span>
                  </div>
                </div>
              )}
              
              {mostrarOpcoesTJBA ? (
                <div style={{display:'flex',gap:'12px',flexWrap:'wrap'}}>
                  <button 
                    onClick={() => abrirNoTribunal('pje')} 
                    style={{
                      padding:'16px 28px',
                      background: sugestao.sistema === 'pje' ? '#3b82f6' : '#e0e7ff',
                      color: sugestao.sistema === 'pje' ? 'white' : '#3730a3',
                      border: sugestao.sistema === 'pje' ? 'none' : '2px solid #6366f1',
                      borderRadius:'12px',
                      cursor:'pointer',
                      fontWeight:'700',
                      fontSize:'15px',
                      position:'relative',
                      boxShadow: sugestao.sistema === 'pje' ? '0 4px 12px rgba(59,130,246,0.4)' : 'none'
                    }}
                  >
                    {sugestao.sistema === 'pje' && <span style={{position:'absolute',top:'-10px',right:'-10px',background:'#10b981',color:'white',borderRadius:'50%',width:'28px',height:'28px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'14px',fontWeight:'bold',boxShadow:'0 2px 8px rgba(16,185,129,0.4)'}}>✓</span>}
                    🔵 PJe<br/><span style={{fontSize:'12px',opacity:0.8}}>(2020+)</span>
                  </button>
                  <button 
                    onClick={() => abrirNoTribunal('projudi')} 
                    style={{
                      padding:'16px 28px',
                      background: sugestao.sistema === 'projudi' ? '#8b5cf6' : '#ede9fe',
                      color: sugestao.sistema === 'projudi' ? 'white' : '#5b21b6',
                      border: sugestao.sistema === 'projudi' ? 'none' : '2px solid #a855f7',
                      borderRadius:'12px',
                      cursor:'pointer',
                      fontWeight:'700',
                      fontSize:'15px',
                      position:'relative',
                      boxShadow: sugestao.sistema === 'projudi' ? '0 4px 12px rgba(139,92,246,0.4)' : 'none'
                    }}
                  >
                    {sugestao.sistema === 'projudi' && <span style={{position:'absolute',top:'-10px',right:'-10px',background:'#10b981',color:'white',borderRadius:'50%',width:'28px',height:'28px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'14px',fontWeight:'bold',boxShadow:'0 2px 8px rgba(16,185,129,0.4)'}}>✓</span>}
                    🟣 Projudi<br/><span style={{fontSize:'12px',opacity:0.8}}>(2010-2019)</span>
                  </button>
                  <button 
                    onClick={() => abrirNoTribunal('saj')} 
                    style={{
                      padding:'16px 28px',
                      background: sugestao.sistema === 'saj' ? '#06b6d4' : '#cffafe',
                      color: sugestao.sistema === 'saj' ? 'white' : '#0e7490',
                      border: sugestao.sistema === 'saj' ? 'none' : '2px solid #22d3ee',
                      borderRadius:'12px',
                      cursor:'pointer',
                      fontWeight:'700',
                      fontSize:'15px',
                      position:'relative',
                      boxShadow: sugestao.sistema === 'saj' ? '0 4px 12px rgba(6,182,212,0.4)' : 'none'
                    }}
                  >
                    {sugestao.sistema === 'saj' && <span style={{position:'absolute',top:'-10px',right:'-10px',background:'#10b981',color:'white',borderRadius:'50%',width:'28px',height:'28px',display:'flex',alignItems:'center',justifyContent:'center',fontSize:'14px',fontWeight:'bold',boxShadow:'0 2px 8px rgba(16,185,129,0.4)'}}>✓</span>}
                    🔵 e-SAJ<br/><span style={{fontSize:'12px',opacity:0.8}}>(Antes 2010)</span>
                  </button>
                  <button 
                    onClick={() => setMostrarOpcoesTJBA(false)} 
                    style={{padding:'16px 28px',background:'#f1f5f9',color:'#64748b',border:'none',borderRadius:'12px',cursor:'pointer',fontWeight:'700',fontSize:'15px'}}
                  >
                    ✕ Cancelar
                  </button>
                </div>
              ) : (
                <button 
                  onClick={() => setMostrarOpcoesTJBA(true)}
                  style={{
                    padding:'16px 32px',
                    background:'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                    color:'white',
                    border:'none',
                    borderRadius:'12px',
                    fontSize:'17px',
                    fontWeight:'700',
                    cursor:'pointer',
                    display:'inline-flex',
                    alignItems:'center',
                    gap:'10px',
                    boxShadow:'0 6px 20px rgba(59,130,246,0.4)'
                  }}
                >
                  🔗 Consultar no TJBA
                </button>
              )}
            </>
          )}
          
          <button 
            style={{
              padding:'16px 32px',
              background:'#f1f5f9',
              color:'#64748b',
              border:'2px solid #e2e8f0',
              borderRadius:'12px',
              fontSize:'16px',
              fontWeight:'700',
              cursor:'not-allowed',
              marginLeft:'12px',
              display:'inline-flex',
              alignItems:'center',
              gap:'8px'
            }}
          >
            📄 Baixar Autos
          </button>
        </div>

        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'24px'}}>
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px'}}>NÚMERO CNJ</div>
            <div style={{fontFamily:'monospace',fontSize:'18px',color:'#3b82f6',fontWeight:'700'}}>{processo.numero_cnj}</div>
          </div>
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px'}}>TRIBUNAL</div>
            <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{processo.tribunal}</div>
          </div>
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px'}}>TIPO</div>
            <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{processo.tipo_processo}</div>
          </div>
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px'}}>CLASSE</div>
            <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{processo.classe || 'N/A'}</div>
          </div>
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px'}}>COMARCA</div>
            <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{processo.comarca || 'N/A'}</div>
          </div>
          {processo.data_ajuizamento && (
            <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
              <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px'}}>DATA AJUIZAMENTO</div>
              <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{new Date(processo.data_ajuizamento).toLocaleDateString('pt-BR')}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
