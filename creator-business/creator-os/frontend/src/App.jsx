import { Navigate, NavLink, Route, Routes } from 'react-router-dom'
import { getToken } from './api'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Ideas from './pages/Ideas.jsx'
import Content from './pages/Content.jsx'
import VideoDetail from './pages/VideoDetail.jsx'
import Seo from './pages/Seo.jsx'
import Trends from './pages/Trends.jsx'
import Competitors from './pages/Competitors.jsx'
import Planner from './pages/Planner.jsx'
import Assistant from './pages/Assistant.jsx'
import Library from './pages/Library.jsx'
import Tasks from './pages/Tasks.jsx'

const NAV = [
  ['/', 'Dashboard'],
  ['/ideas', 'Ideas'],
  ['/content', 'Content'],
  ['/planner', 'Planner'],
  ['/seo', 'SEO'],
  ['/trends', 'Trends'],
  ['/competitors', 'Competitors'],
  ['/tasks', 'Tasks'],
  ['/library', 'Library'],
  ['/assistant', 'Assistant'],
]

function Protected({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="*"
        element={
          <Protected>
            <div className="min-h-screen flex">
              <aside className="w-52 shrink-0 bg-ink text-paper p-4 flex flex-col gap-1">
                <div className="mb-4">
                  <div className="font-black text-lg tracking-tight">CreatorOS</div>
                  <div className="text-xs text-slate-400">Plain Money studio</div>
                </div>
                {NAV.map(([to, label]) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) =>
                      `px-3 py-1.5 rounded text-sm ${isActive ? 'bg-verified text-white' : 'text-slate-300 hover:bg-slate-800'}`
                    }
                  >
                    {label}
                  </NavLink>
                ))}
                <button
                  className="mt-auto text-left px-3 py-1.5 text-sm text-slate-400 hover:text-white"
                  onClick={() => {
                    localStorage.removeItem('token')
                    window.location.hash = '#/login'
                  }}
                >
                  Sign out
                </button>
              </aside>
              <main className="flex-1 p-6 overflow-x-hidden">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/ideas" element={<Ideas />} />
                  <Route path="/content" element={<Content />} />
                  <Route path="/content/:id" element={<VideoDetail />} />
                  <Route path="/planner" element={<Planner />} />
                  <Route path="/seo" element={<Seo />} />
                  <Route path="/trends" element={<Trends />} />
                  <Route path="/competitors" element={<Competitors />} />
                  <Route path="/tasks" element={<Tasks />} />
                  <Route path="/library" element={<Library />} />
                  <Route path="/assistant" element={<Assistant />} />
                </Routes>
              </main>
            </div>
          </Protected>
        }
      />
    </Routes>
  )
}
