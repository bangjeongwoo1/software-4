import { useState } from 'react'
import { items } from '../data/items.js'

export default function AdminNotifications() {
  const [channel, setChannel] = useState('email') // email | sms | push
  const [target, setTarget] = useState('all') // all | scholarship | contest | dept
  const [department, setDepartment] = useState('소프트웨어학과')
  const [linkedItem, setLinkedItem] = useState('')
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')

  const [sentLog, setSentLog] = useState([
    { id: 1, time: '2026-04-29 09:12', channel: 'email', title: '국가장학금 1차 신청 안내', count: 1245 },
    { id: 2, time: '2026-04-28 17:30', channel: 'sms', title: 'AI 해커톤 마감 임박', count: 318 },
  ])

  const handleSend = (e) => {
    e.preventDefault()
    if (!title || !body) return alert('제목과 내용을 입력해 주세요.')
    const dummyCount = Math.floor(Math.random() * 1500) + 100
    setSentLog((log) => [
      {
        id: Date.now(),
        time: new Date().toLocaleString('ko-KR'),
        channel,
        title,
        count: dummyCount,
      },
      ...log,
    ])
    setTitle('')
    setBody('')
    alert(`${dummyCount}명에게 ${channel.toUpperCase()} 발송 완료 (더미)`)
  }

  return (
    <div>
      <div className="page-header">
        <h1>알림 전송 (관리자)</h1>
        <p>학생 그룹 또는 관심 공고 기준으로 알림을 발송합니다.</p>
      </div>

      <div className="row">
        <div className="col">
          <div className="card">
            <div className="card__title">
              <h3>새 알림 작성</h3>
            </div>

            <form onSubmit={handleSend}>
              <div className="form-group">
                <label className="form-label">발송 채널</label>
                <div className="filter-bar" style={{ border: 'none', padding: 0 }}>
                  {['email', 'sms', 'push'].map((c) => (
                    <button
                      type="button"
                      key={c}
                      className={'filter-chip ' + (channel === c ? 'active' : '')}
                      onClick={() => setChannel(c)}
                    >
                      {c.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">대상 그룹</label>
                <select
                  className="form-control"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                >
                  <option value="all">전체 학생</option>
                  <option value="scholarship">장학 관심 학생</option>
                  <option value="contest">대회 관심 학생</option>
                  <option value="dept">특정 학과</option>
                </select>
              </div>

              {target === 'dept' && (
                <div className="form-group">
                  <label className="form-label">학과</label>
                  <select
                    className="form-control"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                  >
                    <option>소프트웨어학과</option>
                    <option>공과대학</option>
                  </select>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">연결할 공고 (선택)</label>
                <select
                  className="form-control"
                  value={linkedItem}
                  onChange={(e) => setLinkedItem(e.target.value)}
                >
                  <option value="">선택 안 함</option>
                  {items.map((it) => (
                    <option key={it.id} value={it.id}>
                      [{it.type === 'contest' ? '대회' : '장학'}] {it.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">제목</label>
                <input
                  className="form-control"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="예: 국가장학금 신청 마감 D-3"
                />
              </div>

              <div className="form-group">
                <label className="form-label">내용</label>
                <textarea
                  className="form-control"
                  rows={4}
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder="발송할 알림 본문을 입력하세요."
                />
              </div>

              <div className="flex justify-between items-center mt-3">
                <span className="text-muted" style={{ fontSize: 13 }}>
                  ⚠ 발송 후 취소 불가
                </span>
                <button className="btn btn-primary" type="submit">
                  발송하기
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* 발송 로그 */}
        <div className="col" style={{ maxWidth: 380, flex: '0 0 380px' }}>
          <div className="card">
            <div className="card__title">
              <h3>최근 발송 이력</h3>
            </div>
            {sentLog.length === 0 ? (
              <div className="empty-state">발송 이력이 없습니다.</div>
            ) : (
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {sentLog.map((log) => (
                  <li
                    key={log.id}
                    style={{
                      padding: '10px 0',
                      borderBottom: '1px solid var(--color-border)',
                    }}
                  >
                    <div className="flex justify-between items-center">
                      <span className="badge badge-muted">{log.channel.toUpperCase()}</span>
                      <span className="text-muted" style={{ fontSize: 12 }}>
                        {log.time}
                      </span>
                    </div>
                    <div style={{ fontWeight: 500, marginTop: 4 }}>{log.title}</div>
                    <div className="text-secondary" style={{ fontSize: 13 }}>
                      {log.count.toLocaleString()}명에게 발송
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
