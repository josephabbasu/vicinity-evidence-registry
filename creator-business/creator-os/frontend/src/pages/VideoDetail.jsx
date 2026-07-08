import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'

export default function VideoDetail() {
  const { id } = useParams()
  const [video, setVideo] = useState(null)
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)
  const [sourceInputs, setSourceInputs] = useState({})

  const load = () => api(`/videos/${id}`).then(setVideo).catch((e) => setMsg(e.message))
  useEffect(() => { load() }, [id])

  async function run(action) {
    setBusy(true)
    setMsg('')
    try {
      const r = await api(`/videos/${id}/${action}`, { method: 'POST' })
      setMsg(r.mode ? `${action}: done (${r.mode} mode)` : `Advanced to ${r.status}`)
      load()
    } catch (e) { setMsg(e.message) } finally { setBusy(false) }
  }

  async function save(field, value) {
    await api(`/videos/${id}`, { method: 'PATCH', body: { [field]: value } })
    load()
  }

  async function verifyClaim(claim) {
    const url = sourceInputs[claim.id] ?? claim.source_url
    try {
      await api(`/videos/${id}/claims/${claim.id}`, {
        method: 'PATCH',
        body: { status: 'verified', source_url: url },
      })
      load()
    } catch (e) { setMsg(e.message) }
  }

  if (!video) return <div className="text-slate-500">{msg || 'Loading…'}</div>

  const unverified = video.claims.filter((c) => c.status === 'unverified').length

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-black">{video.title}</h1>
        <span className="px-2 py-1 rounded bg-ink text-paper text-xs uppercase">{video.status.replace('_', ' ')}</span>
      </div>

      <div className="flex gap-2 flex-wrap">
        <button className="btn" disabled={busy} onClick={() => run('research')}>1 · Research</button>
        <button className="btn" disabled={busy} onClick={() => run('script')}>2 · Script</button>
        <button className="btn" disabled={busy} onClick={() => run('factcheck')}>3 · Fact-check pass</button>
        <button className="btn-green" disabled={busy} onClick={() => run('advance')}>Advance pipeline →</button>
      </div>
      {msg && <div className="text-sm text-slate-600">{msg}</div>}

      <div className="card">
        <div className="flex justify-between items-center mb-2">
          <h2 className="font-bold">Claims (verification gate)</h2>
          <span className={`text-sm font-mono ${unverified ? 'text-claret' : 'text-verified'}`}>
            {unverified ? `${unverified} unverified — pipeline blocked` : 'all verified ✓'}
          </span>
        </div>
        <div className="space-y-2">
          {video.claims.map((c) => (
            <div key={c.id} className="flex gap-2 items-center text-sm border-t border-slate-100 pt-2">
              <span className={`shrink-0 w-2 h-2 rounded-full ${c.status === 'verified' ? 'bg-verified' : c.status === 'unverified' ? 'bg-claret' : 'bg-signal'}`} />
              <span className="flex-1">{c.text}</span>
              {c.status === 'unverified' ? (
                <>
                  <input
                    className="input w-64"
                    placeholder="Source URL"
                    value={sourceInputs[c.id] ?? c.source_url}
                    onChange={(e) => setSourceInputs({ ...sourceInputs, [c.id]: e.target.value })}
                  />
                  <button className="btn-green" onClick={() => verifyClaim(c)}>Verify</button>
                </>
              ) : (
                <a className="text-xs underline text-slate-500 truncate max-w-48" href={c.source_url} target="_blank" rel="noreferrer">{c.source_url}</a>
              )}
            </div>
          ))}
          {video.claims.length === 0 && <div className="text-sm text-slate-500">No claims yet — run the fact-check pass to extract [CLAIM] lines.</div>}
        </div>
      </div>

      <Editor label="Research brief" value={video.research_brief} onSave={(v) => save('research_brief', v)} />
      <Editor label="Script" value={video.script} onSave={(v) => save('script', v)} rows={14} />
      <Editor label="Description" value={video.description} onSave={(v) => save('description', v)} rows={5} />
      <Editor label="Tags (comma-separated)" value={video.tags} onSave={(v) => save('tags', v)} rows={2} />
      <Editor label="Thumbnail brief" value={video.thumbnail_brief} onSave={(v) => save('thumbnail_brief', v)} rows={3} />

      <div className="card flex items-end gap-2">
        <div>
          <div className="label mb-1">Scheduled at (UTC)</div>
          <input
            className="input"
            type="datetime-local"
            defaultValue={video.scheduled_at ? video.scheduled_at.slice(0, 16) : ''}
            onBlur={(e) => e.target.value && save('scheduled_at', new Date(e.target.value).toISOString())}
          />
        </div>
        <div className="text-xs text-slate-500 pb-2">Cadence anchor: Tue & Sat 14:00 UTC</div>
      </div>
    </div>
  )
}

function Editor({ label, value, onSave, rows = 8 }) {
  const [text, setText] = useState(value)
  const [dirty, setDirty] = useState(false)
  useEffect(() => { setText(value); setDirty(false) }, [value])
  return (
    <div className="card">
      <div className="flex justify-between items-center mb-1">
        <div className="label">{label}</div>
        {dirty && <button className="btn-green" onClick={() => { onSave(text); setDirty(false) }}>Save</button>}
      </div>
      <textarea
        className="input font-mono text-xs"
        rows={rows}
        value={text}
        onChange={(e) => { setText(e.target.value); setDirty(true) }}
      />
    </div>
  )
}
