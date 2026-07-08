import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Planner() {
  const [cal, setCal] = useState(null)
  const [slots, setSlots] = useState([])

  useEffect(() => {
    api('/planner/calendar').then(setCal)
    api('/planner/next-slots').then((r) => setSlots(r.slots))
  }, [])

  if (!cal) return <div className="text-slate-500">Loading…</div>

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black">Publishing Planner</h1>
      <div className="grid md:grid-cols-3 gap-3">
        <div className="card">
          <div className="label">Batch buffer</div>
          <div className={`text-2xl font-black font-mono ${cal.buffer_ok ? 'text-verified' : 'text-claret'}`}>
            {cal.buffer_weeks} wk
          </div>
          <div className="text-xs text-slate-500">target ≥ {cal.buffer_target_weeks} weeks</div>
        </div>
        <div className="card">
          <div className="label">In production</div>
          <div className="text-2xl font-black font-mono">{cal.in_production}</div>
        </div>
        <div className="card">
          <div className="label">Next publish slots (Tue/Sat 14:00 UTC)</div>
          <div className="text-xs font-mono space-y-0.5 mt-1">
            {slots.map((s) => <div key={s}>{s.replace('T', ' ').slice(0, 16)} UTC</div>)}
          </div>
        </div>
      </div>
      <div className="card">
        <h2 className="font-bold mb-2">Scheduled & published</h2>
        {cal.scheduled.length === 0 && <div className="text-sm text-slate-500">Nothing scheduled yet.</div>}
        <table className="w-full text-sm">
          <tbody>
            {cal.scheduled.map((v) => (
              <tr key={v.id} className="border-t border-slate-100">
                <td className="py-2"><Link className="underline" to={`/content/${v.id}`}>{v.title}</Link></td>
                <td className="text-slate-500">{v.status}</td>
                <td className="font-mono text-xs">{(v.scheduled_at || v.published_at || '').slice(0, 16).replace('T', ' ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
