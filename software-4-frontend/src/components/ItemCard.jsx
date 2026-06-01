import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { isBookmarked, toggleBookmark } from '../lib/bookmark.js'

export default function ItemCard({ item, onBookmarkChange }) {
  const isContest = item.type === 'contest'
  const [starred, setStarred] = useState(false)

  useEffect(() => {
    setStarred(isBookmarked(item.id))
  }, [item.id])

  const handleStarClick = (e) => {
    e.preventDefault()
    e.stopPropagation()
    toggleBookmark(item.id)
    setStarred(!starred)
    if (onBookmarkChange) {
      onBookmarkChange(item.id, !starred)
    }
  }

  return (
    <Link to={`/detail/${item.id}`} className="item-card">
      <div className="flex items-center justify-between">
        <span className="item-card__source">{item.source}</span>
        <div className="flex items-center gap-2">
          <button
            onClick={handleStarClick}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: 18,
              padding: '2px 4px',
              color: starred ? '#ffb800' : '#ccc',
              transition: 'transform 0.1s ease',
              lineHeight: 1,
            }}
            title={starred ? '북마크 해제' : '북마크 등록'}
          >
            ★
          </button>
          <span className={isContest ? 'badge badge-accent' : 'badge'}>
            {isContest ? '대회' : '장학'}
          </span>
        </div>
      </div>
      <div className="item-card__title">{item.title}</div>
      <div className="text-secondary" style={{ fontSize: 13, lineHeight: 1.5 }}>
        {item.summary}
      </div>
      <div className="item-card__meta">
        {item.tags.slice(0, 3).map((t) => (
          <span key={t} className="badge badge-muted">
            #{t}
          </span>
        ))}
      </div>
      <div className="flex justify-between items-center" style={{ marginTop: 4 }}>
        <span className="item-card__deadline">마감 {item.deadline}</span>
        <span className="text-muted" style={{ fontSize: 12 }}>
          조회 {item.views.toLocaleString()}
        </span>
      </div>
    </Link>
  )
}
