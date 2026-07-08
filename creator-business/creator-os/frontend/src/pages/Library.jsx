import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Library() {
  const [prompts, setPrompts] = useState([])
  const [articles, setArticles] = useState([])
  const [tab, setTab] = useState('knowledge')

  useEffect(() => {
    api('/prompts').then(setPrompts)
    api('/knowledge').then(setArticles)
  }, [])

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black">Library</h1>
      <div className="flex gap-2">
        <button className={tab === 'knowledge' ? 'btn-green' : 'btn'} onClick={() => setTab('knowledge')}>Knowledge base</button>
        <button className={tab === 'prompts' ? 'btn-green' : 'btn'} onClick={() => setTab('prompts')}>Prompt library</button>
      </div>

      {tab === 'knowledge' && (
        <div className="grid md:grid-cols-2 gap-3">
          {articles.map((a) => (
            <div key={a.id} className="card">
              <div className="label">{a.category}</div>
              <div className="font-bold">{a.title}</div>
              <p className="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{a.body}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'prompts' && (
        <div className="space-y-3">
          {prompts.map((p) => (
            <div key={p.id} className="card">
              <div className="flex justify-between">
                <div className="font-bold font-mono text-sm">{p.name}</div>
                <div className="text-xs text-slate-400">v{p.version}</div>
              </div>
              <div className="text-xs text-slate-500">{p.purpose}</div>
              <p className="text-sm text-slate-700 mt-2 whitespace-pre-wrap">{p.body}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
