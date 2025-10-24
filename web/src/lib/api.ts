import axios from 'axios';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000',
});

export interface Process {
  id: number;
  numero_cnj: string;
  tribunal: string;
  classe_tpu: string;
  assunto_tpu: string[];
  orgao: string;
  vara: string;
  comarca: string;
  valor_causa: number;
  relevance: string;
  created_at: string;
  updated_at: string;
}

export interface ProcessDetail extends Process {
  parties: Array<{
    id: number;
    tipo: string;
    nome: string;
  }>;
  movements: Array<{
    id: number;
    data: string;
    tipo_tpu: string;
    descricao_norm: string;
    relevance: string;
  }>;
}

export async function fetchProcesses(params: {
  page?: number;
  page_size?: number;
  tribunal?: string;
  classe?: string;
  assunto?: string;
  relevance?: string;
  numero_cnj?: string;
}) {
  const response = await api.get<{
    items: Process[];
    total: number;
    page: number;
    page_size: number;
  }>('/processes', { params });
  return response.data;
}

export async function fetchProcessById(id: number) {
  const response = await api.get<ProcessDetail>(\`/processes/\${id}\`);
  return response.data;
}
