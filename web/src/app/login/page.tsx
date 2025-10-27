'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Usuário ou senha incorretos');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('username', username);
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="login-container">
        <div className="login-card">
          
          <div className="logo-section">
            <div className="logo-icon">⚖️</div>
            <h1 className="title">Judicial Aggregator</h1>
            <p className="subtitle">Sistema de agregação de processos judiciais</p>
          </div>

          <form onSubmit={handleLogin} className="login-form">
            
            {error && (
              <div className="error-box">
                <span className="error-icon">⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <div className="form-group">
              <label>Usuário</label>
              <div className="input-wrapper">
                <span className="input-icon">👤</span>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Digite seu usuário"
                  required
                  autoFocus
                />
              </div>
            </div>

            <div className="form-group">
              <label>Senha</label>
              <div className="input-wrapper">
                <span className="input-icon">🔒</span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Digite sua senha"
                  required
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="submit-btn">
              {loading ? '⏳ Entrando...' : 'Entrar no Sistema'}
            </button>
          </form>

          <div className="users-info">
            <p>
              <strong>👥 Usuários cadastrados:</strong><br />
              momachado • adrianoduarte • raqueldavico
            </p>
          </div>

          <div className="footer">
            © 2025 Judicial Aggregator • Sistema Interno
          </div>
        </div>
      </div>

      <style jsx>{`
        .login-container {
          min-height: 100vh;
          background: linear-gradient(135deg, #1e293b 0%, #3b82f6 50%, #1e293b 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .login-card {
          background: rgba(255, 255, 255, 0.98);
          backdrop-filter: blur(20px);
          border-radius: 24px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
          width: 100%;
          max-width: 440px;
          padding: 48px 40px;
          border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .logo-section {
          text-align: center;
          margin-bottom: 40px;
        }

        .logo-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 80px;
          height: 80px;
          background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
          border-radius: 20px;
          font-size: 40px;
          margin-bottom: 20px;
          box-shadow: 0 10px 30px rgba(59, 130, 246, 0.4);
        }

        .title {
          font-size: 32px;
          font-weight: 700;
          color: #1e293b;
          margin: 0 0 8px 0;
          background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .subtitle {
          color: #64748b;
          font-size: 14px;
          margin: 0;
        }

        .login-form {
          margin-bottom: 32px;
        }

        .error-box {
          background: #fef2f2;
          border-left: 4px solid #ef4444;
          color: #991b1b;
          padding: 16px;
          border-radius: 12px;
          margin-bottom: 24px;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 500;
        }

        .error-icon {
          font-size: 20px;
        }

        .form-group {
          margin-bottom: 24px;
        }

        .form-group label {
          display: block;
          font-size: 14px;
          font-weight: 600;
          color: #334155;
          margin-bottom: 8px;
        }

        .input-wrapper {
          position: relative;
        }

        .input-icon {
          position: absolute;
          left: 16px;
          top: 50%;
          transform: translateY(-50%);
          font-size: 20px;
          pointer-events: none;
        }

        .input-wrapper input {
          width: 100%;
          padding: 16px 16px 16px 52px;
          background: #f8fafc;
          border: 2px solid #e2e8f0;
          border-radius: 12px;
          font-size: 15px;
          color: #1e293b;
          transition: all 0.2s;
          box-sizing: border-box;
        }

        .input-wrapper input:focus {
          outline: none;
          border-color: #3b82f6;
          background: white;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .input-wrapper input::placeholder {
          color: #94a3b8;
        }

        .submit-btn {
          width: 100%;
          background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
          color: white;
          font-weight: 600;
          font-size: 16px;
          padding: 18px 24px;
          border: none;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
          box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3);
          margin-top: 32px;
        }

        .submit-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 15px 35px rgba(59, 130, 246, 0.4);
        }

        .submit-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .users-info {
          background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%);
          border: 1px solid #dbeafe;
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 24px;
        }

        .users-info p {
          text-align: center;
          font-size: 13px;
          color: #475569;
          margin: 0;
          line-height: 1.6;
        }

        .users-info strong {
          color: #1e293b;
        }

        .footer {
          text-align: center;
          font-size: 11px;
          color: #94a3b8;
        }
      `}</style>
    </>
  );
}
