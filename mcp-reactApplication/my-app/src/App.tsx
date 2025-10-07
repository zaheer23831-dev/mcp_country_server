import { useMemo, useState, type ChangeEvent, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { getReport } from './api'

export default function App() {
  const [country, setCountry] = useState<string>('france')
  const [markdown, setMarkdown] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string>('')

  // keep an AbortController so we can cancel in-flight requests
  const abortRef = useRef<AbortController | null>(null)

  async function fetchReport(mode: 'GET' | 'POST' = 'GET') {
    setLoading(true); setError('')

    // cancel prior request if any
    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    const result = await getReport(country, { mode, signal: ctrl.signal })
    if (result.ok) {
      setMarkdown(result.data.markdown || '')
      setError('')
    } else {
      setMarkdown('')
      setError(`Failed (${result.status}): ${result.error}`)
    }
    setLoading(false)
  }

  const preview = useMemo(() => markdown, [markdown])

  return (
    <div
      style={{
        maxWidth: 900,
        margin: '2rem auto',
        fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Arial',
      }}
    >
      <h1>Agent Markdown Viewer</h1>
      <p style={{ opacity: 0.8 }}>
        Calls the DeepSeek agent service and renders the Markdown it returns.
      </p>

      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 16 }}>
        <label>
          Country:&nbsp;
          <input
            value={country}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setCountry(e.target.value)}
            placeholder="france"
          />
        </label>
        <button onClick={() => fetchReport('GET')} disabled={loading}>
          {loading ? 'Generating…' : 'Generate (GET)'}
        </button>
        <button onClick={() => fetchReport('POST')} disabled={loading}>
          {loading ? 'Generating…' : 'Generate (POST)'}
        </button>
      </div>

      {error && (
        <pre
          style={{
            color: 'crimson',
            background: '#fee',
            padding: 12,
            marginTop: 16,
          }}
        >
          {error}
        </pre>
      )}

      {markdown && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 16,
            marginTop: 24,
          }}
        >
          <div>
            <h3>Markdown</h3>
            <pre
              style={{
                background: '#f6f8fa',
                padding: 12,
                whiteSpace: 'pre-wrap',
              }}
            >
              {markdown}
            </pre>
          </div>
          <div>
            <h3>Preview</h3>
            <div
              style={{
                background: 'white',
                padding: 16,
                border: '1px solid #eee',
              }}
            >
              <ReactMarkdown>{preview}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      <hr style={{ marginTop: 32 }} />
      <h3>Config</h3>
      <ul>
        <li>
          <code>VITE_AGENT_BASE_URL</code> (default: <code>http://localhost:5050</code>)
        </li>
        <li>
          <code>VITE_USE_PROXY</code> = <code>1</code> to proxy <code>/report</code> to the
          agent service (avoids CORS)
        </li>
      </ul>
    </div>
  )
}
