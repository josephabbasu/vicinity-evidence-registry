import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

const STATUS_COLORS = {
  idea: 'bg-slate-200 text-slate-700',
  researched: 'bg-blue-100 text-blue-800',
  scripted: 'bg-indigo-100 text-indigo-800',
  fact_checked: 'bg-amber-100 text-amber-800',
  voiced: 'bg-purple-100 text-purple-800',
  edited: 'bg-pink-100 text-pink-800',
  thumbnail: 'bg-cyan-100 text-cyan-800',
  scheduled: 'bg-emerald-100 text-emerald-800',
  published: 'bg-verified text-white',
  analyzed: 'bg-ink text-paper',
}

export default function Content() {
  const [videos, setVideos] = useState([])
  const [title, setTitle] = useState('')

  const load = () => api('/videos').then(setVideos)
  useEffect(() => { load() }, [])

  async function add(e) {
    e.preventDefault()
    await api('/videos', { method: 'POST', body: { title } })
    setTitle('')
    load()
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black">Content Database</h1>
      <form onSubmit={add} className="card flex gap-2">
        <input className="input flex-1" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="New video title" required />
        <button className="btn">Create</button>
      </form>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left label">
              <th className="py-1">Video</th><th>Pillar</th><th>Format</th><th>Status</th><th>Claims</th>
            </tr>
          </thead>
          <tbody>
            {videos.map((v) => {
              const unverified = v.claims.filter((c) => c.status === 'unverified').length
              return (
                <tr key={v.id} className="border-t border-slate-100">
                  <td className="py-2 pr-2">
                    <Link className="underline" to={`/content/${v.id}`}>{v.title}</Link>
                  </td>
                  <td className="pr-2 text-slate-500">{v.pillar}</td>
                  <td className="text-slate-500">{v.format}</td>
                  <td>
                    <span className={`px-2 py-0.5 rounded text-xs ${STATUS_COLORS[v.status] || ''}`}>
                      {v.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="font-mono text-xs">
                    {v.claims.length > 0 && (
                      unverified > 0
                        ? <span className="text-claret">{unverified} unverified</span>
                        : <span className="text-verified">all verified ✓</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
