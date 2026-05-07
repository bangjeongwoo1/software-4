import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import MyPage from './pages/MyPage.jsx'
import ItemList from './pages/ItemList.jsx'
import ItemDetail from './pages/ItemDetail.jsx'
import Popular from './pages/Popular.jsx'
import Feed from './pages/Feed.jsx'
import Notifications from './pages/Notifications.jsx'
import AdminNotifications from './pages/AdminNotifications.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/list" replace />} />
        <Route path="/mypage" element={<MyPage />} />
        <Route path="/list" element={<ItemList />} />
        <Route path="/detail/:id" element={<ItemDetail />} />
        <Route path="/popular" element={<Popular />} />
        <Route path="/feed" element={<Feed />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/admin/notifications" element={<AdminNotifications />} />
        <Route path="*" element={<Navigate to="/list" replace />} />
      </Route>
    </Routes>
  )
}
