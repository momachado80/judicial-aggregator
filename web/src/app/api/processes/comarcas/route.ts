import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://judicial-aggregator-production.up.railway.app';
    const response = await fetch(`${apiUrl}/api/processes/comarcas`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Erro ao buscar comarcas:', error);
    // Retornar formato correto mesmo em caso de erro
    return NextResponse.json({
      TJSP: [],
      TJBA: [],
      total: 0,
      error: 'Falha ao carregar comarcas'
    }, { status: 500 });
  }
}
