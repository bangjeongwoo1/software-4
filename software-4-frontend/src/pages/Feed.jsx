import { useMemo, useState } from 'react'
import { items } from '../data/items.js'
import { currentUser } from '../data/user.js'
import ItemCard from '../components/ItemCard.jsx'

// 간단한 추천 점수 계산기 (더미)
function recommendScore(item, user) {
  let score = 0
  if (item.department === user.department || item.department === '전체') score += 3
  if (item.targetGrade.includes(user.grade)) score += 2
  if (item.minGpa <= user.gpa) score += 1
  const interestHit = item.interest.filter((i) => user.interests.includes(i)).length
  score += interestHit * 2
  return score
}

export default function Feed() {
  const [tab, setTab] = useState('recommend') // 'recommend' | 'views'

  const recommendList = useMemo(
    () =>
      [...items]
        .map((it) => ({ ...it, _score: recommendScore(it, currentUser) }))
        .sort((a, b) => b._score - a._score)
        .slice(0, 8),
    []
  )

  const viewsList = useMemo(
    () => [...items].sort((a, b) => b.views - a.views).slice(0, 8),
    []
  )

  const list = tab === 'recommend' ? recommendList : viewsList

  return (
    <div>
      <div className="page-header">
        <h1>피드</h1>
        <p>
          {currentUser.name}님의 정보({currentUser.department} {currentUser.grade}학년 ·
          평점 {currentUser.gpa})에 기반한 맞춤 피드입니다.
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
          조회수 기반 피드
        </button>
      </div>

      {tab === 'recommend' && (
        <div className="card mb-4" style={{ background: 'var(--color-primary-soft)', borderColor: '#c5d6ed' }}>
          <strong>추천 로직 (요약)</strong>
          <ul className="text-secondary" style={{ fontSize: 13, marginTop: 6, marginBottom: 0 }}>
            <li>학과 일치 +3 / 학년 해당 +2 / 평점 충족 +1</li>
            <li>관심 분야 매치 항목당 +2</li>
            <li>점수 내림차순으로 상위 8건 노출</li>
          </ul>
        </div>
      )}

      <div className="list-grid">
        {list.map((it) => (
          <ItemCard key={it.id} item={it} />
        ))}
      </div>
    </div>
  )
}
