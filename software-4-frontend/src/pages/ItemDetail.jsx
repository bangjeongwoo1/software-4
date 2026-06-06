import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchItemById } from '../data/itemsApi.js'
import { isBookmarked, toggleBookmark } from '../lib/bookmark.js'

export default function ItemDetail() {
  const { id } = useParams()
  const [item, setItem] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [starred, setStarred] = useState(false)

  useEffect(() => {
    fetchItemById(id)
      .then((data) => {
        setItem(data)
        if (data) {
          setStarred(isBookmarked(data.id))
        }
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [id])

  const handleStarToggle = () => {
    if (item) {
      toggleBookmark(item.id)
      setStarred(!starred)
    }
  }

  if (loading) {
    return (
      <div className="card">
        <div className="empty-state">공고를 불러오는 중입니다.</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div className="empty-state">
          데이터를 불러오지 못했습니다.
          <div className="text-muted mt-3">{error.message}</div>
          <div className="mt-3">
            <Link to="/list" className="btn btn-secondary btn-sm">
              리스트로 돌아가기
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (!item) {
    return (
      <div className="card">
        <div className="empty-state">
          해당 공고를 찾을 수 없습니다.
          <div className="mt-3">
            <Link to="/list" className="btn btn-secondary btn-sm">
              리스트로 돌아가기
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const isContest = item.type === 'contest'

  return (
    <div>
      <div className="page-header">
        <Link to="/list" className="text-muted" style={{ fontSize: 13 }}>
          ← 리스트로
        </Link>
        <div className="flex items-center gap-2 mt-2">
          <span className={isContest ? 'badge badge-accent' : 'badge'}>
            {isContest ? '대회' : '장학'}
          </span>
          <span className="text-muted" style={{ fontSize: 13 }}>{item.source}</span>
        </div>
        <h1 style={{ marginTop: 8 }}>{item.title}</h1>
      </div>

      <div className="detail-grid">
        <div>
          <div className="card">
            <h3>공고 요약</h3>
            <p>{item.summary}</p>

            <hr className="divider" />

            <h4>주요 정보</h4>

            {item.type === 'scholarship' ? (
              <ul>
                <li>지원 금액 / 혜택: <strong>{item.amount}</strong></li>
                <li>대상 캠퍼스: {item.campus}</li>
                <li>대상 학년: {item.targetGrade.length ? `${item.targetGrade.join(', ')}학년` : '-'}</li>
                {item.minGpa > 0 && <li>최소 평점: {item.minGpa}</li>}
                <li>마감일: <strong>{item.deadline}</strong></li>
              </ul>
            ) : (
              <ul>
                <li>참가 대상: {item.target || '-'}</li>
                <li>시상/혜택: {item.amount || '-'}</li>
                <li>분야: {item.mainField || '-'}</li>
                <li>접수 마감: {item.deadline || '-'}</li>
              </ul>
            )}

            <h4 className="mt-4">관련 태그</h4>
            <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
              {item.tags.map((t) => (
                <span key={t} className="badge badge-muted">#{t}</span>
              ))}
            </div>
          </div>
        </div>

        <aside>
          <div className="detail-meta">
            <div className="meta-row">
              <span className="meta-row__label">조회수</span>
              <span className="meta-row__value">{item.views.toLocaleString()}</span>
            </div>
            <div className="meta-row">
              <span className="meta-row__label">출처</span>
              <span className="meta-row__value">{item.source}</span>
            </div>
            <div className="meta-row">
              <span className="meta-row__label">유형</span>
              <span className="meta-row__value">{isContest ? '대회' : '장학'}</span>
            </div>
            <div className="meta-row">
              <span className="meta-row__label">마감</span>
              <span className="meta-row__value">{item.deadline}</span>
            </div>
          </div>

          <a
            href={item.externalUrl}
            target="_blank"
            rel="noreferrer"
            className="btn btn-primary btn-block mt-4"
          >
            {isContest ? '대회 페이지로 이동 ↗' : '장학 페이지로 이동 ↗'}
          </a>
          <button 
            className={`btn btn-block mt-2 ${starred ? 'btn-primary' : 'btn-secondary'}`}
            onClick={handleStarToggle}
          >
            {starred ? '★ 관심 공고 해제' : '☆ 관심 공고로 저장'}
          </button>
        </aside>
      </div>
    </div>
  )
}
