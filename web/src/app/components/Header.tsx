'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Header() {
  const pathname = usePathname()
  const isLoginPage = pathname === '/login'

  return (
    <header className="header">
      <div className="header-content">
        <div className="logo-section">
          <span className="logo">⚖️</span>
          <div>
            <h1 className="header-title">Judicial Aggregator</h1>
          </div>
        </div>
        
        {!isLoginPage && (
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link 
              href="/login"
              style={{
                padding: '0.75rem 1.5rem',
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                color: 'white',
                borderRadius: '12px',
                fontWeight: '600',
                textDecoration: 'none',
                transition: 'all 0.3s ease',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              🔐 Login
            </Link>
            <button
              onClick={() => {
                localStorage.removeItem('token')
                window.location.href = '/login'
              }}
              style={{
                padding: '0.75rem 1.5rem',
                background: '#ef4444',
                color: 'white',
                borderRadius: '12px',
                fontWeight: '600',
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
            >
              🚪 Sair
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
