import { useState, useEffect } from 'react'
import { api } from '../lib/api.js'
import { interests as INTEREST_OPTIONS } from '../data/items.js'
import { getBookmarks } from '../lib/bookmark.js'
import { fetchItems } from '../data/itemsApi.js'
import ItemCard from '../components/ItemCard.jsx'

export default function MyPage() {
  const [studentId, setStudentId] = useState('')
  const [profile, setProfile] = useState({
    name: '', college: '', department: '', grade: 1, interests: []
  })
  const [passwords, setPasswords] = useState({
    current_password: '', new_password: '', new_password_confirm: ''
  })
  const [bookmarkedItems, setBookmarkedItems] = useState([])
  const [savedAt, setSavedAt] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const user = await api.getMe()
        if (user) {
          setStudentId(user.student_id)
          setProfile({
            name: user.name || '',
            college: user.college || '',
            department: user.department || '',
            grade: user.grade || 1,
            interests: user.interests || []
          })
        }

        // 북마크 목록 로드
        const allItems = await fetchItems()
        const bIds = getBookmarks()
        const bookmarked = allItems.filter(item => bIds.includes(item.id))
        setBookmarkedItems(bookmarked)

        setLoading(false)
      } catch (err) {
        console.error(err)
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleBookmarkChange = (itemId, isStarred) => {
    if (!isStarred) {
      setBookmarkedItems(prev => prev.filter(item => item.id !== itemId))
    }
  }

  const update = (key, value) => setProfile((p) => ({ ...p, [key]: value }))
  const updatePassword = (key, value) => setPasswords((p) => ({ ...p, [key]: value }))

  const toggleInterest = (interest) => {
    setProfile((p) => {
      const has = p.interests.includes(interest)
      return {
        ...p,
        interests: has
          ? p.interests.filter((i) => i !== interest)
          : [...p.interests, interest],
      }
    })
  }

  const handleSave = async (e) => {
    e.preventDefault()

    try {
      const updateData = {
        name: profile.name,
        college: profile.college,
        department: profile.department,
        grade: Number(profile.grade),
        interests: profile.interests,
      }

      if (passwords.new_password) {
        if (passwords.new_password !== passwords.new_password_confirm) {
          alert('새 비밀번호가 일치하지 않습니다.')
          return
        }
        if (!passwords.current_password) {
          alert('비밀번호를 변경하려면 현재 비밀번호를 입력해야 합니다.')
          return
        }
        updateData.current_password = passwords.current_password
        updateData.new_password = passwords.new_password
      }

      await api.updateMe(updateData)

      setSavedAt(new Date().toLocaleTimeString('ko-KR'))
      setPasswords({ current_password: '', new_password: '', new_password_confirm: '' })
      alert('저장되었습니다.')
    } catch (error) {
      console.error(error)
      alert(`저장 중 오류가 발생했습니다:\n${error.message}`)
    }
  }

  if (loading) return <div style={{ padding: 40, textAlign: 'center' }}>데이터를 불러오는 중...</div>

  return (
    <div>
      <div className="page-header">
        <h1>마이 페이지</h1>
        <p>학생 정보를 입력하면 조건에 맞는 장학·대회를 추천받을 수 있습니다.</p>
      </div>

      <form onSubmit={handleSave}>
        {/* 기본 정보 */}
        <div className="card">
          <div className="card__title">
            <h3>기본 정보</h3>
            <span className="text-muted" style={{ fontSize: 13 }}>
              학번: {studentId}
            </span>
          </div>

          <div className="row">
            <div className="col">
              <div className="form-group">
                <label className="form-label">이름</label>
                <input className="form-control" value={profile.name} onChange={(e) => update('name', e.target.value)} />
              </div>
            </div>
            <div className="col">
              <div className="form-group">
                <label className="form-label">학년</label>
                <select
                  className="form-control"
                  value={profile.grade}
                  onChange={(e) => update('grade', Number(e.target.value))}
                >
                  {[1, 2, 3, 4, 5, 6].map((g) => (
                    <option key={g} value={g}>{g}학년</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="row">
            <div className="col">
              <div className="form-group">
                <label className="form-label">단과대학</label>
                <input className="form-control" value={profile.college} onChange={(e) => update('college', e.target.value)} />
              </div>
            </div>
            <div className="col">
              <div className="form-group">
                <label className="form-label">학과</label>
                <input className="form-control" value={profile.department} onChange={(e) => update('department', e.target.value)} />
              </div>
            </div>
          </div>
        </div>

        {/* 관심 분야 */}
        <div className="card">
          <div className="card__title">
            <h3>관심 분야</h3>
            <span className="text-muted" style={{ fontSize: 13 }}>
              추천 점수 가중치에 반영됩니다
            </span>
          </div>
          <div className="filter-bar" style={{ border: 'none', padding: 0 }}>
            {INTEREST_OPTIONS.map((it) => (
              <button
                type="button"
                key={it}
                className={'filter-chip ' + (profile.interests.includes(it) ? 'active' : '')}
                onClick={() => toggleInterest(it)}
              >
                {it}
              </button>
            ))}
          </div>
          <div className="form-help">선택한 항목 {profile.interests.length}개</div>
        </div>

        {/* 비밀번호 변경 */}
        <div className="card">
          <div className="card__title">
            <h3>비밀번호 변경</h3>
            <span className="text-muted" style={{ fontSize: 13 }}>
              비밀번호를 변경하려면 아래 필드를 채워주세요
            </span>
          </div>

          <div className="form-group">
            <label className="form-label">현재 비밀번호</label>
            <input
              type="password"
              className="form-control"
              value={passwords.current_password}
              onChange={(e) => updatePassword('current_password', e.target.value)}
              placeholder="현재 비밀번호 입력"
            />
          </div>

          <div className="row">
            <div className="col">
              <div className="form-group">
                <label className="form-label">새 비밀번호</label>
                <input
                  type="password"
                  className="form-control"
                  value={passwords.new_password}
                  onChange={(e) => updatePassword('new_password', e.target.value)}
                  placeholder="8자 이상 새 비밀번호"
                />
              </div>
            </div>
            <div className="col">
              <div className="form-group">
                <label className="form-label">새 비밀번호 확인</label>
                <input
                  type="password"
                  className="form-control"
                  value={passwords.new_password_confirm}
                  onChange={(e) => updatePassword('new_password_confirm', e.target.value)}
                  placeholder="새 비밀번호 다시 입력"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 북마크한 장학·대회 공고 */}
        <div className="card">
          <div className="card__title">
            <h3>관심 공고 (북마크)</h3>
            <span className="text-muted" style={{ fontSize: 13 }}>
              내가 별표(★) 해둔 장학 및 공모전 목록입니다
            </span>
          </div>

          {bookmarkedItems.length === 0 ? (
            <div className="empty-state" style={{ padding: '24px 0' }}>
              아직 별표로 관심 지정해 둔 공고가 없습니다. <br />
              장학/대회 리스트나 피드에서 별표를 클릭해 보세요!
            </div>
          ) : (
            <div className="list-grid" style={{ marginTop: 12 }}>
              {bookmarkedItems.map((item) => (
                <ItemCard 
                  key={item.id} 
                  item={item} 
                  onBookmarkChange={handleBookmarkChange} 
                />
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-between items-center mt-4">
          <span className="text-muted" style={{ fontSize: 13 }}>
            {savedAt ? `${savedAt}에 저장됨` : '변경사항이 있는 경우 저장을 눌러주세요.'}
          </span>
          <button type="submit" className="btn btn-primary">저장</button>
        </div>
      </form>
    </div>
  )
}
