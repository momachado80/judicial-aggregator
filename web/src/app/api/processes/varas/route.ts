import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const comarca = searchParams.get('comarca');
    
    let url = `${process.env.NEXT_PUBLIC_API_URL}/processes/varas`;
    if (comarca) {
      url += `?comarca=${encodeURIComponent(comarca)}`;
    }

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Erro ao buscar varas:', error);
    return NextResponse.json({ varas: [] }, { status: 500 });
  }
}
