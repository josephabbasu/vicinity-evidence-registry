import { useState } from 'react'
import { api } from '../api'

export default function Seo() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [tags, setTags] = useState('')
  const [result, setResult] = useState(null)
  const [aiText, setAiText] = useState('')
  const [busy, setBusy] = useState(false)

  async function score() {
    setResult(await api('/seo/score', { method: 'POST', body: { title, description, tags } }))
  }

  async function suggest() {
    setBusy(true)
    try {
      const r = await api('/seo/suggest', { method: 'POST', body: { title, description, tags } })
      setAiText(`(${r.mode} mode)\n\n${r.suggestions}`)
    } finally { setBusy(false) }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black">SEO Optimizer</h1>
      <div className="card space-y-2">
        <input className="input" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <textarea className="input" rows={5} placeholder="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
        <input className="input" placeholder="Tags, comma-separated" value={tags} onChange={(e) => setTags(e.target.value)} />
        <div className="flex gap-2">
          <button className="btn" onClick={score}>Score</button>
          <button className="btn-green" onClick={suggest} disabled={busy}>AI suggestions</button>
        </div>
      </div>

      {result && (
        <div className="card">
          <div className="text-3xl font-black font-mono mb-2">
            {result.score}<span className="text-base text-slate-400">/100</span>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <div className="label mb-1">Checks</div>
              {result.checks.map((c) => (
                <div key={c.name} className="text-sm flex gap-2">
                  <span className={c.passed ? 'text-verified' : 'text-claret'}>{c.passed ? '✓' : '✗'}</span>
                  {c.name}
                </div>
              ))}
            </div>
            <div>
              <div className="label mb-1">Fix first</div>
              {result.suggestions.map((s, i) => (
                <div key={i} className="text-sm text-slate-600 mb-1">• {s}</div>
              ))}
            </div>
          </div>
        </div>
      )}

      {aiText && (
        <div className="card whitespace-pre-wrap text-sm">{aiText}</div>
      )}
    </div>
  )
}
