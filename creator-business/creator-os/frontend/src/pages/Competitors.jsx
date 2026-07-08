import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Competitors() {
  const [comps, setComps] = useState([])
  const [name, setName] = useState('')
  const [url, setUrl] = useState('')
  const [snapInputs, setSnapInputs] = useState({})

  const load = () => api('/competitors').then(setComps)
  useEffect(() => { load() }, [])

  async function add(e) {
    e.preventDefault()
    await api('/competitors', { method: 'POST', body: { name, channel_url: url } })
    setName(''); setUrl('')
    load()
  }

  async function snapshot(id) {
    const subs = parseInt(snapInputs[id], 10)
    if (Number.isNaN(subs)) return
    await api(`/competitors/${id}/snapshots`, { method: 'POST', body: { subscribers: subs } })
    setSnapInputs({ ...snapInputs, [id]: '' })
    load()
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black">Competitor Tracker</h1>
      <form onSubmit={add} className="card flex gap-2">
        <input className="input flex-1" placeholder="Channel name" value={name} onChange={(e) => setName(e.target.value)} required />
        <input className="input flex-1" placeholder="Channel URL" value={url} onChange={(e) => setUrl(e.target.value)} />
        <button className="btn">Track</button>
      </form>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left label"><th className="py-1">Channel</th><th>Subscribers</th><th>Growth</th><th>Record snapshot</th></tr>
          </thead>
          <tbody>
            {comps.map((c) => (
              <tr key={c.id} className="border-t border-slate-100">
                <td className="py-2 pr-2">
                  {c.channel_url ? <a className="underline" href={c.channel_url} target="_blank" rel="noreferrer">{c.name}</a> : c.name}
                </td>
                <td className="font-mono">{c.subscribers?.toLocaleString() ?? '—'}</td>
                <td className={`font-mono ${c.growth_pct > 0 ? 'text-verified' : ''}`}>
                  {c.growth_pct != null ? `${c.growth_pct > 0 ? '+' : ''}${c.growth_pct}%` : '—'}
                </td>
                <td>
                  <div className="flex gap-1">
                    <input className="input w-28" placeholder="subs" value={snapInputs[c.id] || ''} onChange={(e) => setSnapInputs({ ...snapInputs, [c.id]: e.target.value })} />
                    <button className="btn" onClick={() => snapshot(c.id)}>+</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500">
        Track adjacent channels' scale over time to spot format gaps — the goal is differentiation, not imitation.
      </p>
    </div>
  )
}
