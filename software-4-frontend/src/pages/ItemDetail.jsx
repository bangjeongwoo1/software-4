import { useParams, Link } from 'react-router-dom'
import { items } from '../data/items.js'

export default function ItemDetail() {
  const { id } = useParams()
  const item = items.find((it) => it.id === id)

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
            <ul>
              <li>지원 금액 / 혜택: <strong>{item.amount}</strong></li>
              <li>대상 학과: {item.department}</li>
              <li>대상 학년: {item.targetGrade.join(', ')}학년</li>
              {item.minGpa > 0 && <li>최소 평점: {item.minGpa}</li>}
              <li>마감일: <strong>{item.deadline}</strong></li>
            </ul>

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
          <button className="btn btn-secondary btn-block mt-2">
            관심 공고로 저장
          </button>
        </aside>
      </div>
    </div>
  )
}
