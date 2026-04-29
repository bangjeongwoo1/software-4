import { useState } from 'react'
import { Link } from 'react-router-dom'
import { notifications as initialNotis } from '../data/notifications.js'
import { currentUser } from '../data/user.js'

export default function Notifications() {
  const [list, setList] = useState(initialNotis)
  const [prefs, setPrefs] = useState(currentUser.notificationPrefs)

  const togglePref = (key) =>
    setPrefs((p) => ({ ...p, [key]: !p[key] }))

  const markRead = (id) =>
    setList((l) => l.map((n) => (n.id === id ? { ...n, unread: false } : n)))

  const markAllRead = () =>
    setList((l) => l.map((n) => ({ ...n, unread: false })))

  const unreadCount = list.filter((n) => n.unread).length

  return (
    <div>
      <div className="page-header">
        <h1>알림</h1>
        <p>관심 공고의 마감 임박, 신규 공고 등록 등을 받아볼 수 있습니다.</p>
      </div>

      <div className="row">
        {/* 알림 수신 설정 */}
        <div className="col" style={{ maxWidth: 360, flex: '0 0 360px' }}>
          <div className="card">
            <div className="card__title">
              <h3>희망 수신 방식</h3>
            </div>

            <div className="option-row">
              <div>
                <div className="option-row__label">이메일</div>
                <div className="option-row__hint">{currentUser.email}</div>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={prefs.email}
                  onChange={() => togglePref('email')}
                />
                <span className="switch__slider" />
              </label>
            </div>

            <div className="option-row">
              <div>
                <div className="option-row__label">SMS</div>
                <div className="option-row__hint">{currentUser.phone}</div>
              </div>
              <label className="switch">
                <input
                  type="checkbox"
                  checked={prefs.sms}
                  onChange={() => togglePref('sms')}
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
                  checked={prefs.push}
                  onChange={() => togglePref('push')}
                />
                <span className="switch__slider" />
              </label>
            </div>

            <hr className="divider" />

            <div className="form-group">
              <label className="form-label">마감 임박 알림 (며칠 전)</label>
              <select
                className="form-control"
                value={prefs.deadlineReminderDays}
                onChange={(e) =>
                  setPrefs((p) => ({ ...p, deadlineReminderDays: Number(e.target.value) }))
                }
              >
                {[1, 3, 7, 14].map((d) => (
                  <option key={d} value={d}>{d}일 전</option>
                ))}
              </select>
            </div>

            <button className="btn btn-primary btn-block">설정 저장</button>
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
                list.map((n) => (
                  <Link
                    key={n.id}
                    to={`/detail/${n.relatedId}`}
                    onClick={() => markRead(n.id)}
                    className={'notification-item' + (n.unread ? ' unread' : '')}
                    style={{ textDecoration: 'none', color: 'inherit' }}
                  >
                    {n.unread && <div className="notification-item__dot" />}
                    <div className="notification-item__body">
                      <div className="notification-item__title">{n.title}</div>
                      <div className="text-secondary" style={{ fontSize: 13 }}>
                        {n.body}
                      </div>
                    </div>
                    <div className="notification-item__time">{n.time}</div>
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
