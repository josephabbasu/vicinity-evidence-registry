import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Trends() {
  const [trends, setTrends] = useState([])
  const [keyword, setKeyword] = useState('')
  const [pointInputs, setPointInputs] = useState({})

  const load = () => api('/trends').then(setTrends)
  useEffect(() => { load() }, [])

  async function add(e) {
    e.preventDefault()
    await api('/trends', { method: 'POST', body: { keyword } })
    setKeyword('')
    load()
  }

  async function addPoint(id) {
    const interest = parseFloat(pointInputs[id])
    if (Number.isNaN(interest)) return
    await api(`/trends/${id}/points`, { method: 'POST', body: { interest } })
    setPointInputs({ ...pointInputs, [id]: '' })
    load()
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black">Trend Detector</h1>
      <form onSubmit={add} className="card flex gap-2">
        <input className="input flex-1" placeholder="Keyword to track (e.g. 'how to save money')" value={keyword} onChange={(e) => setKeyword(e.target.value)} required />
        <button className="btn">Track</button>
      </form>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left label"><th className="py-1">Keyword</th><th>Latest</th><th>Growth</th><th>Momentum</th><th>Sparkline</th><th>Add point (0-100)</th></tr>
          </thead>
          <tbody>
            {trends.map((t) => (
              <tr key={t.id} className="border-t border-slate-100">
                <td className="py-2 pr-2">{t.keyword}</td>
                <td className="font-mono">{t.latest}</td>
                <td className={`font-mono ${t.growth_pct > 5 ? 'text-verified' : t.growth_pct < -5 ? 'text-claret' : ''}`}>
                  {t.growth_pct > 0 ? '+' : ''}{t.growth_pct}%
                </td>
                <td className="text-slate-500">{t.momentum}</td>
                <td>
                  <Spark points={t.points} />
                </td>
                <td>
                  <div className="flex gap-1">
                    <input className="input w-20" value={pointInputs[t.id] || ''} onChange={(e) => setPointInputs({ ...pointInputs, [t.id]: e.target.value })} />
                    <button className="btn" onClick={() => addPoint(t.id)}>+</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500">
        Enter relative interest values (0–100) from Google Trends / YouTube search exports. Momentum classifies
        keywords as rising (make now), stable (evergreen library), or declining (skip).
      </p>
    </div>
  )
}

function Spark({ points }) {
  if (!points.length) return <span className="text-xs text-slate-400">no data</span>
  const values = points.map((p) => p.interest)
  const max = Math.max(...values, 1)
  const w = 100, h = 24
  const step = values.length > 1 ? w / (values.length - 1) : w
  const d = values.map((v, i) => `${i === 0 ? 'M' : 'L'}${(i * step).toFixed(1)},${(h - (v / max) * h).toFixed(1)}`).join(' ')
  return (
    <svg width={w} height={h} className="text-verified">
      <path d={d} fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}
