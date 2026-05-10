import { useState, useEffect } from 'react'
import { supabase } from '../lib/supabase.js'
import { interests as INTEREST_OPTIONS } from '../data/items.js'

export default function MyPage() {
  const [studentId, setStudentId] = useState('')
  const [profile, setProfile] = useState({
    name: '', department: '', grade: 1, gpa: 0, email: '', phone: '', interests: []
  })
  const [history, setHistory] = useState([])
  const [savedAt, setSavedAt] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return
      
      const sid = user.email.split('@')[0]
      setStudentId(sid)

      const { data: pData } = await supabase.from('user_profile').select('*').eq('student_id', sid).single()
      const { data: iData } = await supabase.from('user_interest').select('interest_name').eq('student_id', sid)
      const { data: hData } = await supabase.from('user_competition').select('*').eq('student_id', sid).order('participated_at', { ascending: false })

      setProfile({
        name: pData?.name || '',
        department: pData?.department || '',
        grade: pData?.grade ? parseInt(pData.grade) : 1,
        gpa: pData?.gpa_prev || 0,
        email: pData?.email || user.email,
        phone: pData?.phone || '',
        interests: iData ? iData.map(i => i.interest_name) : []
      })
      
      if (hData) {
        setHistory(hData.map(h => ({
          id: h.competition_id, title: h.competition_name, date: h.participated_at, result: h.result || ''
        })))
      }
      setLoading(false)
    }
    fetchData()
  }, [])

  const update = (key, value) => setProfile((p) => ({ ...p, [key]: value }))

  const toggleInterest = (interest) => {
    setProfile((p) => {
      const has = p.interests.includes(interest)
      return {
        ...p,
        interests: has
          ? p.interests.filter((i) => i !== interest)
          : [...p.interests, interest],
      }
    })
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!studentId) return

    try {
      const { error: profileError } = await supabase.from('user_profile').upsert({
        student_id: studentId,
        name: profile.name,
        department: profile.department,
        grade: `${profile.grade}학년`,
        gpa_prev: profile.gpa,
        email: profile.email,
        phone: profile.phone,
        campus: '춘천',
        student_type: '재학생'
      })
      if (profileError) throw profileError

      const { error: intDelError } = await supabase.from('user_interest').delete().eq('student_id', studentId)
      if (intDelError) throw intDelError

      if (profile.interests.length > 0) {
        const interestInserts = profile.interests.map(i => ({ student_id: studentId, interest_name: i }))
        const { error: intInsError } = await supabase.from('user_interest').insert(interestInserts)
        if (intInsError) throw intInsError
      }

      const { error: compDelError } = await supabase.from('user_competition').delete().eq('student_id', studentId)
      if (compDelError) throw compDelError

      const validHistory = history.filter(h => h.title && h.date)
      if (validHistory.length > 0) {
        const historyInserts = validHistory.map(h => ({
          student_id: studentId,
          competition_name: h.title,
          participated_at: h.date,
          result: h.result
        }))
        const { error: compInsError } = await supabase.from('user_competition').insert(historyInserts)
        if (compInsError) throw compInsError
      }

      setSavedAt(new Date().toLocaleTimeString('ko-KR'))
      alert('저장되었습니다.')
    } catch (error) {
      console.error(error)
      alert(`저장 중 오류가 발생했습니다:\n${error.message || JSON.stringify(error)}`)
    }
  }

  const addHistory = () => {
    setHistory((h) => [
      ...h,
      { id: 'h-' + (h.length + 1), title: '', date: '', result: '' },
    ])
  }
  const updateHistory = (idx, key, value) => {
    setHistory((h) => h.map((item, i) => (i === idx ? { ...item, [key]: value } : item)))
  }
  const removeHistory = (idx) => {
    setHistory((h) => h.filter((_, i) => i !== idx))
  }

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}>데이터를 불러오는 중...</div>

  return (
    <div>
      <div className="page-header">
        <h1>마이 페이지</h1>
        <p>학생 정보를 입력하면 조건에 맞는 장학·대회를 추천받을 수 있습니다.</p>
      </div>

      <form onSubmit={handleSave}>
        {/* 기본 정보 */}
        <div className="card">
          <div className="card__title">
            <h3>기본 정보</h3>
            <span className="text-muted" style={{ fontSize: 13 }}>
              프로필 정보를 입력해 주세요
            </span>
          </div>

          <div className="row">
            <div className="col">
              <div className="form-group">
                <label className="form-label">이름</label>
                <input className="form-control" value={profile.name} onChange={(e) => update('name', e.target.value)} />
              </div>
            </div>
            <div className="col">
              <div className="form-group">
                <label className="form-label">학과</label>
                <input className="form-control" value={profile.department} onChange={(e) => update('department', e.target.value)} />
              </div>
            </div>
          </div>

          <div className="row">
            <div className="col">
              <div className="form-group">
                <label className="form-label">학년</label>
                <select
                  className="form-control"
                  value={profile.grade}
                  onChange={(e) => update('grade', Number(e.target.value))}
                >
                  {[1, 2, 3, 4].map((g) => (
                    <option key={g} value={g}>{g}학년</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="col">
              <div className="form-group">
                <label className="form-label">평점 (GPA, 4.5 만점)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="4.5"
                  className="form-control"
                  value={profile.gpa}
                  onChange={(e) => update('gpa', parseFloat(e.target.value))}
                />
              </div>
            </div>
          </div>

          <div className="row">
            <div className="col">
              <div className="form-group">
                <label className="form-label">이메일</label>
                <input
                  type="email"
                  className="form-control"
                  value={profile.email}
                  onChange={(e) => update('email', e.target.value)}
                />
              </div>
            </div>
            <div className="col">
              <div className="form-group">
                <label className="form-label">휴대폰</label>
                <input
                  type="tel"
                  className="form-control"
                  value={profile.phone}
                  onChange={(e) => update('phone', e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>

        {/* 관심 분야 */}
        <div className="card">
          <div className="card__title">
            <h3>관심 분야</h3>
            <span className="text-muted" style={{ fontSize: 13 }}>
              추천 점수 가중치에 반영됩니다
            </span>
          </div>
          <div className="filter-bar" style={{ border: 'none', padding: 0 }}>
            {INTEREST_OPTIONS.map((it) => (
              <button
                type="button"
                key={it}
                className={'filter-chip ' + (profile.interests.includes(it) ? 'active' : '')}
                onClick={() => toggleInterest(it)}
              >
                {it}
              </button>
            ))}
          </div>
          <div className="form-help">선택한 항목 {profile.interests.length}개</div>
        </div>

        {/* 대회 참여 이력 */}
        <div className="card" id="history">
          <div className="card__title">
            <h3>대회 참여 이력</h3>
            <button type="button" className="btn btn-secondary btn-sm" onClick={addHistory}>
              + 이력 추가
            </button>
          </div>

          {history.length === 0 ? (
            <div className="empty-state">아직 등록된 대회 참여 이력이 없습니다.</div>
          ) : (
            history.map((h, idx) => (
              <div key={h.id} className="row" style={{ alignItems: 'flex-end' }}>
                <div className="col">
                  <div className="form-group">
                    <label className="form-label">대회명</label>
                    <input
                      className="form-control"
                      value={h.title}
                      placeholder="예: 교내 알고리즘 경진대회"
                      onChange={(e) => updateHistory(idx, 'title', e.target.value)}
                    />
                  </div>
                </div>
                <div className="col">
                  <div className="form-group">
                    <label className="form-label">참여일</label>
                    <input
                      type="date"
                      className="form-control"
                      value={h.date}
                      onChange={(e) => updateHistory(idx, 'date', e.target.value)}
                    />
                  </div>
                </div>
                <div className="col">
                  <div className="form-group">
                    <label className="form-label">결과</label>
                    <input
                      className="form-control"
                      value={h.result}
                      placeholder="예: 장려상 / 수료"
                      onChange={(e) => updateHistory(idx, 'result', e.target.value)}
                    />
                  </div>
                </div>
                <div style={{ marginBottom: 16 }}>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => removeHistory(idx)}
                  >
                    삭제
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="flex justify-between items-center mt-4">
          <span className="text-muted" style={{ fontSize: 13 }}>
            {savedAt ? `${savedAt}에 저장됨` : '아직 저장되지 않은 변경사항이 있을 수 있습니다.'}
          </span>
          <button type="submit" className="btn btn-primary">저장</button>
        </div>
      </form>
    </div>
  )
}
