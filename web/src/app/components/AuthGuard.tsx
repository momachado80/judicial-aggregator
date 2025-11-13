'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Não verificar na página de login
    if (pathname === '/login') {
      setIsChecking(false);
      return;
    }

    // Verificação RÁPIDA - só checa se existe token
    const token = localStorage.getItem('token');
    
    if (!token) {
      // Sem token = redireciona imediatamente
      router.push('/login');
      return;
    }

    // Com token = libera acesso imediatamente
    // A validação real acontece quando o usuário fizer requisições
    setIsChecking(false);
  }, [pathname, router]);

  // Loading rápido (só aparece por 100-200ms)
  if (isChecking && pathname !== '/login') {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #1e293b 0%, #3b82f6 50%, #1e293b 100%)',
        color: 'white',
        fontSize: '20px',
        fontFamily: 'system-ui'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚖️</div>
          <div>Carregando...</div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
