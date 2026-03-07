import { NavLink } from 'react-router-dom'

const TABS = [
  { to: '/', label: "ג'יו", emoji: '💬' },
  { to: '/timeline', label: 'לוח זמנים', emoji: '📅' },
  { to: '/grades', label: 'ציונים', emoji: '🎓' },
  { to: '/emails', label: 'מיילים', emoji: '📬' },
  { to: '/settings', label: 'הגדרות', emoji: '⚙️' },
]

export default function TabNavigator() {
  return (
    <nav className="flex border-t bg-white">
      {TABS.map(({ to, label, emoji }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center py-2 text-xs gap-1 ${
              isActive ? 'text-blue-600 font-semibold' : 'text-gray-500'
            }`
          }
        >
          <span className="text-lg">{emoji}</span>
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
