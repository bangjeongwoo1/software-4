import { useEffect, useMemo, useState } from 'react'
import { fetchItems } from '../data/itemsApi.js'
import { api } from '../lib/api.js'
import ItemCard from '../components/ItemCard.jsx'

export default function Popular() {
  const [department, setDepartment] = useState('all')
  const [grade, setGrade] = useState('all')
  const [type, setType] = useState('all')
  const [items, setItems] = useState([])
  const [userProfile, setUserProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true)
        const allItems = await fetchItems()
        setItems(allItems)

        const user = await api.getMe()
        setUserProfile(user)
        setLoading(false)
      } catch (err) {
        console.error(err)
        setError(err)
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const filtered = useMemo(() => {
    return items
      .filter((it) => {
        if (type !== 'all' && it.type !== type) return false
        if (department !== 'all' && it.department !== department && it.department !== '전체 학과')
          return false
        if (grade !== 'all' && !it.targetGrade.includes(Number(grade))) return false
        return true
      })
      .sort((a, b) => b.views - a.views)
  }, [items, department, grade, type])

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}>인기 공고를 불러오는 중...</div>

  if (error) {
    return (
      <div className="card">
        <div className="empty-state">
          데이터를 불러오지 못했습니다.
          <div className="text-muted mt-3">{error.message}</div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1>인기 장학·대회</h1>
        <p>조회수 기반 인기 공고. 필터로 본인 조건에 맞춰볼 수 있습니다.</p>
      </div>

      <div className="filter-bar">
        <strong style={{ alignSelf: 'center', fontSize: 13, color: 'var(--color-text-secondary)' }}>
          필터
        </strong>

        <select
          className="form-control"
          style={{ maxWidth: 180 }}
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          <option value="all">전체 유형</option>
          <option value="scholarship">장학</option>
          <option value="contest">대회</option>
        </select>

        <select
          className="form-control"
          style={{ maxWidth: 180 }}
          value={department}
          onChange={(e) => setDepartment(e.target.value)}
        >
          <option value="all">전체 학과</option>
          <option value="소프트웨어학과">소프트웨어학과</option>
          <option value="컴퓨터공학과">컴퓨터공학과</option>
          <option value="공과대학">공과대학</option>
          <option value="IT대학">IT대학</option>
        </select>

        <select
          className="form-control"
          style={{ maxWidth: 140 }}
          value={grade}
          onChange={(e) => setGrade(e.target.value)}
        >
          <option value="all">전체 학년</option>
          {[1, 2, 3, 4, 5, 6].map((g) => (
            <option key={g} value={g}>{g}학년</option>
          ))}
        </select>

        <button
          className="btn btn-ghost btn-sm"
          style={{ marginLeft: 'auto' }}
          onClick={() => {
            if (userProfile) {
              setDepartment(userProfile.department || 'all')
              setGrade(userProfile.grade ? String(userProfile.grade) : 'all')
            } else {
              alert('로그인이 필요한 기능입니다.')
            }
          }}
        >
          내 조건으로 자동 설정
        </button>
      </div>

      <div className="list-grid">
        {filtered.map((it) => (
          <ItemCard key={it.id} item={it} />
        ))}
      </div>
    </div>
  )
}
