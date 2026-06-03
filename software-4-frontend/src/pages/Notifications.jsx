import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api.js'

export default function Notifications() {
  const [list, setList] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [userProfile, setUserProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchNotis = async () => {
    try {
      const res = await api.getNotifications({ page: 1, size: 50 })
      setList(res.items || [])
      setUnreadCount(res.unread_count || 0)
    } catch (err) {
      console.error('Error fetching notifications:', err)
      setError(err)
    }
  }

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true)
        const user = await api.getMe()
        setUserProfile(user)
        await fetchNotis()
        setLoading(false)
      } catch (err) {
        console.error(err)
        setError(err)
        setLoading(false)
      }
    }
    init()
  }, [])

  const markRead = async (id) => {
    try {
      await api.readNotification(id)
      await fetchNotis()
    } catch (err) {
      console.error('Error marking notification as read:', err)
    }
  }

  const markAllRead = async () => {
    try {
      const unreadList = list.filter((n) => !n.is_read)
      await Promise.all(unreadList.map((n) => api.readNotification(n.id)))
      await fetchNotis()
    } catch (err) {
      console.error('Error marking all as read:', err)
    }
  }

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}>알림을 불러오는 중...</div>

  if (error) {
    return (
      <div className="card">
        <div className="empty-state">
          알림을 불러오지 못했습니다.
          <div className="text-muted mt-3">{error.message}</div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h1>알림</h1>
        <p>관심 공고의 마감 임박, 신규 공고 등록 등을 받아볼 수 있습니다.</p>
      </div>

      <div className="row">
        {/* 알림 수신 설정 (더미/로컬 상태 유지) */}
        <div className="col" style={{ maxWidth: 360, flex: '0 0 360px' }}>
          <div className="card">
            <div className="card__title">
              <h3>희망 수신 방식 (시뮬레이션)</h3>
            </div>

            <div className="option-row">
              <div>
                <div className="option-row__label">이메일</div>
                <div className="option-row__hint">{userProfile?.email || '학번@student.kangwon.ac.kr'}</div>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  defaultChecked={true}
                />
                <span className="switch__slider" />
              </label>
            </div>

            <div className="option-row">
              <div>
                <div className="option-row__label">SMS</div>
                <div className="option-row__hint">휴대폰 웹 알림</div>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  defaultChecked={false}
                />
                <span className="switch__slider" />
              </label>
            </div>

            <div className="option-row">
              <div>
                <div className="option-row__label">브라우저 푸시</div>
                <div className="option-row__hint">PC·모바일 웹 알림</div>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  defaultChecked={true}
                />
                <span className="switch__slider" />
              </label>
            </div>

            <hr className="divider" />

            <div className="form-group">
              <label className="form-label">마감 임박 알림 (며칠 전)</label>
              <select
                className="form-control"
                defaultValue={3}
              >
                {[1, 3, 7, 14].map((d) => (
                  <option key={d} value={d}>{d}일 전</option>
                ))}
              </select>
            </div>

            <button className="btn btn-primary btn-block" onClick={() => alert('수신 설정이 저장되었습니다.')}>설정 저장</button>
          </div>
        </div>

        {/* 알림 목록 */}
        <div className="col">
          <div className="card">
            <div className="card__title">
              <h3>
                알림 목록{' '}
                {unreadCount > 0 && (
                  <span className="badge badge-accent" style={{ marginLeft: 6 }}>
                    {unreadCount} 신규
                  </span>
                )}
              </h3>
              <button
                className="btn btn-ghost btn-sm"
                onClick={markAllRead}
                disabled={unreadCount === 0}
              >
                모두 읽음 처리
              </button>
            </div>

            <div className="notification-list">
              {list.length === 0 ? (
                <div className="empty-state">알림이 없습니다.</div>
              ) : (
                list.map((n) => {
                  // link_url이 '/scholarships/101' 형태이면 '/detail/s-101' 형식으로 프론트 라우트 매핑
                  let linkTo = '/list'
                  if (n.link_url) {
                    if (n.link_url.includes('scholarship')) {
                      const match = n.link_url.match(/\d+/)
                      if (match) linkTo = `/detail/s-${match[0]}`
                    } else if (n.link_url.includes('contest')) {
                      const match = n.link_url.match(/\d+/)
                      if (match) linkTo = `/detail/c-${match[0]}`
                    }
                  }

                  return (
                    <Link
                      key={n.id}
                      to={linkTo}
                      onClick={() => markRead(n.id)}
                      className={'notification-item' + (!n.is_read ? ' unread' : '')}
                      style={{ textDecoration: 'none', color: 'inherit' }}
                    >
                      {!n.is_read && <div className="notification-item__dot" />}
                      <div className="notification-item__body">
                        <div className="notification-item__title">{n.title}</div>
                        <div className="text-secondary" style={{ fontSize: 13 }}>
                          {n.message}
                        </div>
                      </div>
                      <div className="notification-item__time">
                        {new Date(n.created_at).toLocaleDateString('ko-KR')}
                      </div>
                    </Link>
                  )
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
