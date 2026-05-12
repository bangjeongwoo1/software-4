import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { supabase } from '../lib/supabase.js'

export default function Signup() {
  const navigate = useNavigate()
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')
  const [pwConfirm, setPwConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!id || id.length !== 9 || isNaN(Number(id))) {
      setError('올바른 9자리 학번을 입력해 주세요.')
      return
    }
    if (pw.length < 6) {
      setError('비밀번호는 6자리 이상이어야 합니다.')
      return
    }
    if (pw !== pwConfirm) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }

    try {
      setLoading(true)
      setError('')

      // 1. 학번을 이메일 형식으로 변환하여 Supabase Auth 회원가입
      const email = `${id}@student.kangwon.ac.kr`
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password: pw,
      })

      if (authError) {
        if (authError.message.includes('User already registered')) {
          throw new Error('이미 가입된 학번입니다.')
        }
        throw authError
      }

      // 2. public.user_account 테이블에 학번 데이터 저장
      // 비밀번호는 Supabase Auth가 안전하게 관리하므로, DB 스키마 충돌 방지용으로 더미 텍스트 삽입
      const { error: dbError } = await supabase
        .from('user_account')
        .insert([
          {
            student_id: id,
            password_hash: '[SUPABASE_AUTH_MANAGED]'
          }
        ])

      // 만약 user_account 삽입 중 에러가 발생해도 (이미 있는 학번 등), 일단 에러 캐치로 넘어감
      if (dbError && dbError.code !== '23505') {
        throw dbError
      }

      alert('회원가입이 완료되었습니다! 로그인해 주세요.')
      navigate('/login')

    } catch (err) {
      console.error(err)
      setError(err.message || '회원가입 중 오류가 발생했습니다.')
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
          <h1>회원가입</h1>
          <p>학교 통합 계정 생성</p>
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
              placeholder="6자리 이상 입력"
              value={pw}
              onChange={(e) => setPw(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="pwConfirm">비밀번호 확인</label>
            <input
              id="pwConfirm"
              type="password"
              className="form-control"
              placeholder="비밀번호 다시 입력"
              value={pwConfirm}
              onChange={(e) => setPwConfirm(e.target.value)}
            />
          </div>

          {error && (
            <div style={{ color: 'var(--color-danger)', fontSize: 13, marginBottom: 12 }}>
              {error}
            </div>
          )}

          <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: 8 }} disabled={loading}>
            {loading ? '가입 중...' : '회원가입 완료'}
          </button>

          <div className="text-center text-muted mt-4" style={{ fontSize: 13 }}>
            이미 계정이 있으신가요? <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 'bold', textDecoration: 'none' }}>로그인</Link>
          </div>
        </form>
      </div>
    </div>
  )
}
