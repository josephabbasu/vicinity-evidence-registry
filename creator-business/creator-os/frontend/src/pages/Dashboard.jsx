import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

function Stat({ label, value, note }) {
  return (
    <div className="card">
      <div className="label">{label}</div>
      <div className="text-2xl font-black font-mono">{value}</div>
      {note && <div className="text-xs text-slate-500 mt-1">{note}</div>}
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/analytics/dashboard').then(setData).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="text-claret">{error}</div>
  if (!data) return <div className="text-slate-500">Loading…</div>

  const t = data.totals
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-black">Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <Stat label="Views" value={t.views.toLocaleString()} />
        <Stat label="Watch hours" value={t.watch_hours.toLocaleString()} />
        <Stat label="Subs gained" value={t.subscribers_gained.toLocaleString()} />
        <Stat label="Revenue" value={`$${t.revenue.toLocaleString()}`} />
        <Stat label="Avg CTR" value={`${t.avg_ctr}%`} note={data.health.ctr} />
        <Stat label="Avg % viewed" value={`${t.avg_percentage_viewed}%`} note={data.health.retention} />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="font-bold mb-2">Pipeline</h2>
          {Object.keys(data.pipeline).length === 0 && (
            <div className="text-sm text-slate-500">
              Nothing in production. Start from the <Link className="underline" to="/ideas">Idea Bank</Link>.
            </div>
          )}
          <div className="space-y-1">
            {Object.entries(data.pipeline).map(([status, count]) => (
              <div key={status} className="flex justify-between text-sm">
                <span className="capitalize">{status.replace('_', ' ')}</span>
                <span className="font-mono">{count}</span>
              </div>
            ))}
          </div>
          <div className="mt-3 text-sm text-slate-500">
            Idea backlog: <span className="font-mono">{data.idea_backlog}</span> · Open tasks:{' '}
            <span className="font-mono">{data.open_tasks}</span>
          </div>
        </div>
        <div className="card">
          <h2 className="font-bold mb-2">Top videos</h2>
          {data.top_videos.length === 0 && <div className="text-sm text-slate-500">No metrics yet.</div>}
          <ol className="space-y-1">
            {data.top_videos.map((v) => (
              <li key={v.id} className="flex justify-between text-sm">
                <Link className="underline truncate mr-2" to={`/content/${v.id}`}>{v.title}</Link>
                <span className="font-mono">{v.views.toLocaleString()}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  )
}
