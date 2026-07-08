import { useEffect, useState } from 'react'
import { api } from '../api'

const PILLARS = [
  'Money Foundations', 'Debt & Credit', 'Saving & Budgeting', 'Investing From Zero',
  'Scams & Traps', 'Earning & Career', 'The Economy Explained', 'Money Psychology',
  'Big Life Purchases', 'Money Around the World',
]

export default function Ideas() {
  const [ideas, setIdeas] = useState([])
  const [title, setTitle] = useState('')
  const [pillar, setPillar] = useState(PILLARS[0])
  const [genPillar, setGenPillar] = useState(PILLARS[0])
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')

  const load = () => api('/ideas').then(setIdeas).catch((e) => setMsg(e.message))
  useEffect(() => { load() }, [])

  async function addIdea(e) {
    e.preventDefault()
    await api('/ideas', { method: 'POST', body: { title, pillar } })
    setTitle('')
    load()
  }

  async function generate() {
    setBusy(true)
    try {
      const r = await api('/ideas/generate', { method: 'POST', body: { pillar: genPillar, count: 5 } })
      setMsg(`Generated ${r.created.length} ideas (${r.mode} mode)`)
      load()
    } catch (e) { setMsg(e.message) } finally { setBusy(false) }
  }

  async function produce(id) {
    setBusy(true)
    try {
      const r = await api(`/workflows/produce/${id}`, { method: 'POST' })
      setMsg(`Video #${r.video_id} created: research + script drafted, ${r.claims_extracted} claims queued for verification.`)
      load()
    } catch (e) { setMsg(e.message) } finally { setBusy(false) }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black">Idea Bank</h1>
      <div className="grid md:grid-cols-2 gap-4">
        <form onSubmit={addIdea} className="card flex gap-2 items-end">
          <div className="flex-1">
            <div className="label mb-1">New idea</div>
            <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Video title" required />
          </div>
          <select className="input w-44" value={pillar} onChange={(e) => setPillar(e.target.value)}>
            {PILLARS.map((p) => <option key={p}>{p}</option>)}
          </select>
          <button className="btn" type="submit">Add</button>
        </form>
        <div className="card flex gap-2 items-end">
          <div className="flex-1">
            <div className="label mb-1">AI idea generator</div>
            <select className="input" value={genPillar} onChange={(e) => setGenPillar(e.target.value)}>
              {PILLARS.map((p) => <option key={p}>{p}</option>)}
            </select>
          </div>
          <button className="btn-green" onClick={generate} disabled={busy}>Generate 5</button>
        </div>
      </div>
      {msg && <div className="text-sm text-slate-600">{msg}</div>}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left label">
              <th className="py-1">Idea</th><th>Pillar</th><th>Score</th><th>Status</th><th></th>
            </tr>
          </thead>
          <tbody>
            {ideas.map((i) => (
              <tr key={i.id} className="border-t border-slate-100">
                <td className="py-2 pr-2">{i.title}</td>
                <td className="pr-2 text-slate-500">{i.pillar}</td>
                <td className="font-mono">{i.score}</td>
                <td className="text-slate-500">{i.status}</td>
                <td className="text-right">
                  {i.status === 'backlog' && (
                    <button className="btn-green" disabled={busy} onClick={() => produce(i.id)}>
                      Produce →
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
