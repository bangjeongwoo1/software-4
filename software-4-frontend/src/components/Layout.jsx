import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { api } from '../lib/api.js'

export default function Layout() {
  const navigate = useNavigate()
  const [userProfile, setUserProfile] = useState({ name: '로딩중...', department: '', grade: '' })

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const user = await api.getMe()
        if (user) {
          setUserProfile({
            name: user.name || '이름없음',
            department: user.department || '소속없음',
            grade: user.grade ? `${user.grade}학년` : '?'
          })
        }
      } catch (err) {
        console.error(err)
        navigate('/login')
      }
    }
    fetchProfile()
  }, [navigate])

  const handleLogout = () => {
    api.logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <NavLink to="/" className="app-header__brand">
          <span className="app-header__brand-mark">SC</span>
          <span>장학·취업 정보 추천</span>
        </NavLink>

        <nav className="app-header__nav">
          <NavLink to="/list" className={({ isActive }) => (isActive ? 'active' : '')}>
            정보 조회
          </NavLink>
          <NavLink to="/popular" className={({ isActive }) => (isActive ? 'active' : '')}>
            추천
          </NavLink>
          <NavLink to="/feed" className={({ isActive }) => (isActive ? 'active' : '')}>
            피드
          </NavLink>
          <NavLink to="/notifications" className={({ isActive }) => (isActive ? 'active' : '')}>
            알림
          </NavLink>
        </nav>

        <div className="app-header__actions">
          <span className="text-secondary" style={{ fontSize: 13 }}>
            {userProfile.name} · {userProfile.department} {userProfile.grade !== '?' ? `${userProfile.grade}` : ''}
          </span>
          <button className="btn btn-ghost btn-sm" onClick={handleLogout}>
            로그아웃
          </button>
        </div>
      </header>

      <div className="app-body">
        <aside className="app-sidebar">
          <div className="sidebar-section">
            <div className="sidebar-section__title">정보 기입</div>
            <NavLink to="/mypage" className={({ isActive }) => 'sidebar-link' + (isActive ? ' active' : '')}>
              마이 페이지
            </NavLink>
            <NavLink to="/mypage#history" className="sidebar-link">
              대회 참여 이력
            </NavLink>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section__title">정보 조회</div>
            <NavLink to="/list?type=scholarship" className="sidebar-link">
              장학 리스트
            </NavLink>
            <NavLink to="/list?type=contest" className="sidebar-link">
              대회 리스트
            </NavLink>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section__title">추천</div>
            <NavLink to="/popular" className={({ isActive }) => 'sidebar-link' + (isActive ? ' active' : '')}>
              인기 장학·대회
            </NavLink>
            <NavLink to="/feed" className={({ isActive }) => 'sidebar-link' + (isActive ? ' active' : '')}>
              피드
            </NavLink>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section__title">알림</div>
            <NavLink to="/notifications" end className={({ isActive }) => 'sidebar-link' + (isActive ? ' active' : '')}>
              알림 목록 / 설정
            </NavLink>
            <NavLink to="/admin/notifications" className={({ isActive }) => 'sidebar-link' + (isActive ? ' active' : '')}>
              알림 전송 (관리자)
            </NavLink>
          </div>
        </aside>

        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
