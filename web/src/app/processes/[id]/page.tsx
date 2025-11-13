'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import axios from 'axios';

interface Party {
  id: number;
  nome: string;
  tipo: string;
  cpf_cnpj: string | null;
}

interface Movement {
  id: number;
  data_movimento: string;
  descricao: string;
}

interface ProcessDetail {
  id: number;
  numero_cnj: string;
  tribunal: string;
  classe_tpu: string;
  assunto_tpu: string;
  comarca: string;
  vara: string;
  valor_causa: number | null;
  relevance: string;
  parties?: Party[];
  movements?: Movement[];
}

export default function ProcessDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [process, setProcess] = useState<ProcessDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (params.id) {
      fetchProcessDetail(params.id as string);
    }
  }, [params.id]);

  const fetchProcessDetail = async (id: string) => {
    try {
      setLoading(true);
      const response = await axios.get<ProcessDetail>(`https://judicial-aggregator-production.up.railway.app/processes/${id}`);
      setProcess(response.data);
      setError(null);
    } catch (err) {
      setError('Erro ao carregar detalhes do processo');
      console.error('Erro:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number | null) => {
    if (!value) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('pt-BR');
    } catch {
      return dateString;
    }
  };

  const getClasseLabel = (classe: string) => {
    return classe === '8015' ? 'Divórcio' : 'Inventário';
  };

  const getPartyTypeLabel = (tipo: string) => {
    const types: { [key: string]: string } = {
      'autor': '👤 Autor',
      'reu': '👥 Réu',
      'advogado': '⚖️ Advogado',
      'testemunha': '👁️ Testemunha',
    };
    return types[tipo.toLowerCase()] || tipo;
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">
          <div className="spinner"></div>
          <p>Carregando detalhes...</p>
        </div>
      </div>
    );
  }

  if (error || !process) {
    return (
      <div className="container">
        <div className="detail-error">
          <p>❌ {error || 'Processo não encontrado'}</p>
          <button onClick={() => router.push('/')} className="back-btn">
            ← Voltar para Dashboard
          </button>
        </div>
      </div>
    );
  }

  const parties = process.parties || [];
  const movements = process.movements || [];

  return (
    <div className="container">
      <div className="detail-header">
        <button onClick={() => router.push('/')} className="back-btn">
          ← Voltar
        </button>
        <h1 className="detail-title">Detalhes do Processo</h1>
      </div>

      <div className="detail-content">
        <div className="detail-main-card">
          <div className="detail-cnj-section">
            <span className="detail-cnj-label">Número CNJ</span>
            <span className="detail-cnj-number">{process.numero_cnj}</span>
            <span className={`detail-badge ${process.relevance}`}>
              {process.relevance}
            </span>
          </div>

          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-item-label">🏛️ Tribunal</span>
              <span className="detail-item-value">{process.tribunal}</span>
            </div>

            <div className="detail-item">
              <span className="detail-item-label">📋 Tipo</span>
              <span className="detail-item-value">{getClasseLabel(process.classe_tpu)}</span>
            </div>

            <div className="detail-item">
              <span className="detail-item-label">📍 Comarca</span>
              <span className="detail-item-value">{process.comarca}</span>
            </div>

            <div className="detail-item">
              <span className="detail-item-label">⚖️ Vara</span>
              <span className="detail-item-value">{process.vara}</span>
            </div>

            <div className="detail-item">
              <span className="detail-item-label">📁 Assunto</span>
              <span className="detail-item-value">{process.assunto_tpu}</span>
            </div>

            <div className="detail-item">
              <span className="detail-item-label">💰 Valor da Causa</span>
              <span className="detail-item-value detail-value-highlight">
                {formatCurrency(process.valor_causa)}
              </span>
            </div>
          </div>
        </div>

        <div className="detail-section-card">
          <h2 className="detail-section-title">
            👥 Partes Envolvidas ({parties.length})
          </h2>
          
          {parties.length === 0 ? (
            <p className="detail-empty">Nenhuma parte cadastrada</p>
          ) : (
            <div className="parties-list">
              {parties.map((party) => (
                <div key={party.id} className="party-item">
                  <div className="party-type">{getPartyTypeLabel(party.tipo)}</div>
                  <div className="party-info">
                    <div className="party-name">{party.nome}</div>
                    {party.cpf_cnpj && (
                      <div className="party-doc">{party.cpf_cnpj}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="detail-section-card">
          <h2 className="detail-section-title">
            📅 Movimentações Processuais ({movements.length})
          </h2>
          
          {movements.length === 0 ? (
            <p className="detail-empty">Nenhuma movimentação registrada</p>
          ) : (
            <div className="timeline">
              {movements
                .sort((a, b) => new Date(b.data_movimento).getTime() - new Date(a.data_movimento).getTime())
                .map((movement) => (
                  <div key={movement.id} className="timeline-item">
                    <div className="timeline-marker"></div>
                    <div className="timeline-content">
                      <div className="timeline-date">
                        📆 {formatDate(movement.data_movimento)}
                      </div>
                      <div className="timeline-description">
                        {movement.descricao}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
