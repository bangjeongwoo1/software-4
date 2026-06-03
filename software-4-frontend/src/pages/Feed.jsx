import { useEffect, useState } from 'react'
import { api } from '../lib/api.js'
import { normalizeScholarship, normalizeContest } from '../data/itemsApi.js'
import ItemCard from '../components/ItemCard.jsx'
import { parseRobustDate } from '../lib/dateUtils.js'

export default function Feed() {
  const [tab, setTab] = useState('recommend') // 'recommend' | 'views'
  const [recommendList, setRecommendList] = useState([])
  const [viewsList, setViewsList] = useState([])
  const [userProfile, setUserProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const user = await api.getMe()
        setUserProfile(user)

        const today = new Date()
        today.setHours(0, 0, 0, 0)

        // 1. 추천 목록 로드
        const sRecs = await api.getRecommendations('scholarship', 6)
        const cRecs = await api.getRecommendations('contest', 6)
        
        const normalizedRecs = [
          ...(sRecs?.items || []).map(item => ({
            ...normalizeScholarship(item.scholarship),
            matchScore: item.match_score,
            reasons: item.reasons
          })),
          ...(cRecs?.items || []).map(item => ({
            ...normalizeContest(item.contest),
            matchScore: item.match_score,
            reasons: item.reasons
          }))
        ].filter(it => {
          if (it.deadline) {
            const d = parseRobustDate(it.deadline)
            if (d && d < today) return false
          }
          return true
        }).sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0))

        setRecommendList(normalizedRecs)

        // 2. 조회수(인기) 목록 로드
        const sRes = await api.getScholarships({ page: 1, size: 6, sort: 'latest' })
        const cRes = await api.getContests({ page: 1, size: 6, sort: 'latest' })
        const normalizedViews = [
          ...(sRes?.items || []).map(normalizeScholarship),
          ...(cRes?.items || []).map(normalizeContest)
        ].filter(it => {
          if (it.deadline) {
            const d = parseRobustDate(it.deadline)
            if (d && d < today) return false
          }
          return true
        }).sort((a, b) => b.views - a.views)

        setViewsList(normalizedViews)
        setLoading(false)
      } catch (err) {
        console.error(err)
        setError(err)
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}>피드를 불러오는 중...</div>

  if (error) {
    return (
      <div className="card">
        <div className="empty-state">
          피드를 로드하지 못했습니다.
          <div className="text-muted mt-3">{error.message}</div>
        </div>
      </div>
    )
  }

  const list = tab === 'recommend' ? recommendList : viewsList

  return (
    <div>
      <div className="page-header">
        <h1>피드</h1>
        <p>
          {userProfile?.name}님의 정보({userProfile?.department} {userProfile?.grade}학년)에 기반한 맞춤 피드입니다.
        </p>
      </div>

      <div className="tabs">
        <button
          className={'tab ' + (tab === 'recommend' ? 'active' : '')}
          onClick={() => setTab('recommend')}
        >
          추천 기반 피드
        </button>
        <button
          className={'tab ' + (tab === 'views' ? 'active' : '')}
          onClick={() => setTab('views')}
        >
          최신 인기 피드
        </button>
      </div>

      {tab === 'recommend' && (
        <div className="card mb-4" style={{ background: 'var(--color-primary-soft)', borderColor: '#c5d6ed' }}>
          <strong>추천 가중치 및 추천 사유</strong>
          <ul className="text-secondary" style={{ fontSize: 13, marginTop: 6, marginBottom: 0 }}>
            <li>학적 매칭(학년/학과), 관심사 조건 충족율 반영</li>
            <li>아래 각 공고 카드 하단에서 백엔드가 분석한 추천 사유를 확인할 수 있습니다.</li>
          </ul>
        </div>
      )}

      {list.length === 0 ? (
        <div className="card">
          <div className="empty-state">해당하는 추천 공고가 아직 없습니다.</div>
        </div>
      ) : (
        <div className="list-grid">
          {list.map((it) => (
            <div key={it.id} className="feed-item-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <ItemCard item={it} />
              {tab === 'recommend' && it.reasons && it.reasons.length > 0 && (
                <div className="recommend-reasons-badge" style={{
                  padding: '8px 12px',
                  background: '#f0f4f9',
                  borderRadius: 6,
                  fontSize: 12,
                  borderLeft: '3px solid var(--color-primary)',
                  marginTop: -4,
                  display: 'flex',
                  gap: 6,
                  alignItems: 'center',
                  flexWrap: 'wrap'
                }}>
                  <span style={{ fontWeight: 'bold', color: 'var(--color-primary)' }}>추천 사유:</span>
                  {it.reasons.map((r, i) => (
                    <span key={i} style={{ background: '#e1e8f0', padding: '2px 6px', borderRadius: 4, color: '#333' }}>
                      {r}
                    </span>
                  ))}
                  {it.matchScore !== undefined && (
                    <span style={{ marginLeft: 'auto', fontWeight: 'bold', color: '#666' }}>
                      일치도: {(it.matchScore * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
