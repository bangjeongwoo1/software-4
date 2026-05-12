import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { supabase } from '../lib/supabase.js'

export default function Login() {
  const navigate = useNavigate()
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!id || !pw) {
      setError('아이디와 비밀번호를 입력해 주세요.')
      return
    }

    try {
      setLoading(true)
      setError('')
      const email = `${id}@student.kangwon.ac.kr`

      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password: pw,
      })

      if (authError) throw authError

      navigate('/list')
    } catch (err) {
      console.error(err)
      setError('아이디 또는 비밀번호가 올바르지 않습니다.')
    } finally {
      setLoading(false)
    }
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
              placeholder="예: 202113575"
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

          <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: 8 }} disabled={loading}>
            {loading ? '로그인 중...' : '로그인'}
          </button>

          <div className="text-center mt-4" style={{ fontSize: 13 }}>
            <span className="text-muted">아직 계정이 없으신가요? </span>
            <Link to="/signup" style={{ color: 'var(--color-primary)', fontWeight: 'bold', textDecoration: 'none' }}>
              회원가입
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
