import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const navigate = useNavigate()
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!id || !pw) {
      setError('아이디와 비밀번호를 입력해 주세요.')
      return
    }
    // 더미 인증 — 실제 인증 연결 시 API 호출
    navigate('/list')
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-brand">
          <div
            className="app-header__brand-mark"
            style={{ width: 48, height: 48, fontSize: 18, margin: '0 auto 12px' }}
          >
            SC
          </div>
          <h1>장학·취업 정보 추천</h1>
          <p>학교 통합 계정으로 로그인</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="id">아이디 (학번)</label>
            <input
              id="id"
              type="text"
              className="form-control"
              placeholder="20XXXXXX"
              value={id}
              onChange={(e) => setId(e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="pw">비밀번호</label>
            <input
              id="pw"
              type="password"
              className="form-control"
              placeholder="비밀번호 입력"
              value={pw}
              onChange={(e) => setPw(e.target.value)}
            />
          </div>

          {error && (
            <div style={{ color: 'var(--color-danger)', fontSize: 13, marginBottom: 12 }}>
              {error}
            </div>
          )}

          <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: 8 }}>
            로그인
          </button>

          <div className="text-center text-muted mt-4" style={{ fontSize: 12 }}>
            계정 분실 시 학사지원팀 문의
          </div>
        </form>
      </div>
    </div>
  )
}
