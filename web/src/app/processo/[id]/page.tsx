'use client';
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function ProcessoPage() {
  const params = useParams();
  const router = useRouter();
  const [processo, setProcesso] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/processes/${params.id}`)
      .then(res => res.json())
      .then(data => { setProcesso(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [params.id]);

  const abrirNoTribunal = () => {
    fetch(`http://localhost:8000/processes/${params.id}/link`)
      .then(res => res.json())
      .then(data => {
        if (data.link) window.open(data.link, '_blank');
      });
  };

  if (loading) return <div style={{padding:'40px',textAlign:'center'}}>⚖️ Carregando...</div>;
  if (!processo) return <div style={{padding:'40px',textAlign:'center'}}>❌ Processo não encontrado</div>;

  return (
    <div style={{padding:'40px',maxWidth:'1000px',margin:'0 auto',background:'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',minHeight:'100vh'}}>
      <button onClick={() => router.push('/')} style={{marginBottom:'20px',padding:'10px 20px',cursor:'pointer',background:'white',border:'2px solid #3b82f6',borderRadius:'8px',fontWeight:'600'}}>
        ← Voltar ao Dashboard
      </button>
      
      <div style={{background:'white',padding:'40px',borderRadius:'20px',boxShadow:'0 8px 24px rgba(0,0,0,0.12)'}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:'32px'}}>
          <div>
            <h1 style={{margin:'0 0 8px 0',fontSize:'28px'}}>📋 Detalhes do Processo</h1>
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
          </div>
          
          <div style={{display:'flex',gap:'12px'}}>
            <button 
              onClick={abrirNoTribunal}
              style={{
                padding:'14px 24px',
                background:'#3b82f6',
                color:'white',
                border:'none',
                borderRadius:'12px',
                fontSize:'16px',
                fontWeight:'700',
                cursor:'pointer',
                display:'flex',
                alignItems:'center',
                gap:'8px',
                boxShadow:'0 4px 12px rgba(59,130,246,0.3)',
                transition:'all 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              🔗 Abrir no {processo.tribunal}
            </button>
            
            <button 
              style={{
                padding:'14px 24px',
                background:'#f1f5f9',
                color:'#64748b',
                border:'2px solid #e2e8f0',
                borderRadius:'12px',
                fontSize:'16px',
                fontWeight:'700',
                cursor:'not-allowed',
                display:'flex',
                alignItems:'center',
                gap:'8px'
              }}
              title="Funcionalidade em desenvolvimento"
            >
              📄 Baixar Autos
            </button>
          </div>
        </div>

        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'24px',marginTop:'32px'}}>
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px',textTransform:'uppercase'}}>Número CNJ</div>
            <div style={{fontFamily:'monospace',fontSize:'18px',color:'#3b82f6',fontWeight:'700'}}>{processo.numero_cnj}</div>
          </div>
          
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px',textTransform:'uppercase'}}>Tribunal</div>
            <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{processo.tribunal}</div>
          </div>
          
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px',textTransform:'uppercase'}}>Tipo</div>
            <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{processo.tipo_processo}</div>
          </div>
          
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px',textTransform:'uppercase'}}>Classe</div>
            <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{processo.classe || 'Não informado'}</div>
          </div>
          
          <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
            <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px',textTransform:'uppercase'}}>Comarca</div>
            <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{processo.comarca || 'Não informado'}</div>
          </div>
          
          {processo.data_ajuizamento && (
            <div style={{padding:'20px',background:'#f8fafc',borderRadius:'12px',border:'1px solid #e2e8f0'}}>
              <div style={{fontSize:'12px',color:'#64748b',fontWeight:'600',marginBottom:'8px',textTransform:'uppercase'}}>Data Ajuizamento</div>
              <div style={{fontSize:'18px',color:'#1e293b',fontWeight:'700'}}>{new Date(processo.data_ajuizamento).toLocaleDateString('pt-BR')}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
