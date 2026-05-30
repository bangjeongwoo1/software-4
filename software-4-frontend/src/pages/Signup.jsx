import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { api } from '../lib/api.js'
import { interests as INTEREST_OPTIONS } from '../data/items.js'

export default function Signup() {
  const navigate = useNavigate()
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')
  const [pwConfirm, setPwConfirm] = useState('')
  const [name, setName] = useState('')
  const [college, setCollege] = useState('IT대학')
  const [department, setDepartment] = useState('컴퓨터공학과')
  const [grade, setGrade] = useState(3)
  const [interests, setInterests] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const toggleInterest = (interest) => {
    setInterests((prev) =>
      prev.includes(interest)
        ? prev.filter((i) => i !== interest)
        : [...prev, interest]
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!id || id.length !== 9 || isNaN(Number(id))) {
      setError('올바른 9자리 학번을 입력해 주세요.')
      return
    }
    if (pw.length < 8) {
      setError('비밀번호는 8자리 이상이어야 합니다.')
      return
    }
    if (pw !== pwConfirm) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }
    if (!name.trim()) {
      setError('이름을 입력해 주세요.')
      return
    }
    if (!college.trim()) {
      setError('단과대학을 입력해 주세요.')
      return
    }
    if (!department.trim()) {
      setError('학과를 입력해 주세요.')
      return
    }

    try {
      setLoading(true)
      setError('')

      const email = `${id}@student.kangwon.ac.kr`

      await api.signup({
        email,
        password: pw,
        name,
        student_id: id,
        college,
        department,
        grade: Number(grade),
        interests,
      })

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
      <div className="auth-card" style={{ maxWidth: 480 }}>
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
            <label className="form-label" htmlFor="id">학번 (9자리)</label>
            <input
              id="id"
              type="text"
              className="form-control"
              placeholder="예: 202012345"
              value={id}
              onChange={(e) => setId(e.target.value)}
              autoFocus
            />
          </div>

          <div className="row">
            <div className="col">
              <div className="form-group">
                <label className="form-label" htmlFor="pw">비밀번호</label>
                <input
                  id="pw"
                  type="password"
                  className="form-control"
                  placeholder="8자리 이상 입력"
                  value={pw}
                  onChange={(e) => setPw(e.target.value)}
                />
              </div>
            </div>
            <div className="col">
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
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="name">이름</label>
            <input
              id="name"
              type="text"
              className="form-control"
              placeholder="예: 홍길동"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="row">
            <div className="col">
              <div className="form-group">
                <label className="form-label" htmlFor="college">단과대학</label>
                <input
                  id="college"
                  type="text"
                  className="form-control"
                  placeholder="예: IT대학"
                  value={college}
                  onChange={(e) => setCollege(e.target.value)}
                />
              </div>
            </div>
            <div className="col">
              <div className="form-group">
                <label className="form-label" htmlFor="department">학과</label>
                <input
                  id="department"
                  type="text"
                  className="form-control"
                  placeholder="예: 컴퓨터공학과"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="grade">학년</label>
            <select
              id="grade"
              className="form-control"
              value={grade}
              onChange={(e) => setGrade(Number(e.target.value))}
            >
              {[1, 2, 3, 4, 5, 6].map((g) => (
                <option key={g} value={g}>{g}학년</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">관심 분야</label>
            <div className="filter-bar" style={{ border: 'none', padding: 0, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {INTEREST_OPTIONS.map((it) => (
                <button
                  type="button"
                  key={it}
                  className={'filter-chip ' + (interests.includes(it) ? 'active' : '')}
                  onClick={() => toggleInterest(it)}
                  style={{ margin: 0 }}
                >
                  {it}
                </button>
              ))}
            </div>
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
