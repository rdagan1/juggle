import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import TabNavigator from './components/TabNavigator'
import LoginPage from './pages/LoginPage'
import GioPage from './pages/GioPage'
import TimelinePage from './pages/TimelinePage'
import GradesPage from './pages/GradesPage'
import EmailsPage from './pages/EmailsPage'
import SettingsPage from './pages/SettingsPage'

function ProtectedLayout() {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />

  return (
    <div className="flex flex-col h-screen" dir="rtl">
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<GioPage />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/grades" element={<GradesPage />} />
          <Route path="/emails" element={<EmailsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
      <TabNavigator />
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={<ProtectedLayout />} />
    </Routes>
  )
}
