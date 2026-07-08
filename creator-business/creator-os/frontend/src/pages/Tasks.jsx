import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Tasks() {
  const [tasks, setTasks] = useState([])
  const [title, setTitle] = useState('')

  const load = () => api('/tasks').then(setTasks)
  useEffect(() => { load() }, [])

  async function add(e) {
    e.preventDefault()
    await api('/tasks', { method: 'POST', body: { title } })
    setTitle('')
    load()
  }

  async function toggle(t) {
    await api(`/tasks/${t.id}`, { method: 'PATCH', body: { done: !t.done } })
    load()
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <h1 className="text-2xl font-black">Tasks</h1>
      <form onSubmit={add} className="card flex gap-2">
        <input className="input flex-1" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="New task" required />
        <button className="btn">Add</button>
      </form>
      <div className="card space-y-1">
        {tasks.map((t) => (
          <label key={t.id} className="flex items-center gap-2 text-sm py-1 border-t border-slate-100 first:border-0 cursor-pointer">
            <input type="checkbox" checked={t.done} onChange={() => toggle(t)} />
            <span className={t.done ? 'line-through text-slate-400' : ''}>{t.title}</span>
            {t.video_id && <Link to={`/content/${t.video_id}`} className="text-xs underline text-slate-400 ml-auto">video #{t.video_id}</Link>}
          </label>
        ))}
        {tasks.length === 0 && <div className="text-sm text-slate-500">No tasks. Producing an idea creates the standard checklist automatically.</div>}
      </div>
    </div>
  )
}
