import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchItems } from '../data/itemsApi.js'
import ItemCard from '../components/ItemCard.jsx'
import { parseRobustDate } from '../lib/dateUtils.js'

export default function ItemList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialType = searchParams.get('type') || 'all'

  const [type, setType] = useState(initialType)
  const [source, setSource] = useState('all')
  const [keyword, setKeyword] = useState('')

  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchItems()
      .then(setItems)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  const sources = useMemo(() => {
    return Array.from(new Set(items.map((item) => item.source).filter(Boolean)))
  }, [items])


  const [onlyActive, setOnlyActive] = useState(true)

  const onChangeType = (next) => {
    setType(next)
    if (next === 'all') searchParams.delete('type')
    else searchParams.set('type', next)
    setSearchParams(searchParams)
  }

  const filtered = useMemo(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    return items.filter((it) => {
      if (type !== 'all' && it.type !== type) return false
      if (source !== 'all' && it.source !== source) return false
      if (keyword && !it.title.toLowerCase().includes(keyword.toLowerCase())) return false
      
      if (onlyActive && it.deadline) {
        const deadlineDate = parseRobustDate(it.deadline)
        if (deadlineDate && deadlineDate < today) return false
      }
      return true
    })
  }, [items, type, source, keyword, onlyActive])

  if (loading) {
    return (
      <div className="card">
        <div className="empty-state">목록을 불러오는 중입니다.</div>
      </div>
    )
  }

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
        <h1>장학·대회 리스트</h1>
        <p>학교 홈페이지 / 한국장학재단 / 교내 / 콘테스트 코리아의 정보를 한곳에서.</p>
      </div>

      {/* 타입 탭 */}
      <div className="tabs">
        <button
          className={'tab ' + (type === 'all' ? 'active' : '')}
          onClick={() => onChangeType('all')}
        >
          전체
        </button>
        <button
          className={'tab ' + (type === 'scholarship' ? 'active' : '')}
          onClick={() => onChangeType('scholarship')}
        >
          장학
        </button>
        <button
          className={'tab ' + (type === 'contest' ? 'active' : '')}
          onClick={() => onChangeType('contest')}
        >
          대회
        </button>
      </div>

      {/* 출처 필터 + 검색 */}
      <div className="filter-bar" style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px 12px' }}>
        <button
          className={'filter-chip ' + (source === 'all' ? 'active' : '')}
          onClick={() => setSource('all')}
          style={{ margin: 0 }}
        >
          전체 출처
        </button>
        {sources.map((s) => (
          <button
            key={s}
            className={'filter-chip ' + (source === s ? 'active' : '')}
            onClick={() => setSource(s)}
            style={{ margin: 0 }}
          >
            {s}
          </button>
        ))}

        <label 
          className="text-secondary" 
          style={{ 
            fontSize: 13, 
            cursor: 'pointer', 
            display: 'inline-flex', 
            alignItems: 'center', 
            gap: 6,
            marginLeft: 12,
            userSelect: 'none'
          }}
        >
          <input
            type="checkbox"
            checked={onlyActive}
            onChange={(e) => setOnlyActive(e.target.checked)}
            style={{ cursor: 'pointer', width: 15, height: 15 }}
          />
          진행 중인 공고만 보기
        </label>

        <input
          type="text"
          className="form-control"
          style={{ marginLeft: 'auto', maxWidth: 240 }}
          placeholder="제목 검색"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
      </div>

      <div className="text-secondary mb-3" style={{ fontSize: 13 }}>
        {filtered.length}건이 조회되었습니다.
      </div>

      {filtered.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            조건에 맞는 공고가 없습니다. 필터를 조정해 보세요.
          </div>
        </div>
      ) : (
        <div className="list-grid">
          {filtered.map((it) => (
            <ItemCard key={it.id} item={it} />
          ))}
        </div>
      )}
    </div>
  )
}
