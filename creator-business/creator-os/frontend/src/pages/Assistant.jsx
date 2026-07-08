import { useState } from 'react'
import { api } from '../api'

export default function Assistant() {
  const [history, setHistory] = useState([])
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  async function send(e) {
    e.preventDefault()
    const userMsg = { role: 'user', content: message }
    setHistory((h) => [...h, userMsg])
    setMessage('')
    setBusy(true)
    try {
      const r = await api('/assistant/chat', {
        method: 'POST',
        body: { message: userMsg.content, history },
      })
      setHistory((h) => [...h, { role: 'assistant', content: r.reply, model: r.model }])
    } catch (err) {
      setHistory((h) => [...h, { role: 'assistant', content: `Error: ${err.message}` }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4 max-w-3xl">
      <h1 className="text-2xl font-black">AI Assistant</h1>
      <div className="card min-h-64 space-y-3">
        {history.length === 0 && (
          <div className="text-sm text-slate-500">
            Ask about titles, hooks, thumbnails, retention drops, scheduling, or the brand voice.
          </div>
        )}
        {history.map((m, i) => (
          <div key={i} className={`text-sm whitespace-pre-wrap ${m.role === 'user' ? 'font-medium' : 'text-slate-700 border-l-2 border-verified pl-3'}`}>
            {m.content}
            {m.model && <div className="text-xs text-slate-400 mt-1">{m.model}</div>}
          </div>
        ))}
        {busy && <div className="text-sm text-slate-400">Thinking…</div>}
      </div>
      <form onSubmit={send} className="flex gap-2">
        <input className="input flex-1" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Message the assistant…" required />
        <button className="btn-green" disabled={busy}>Send</button>
      </form>
    </div>
  )
}
