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

  if (loading) return <div style={{padding:'40px',textAlign:'center'}}>Carregando...</div>;
  if (!processo) return <div style={{padding:'40px',textAlign:'center'}}>Não encontrado</div>;

  return (
    <div style={{padding:'40px',maxWidth:'1000px',margin:'0 auto'}}>
      <button onClick={() => router.push('/')} style={{marginBottom:'20px',padding:'8px 16px',cursor:'pointer'}}>← Voltar</button>
      <div style={{background:'white',padding:'32px',borderRadius:'16px',boxShadow:'0 4px 12px rgba(0,0,0,0.1)'}}>
        <h1>Detalhes do Processo</h1>
        <div style={{display:'grid',gap:'16px',marginTop:'24px'}}>
          <div><strong>Número:</strong> <span style={{fontFamily:'monospace',color:'#3b82f6'}}>{processo.numero_cnj}</span></div>
          <div><strong>Tribunal:</strong> {processo.tribunal}</div>
          <div><strong>Tipo:</strong> {processo.tipo_processo}</div>
          <div><strong>Classe:</strong> {processo.classe || 'N/A'}</div>
          <div><strong>Comarca:</strong> {processo.comarca || 'N/A'}</div>
          <div><strong>Relevância:</strong> {processo.relevance}</div>
          {processo.valor_causa && <div><strong>Valor:</strong> R$ {processo.valor_causa.toLocaleString('pt-BR')}</div>}
        </div>
      </div>
    </div>
  );
}
