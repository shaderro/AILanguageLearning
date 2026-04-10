import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiService } from '../services/api'
import { useUiLanguage } from '../contexts/UiLanguageContext'
import { useUIText } from '../i18n/useUIText'
import { useUser } from '../contexts/UserContext'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const pickSentences = (articleResp) => {
  // axios interceptor may return different shapes depending on endpoint.
  const data = articleResp?.data ?? articleResp
  const inner = data?.data ?? data
  return (
    inner?.sentences ||
    inner?.data?.sentences ||
    inner?.text_by_sentence ||
    inner?.textBySentence ||
    []
  )
}

export default function ChatConcurrencySandbox() {
  const tUI = useUIText()
  const { uiLanguage } = useUiLanguage()
  const { token } = useUser()

  const [languageFilter, setLanguageFilter] = useState('all')
  const [articles, setArticles] = useState([])
  const [selectedTextId, setSelectedTextId] = useState('')
  const [sentences, setSentences] = useState([])
  const [selectedSentenceIdx, setSelectedSentenceIdx] = useState(0)

  const [question, setQuestion] = useState('What is the structure of this sentence?')
  const [count, setCount] = useState(5)
  const [delayMs, setDelayMs] = useState(150)
  const [mode, setMode] = useState('parallel') // parallel | sequential | staggered

  const [busy, setBusy] = useState(false)
  const [logs, setLogs] = useState([])

  const uiLangForBackend = useMemo(() => (uiLanguage === 'en' ? '英文' : '中文'), [uiLanguage])

  const selectedSentence = useMemo(() => {
    if (!Array.isArray(sentences) || sentences.length === 0) return null
    return sentences[Math.max(0, Math.min(selectedSentenceIdx, sentences.length - 1))]
  }, [sentences, selectedSentenceIdx])

  const addLog = useCallback((row) => {
    setLogs((prev) => [{ ts: new Date().toISOString(), ...row }, ...prev].slice(0, 200))
  }, [])

  const loadArticles = useCallback(async () => {
    if (!token) {
      setArticles([])
      return
    }
    try {
      const resp = await apiService.getArticlesList(languageFilter === 'all' ? null : languageFilter)
      const data = resp?.data ?? resp
      const inner = data?.data ?? data
      const list = Array.isArray(inner) ? inner : Array.isArray(inner?.texts) ? inner.texts : Array.isArray(inner?.data) ? inner.data : []
      setArticles(list)
    } catch (e) {
      addLog({ type: 'error', msg: `loadArticles failed: ${e?.message || String(e)}` })
      setArticles([])
    }
  }, [addLog, languageFilter, token])

  const loadArticleSentences = useCallback(async (textId) => {
    if (!token || !textId) return
    try {
      const resp = await apiService.getArticleById(textId)
      const sents = pickSentences(resp)
      setSentences(Array.isArray(sents) ? sents : [])
      setSelectedSentenceIdx(0)
    } catch (e) {
      addLog({ type: 'error', msg: `loadArticleById(${textId}) failed: ${e?.message || String(e)}` })
      setSentences([])
    }
  }, [addLog, token])

  useEffect(() => {
    loadArticles()
  }, [loadArticles])

  useEffect(() => {
    if (selectedTextId) loadArticleSentences(selectedTextId)
  }, [loadArticleSentences, selectedTextId])

  const ensureContext = useCallback(async () => {
    if (!selectedSentence) {
      throw new Error('No sentence selected')
    }
    const textIdInt = Number.parseInt(String(selectedTextId), 10)
    const patchedSentence =
      Number.isFinite(textIdInt) && textIdInt > 0
        ? { ...selectedSentence, text_id: selectedSentence?.text_id ?? textIdInt }
        : selectedSentence
    await apiService.session.updateContext({
      // Some article endpoints return sentences without text_id; patch it for SessionState.
      sentence: patchedSentence,
      token: null,
    })
  }, [selectedSentence, selectedTextId])

  const sendOne = useCallback(async (idx) => {
    const startedAt = performance.now()
    try {
      const resp = await apiService.sendChat({
        user_question: `${question} (#${idx + 1})`,
        ui_language: uiLangForBackend,
      }, {
        headers: {
          'X-Sandbox-Test': '1',
        },
      })
      const elapsedMs = Math.round(performance.now() - startedAt)
      addLog({ type: 'ok', idx: idx + 1, status: resp?.status ?? 200, ms: elapsedMs })
      return { ok: true, status: resp?.status ?? 200 }
    } catch (e) {
      const elapsedMs = Math.round(performance.now() - startedAt)
      const status = e?.response?.status
      const message =
        e?.response?.data?.detail?.message ||
        e?.response?.data?.error ||
        e?.message ||
        String(e)
      addLog({ type: 'fail', idx: idx + 1, status: status ?? 'ERR', ms: elapsedMs, msg: message })
      return { ok: false, status: status ?? null, message }
    }
  }, [addLog, question, uiLangForBackend])

  const runBurst = useCallback(async () => {
    if (!token) {
      addLog({ type: 'error', msg: 'Not logged in (no token).' })
      return
    }
    if (!selectedTextId) {
      addLog({ type: 'error', msg: 'Pick a text_id first.' })
      return
    }
    if (!selectedSentence) {
      addLog({ type: 'error', msg: 'Pick a sentence first.' })
      return
    }
    const n = Math.max(1, Math.min(50, Number(count) || 1))
    const d = Math.max(0, Math.min(5000, Number(delayMs) || 0))

    setBusy(true)
    try {
      addLog({ type: 'info', msg: `Setting session context... (ui_language=${uiLangForBackend})` })
      await ensureContext()
      addLog({ type: 'info', msg: `Start burst: mode=${mode}, count=${n}, delayMs=${d}` })

      if (mode === 'sequential') {
        for (let i = 0; i < n; i += 1) {
          await sendOne(i)
        }
        return
      }

      if (mode === 'staggered') {
        const tasks = Array.from({ length: n }, (_, i) => (async () => {
          await sleep(i * d)
          return await sendOne(i)
        })())
        await Promise.allSettled(tasks)
        return
      }

      // parallel
      await Promise.allSettled(Array.from({ length: n }, (_, i) => sendOne(i)))
    } finally {
      setBusy(false)
    }
  }, [addLog, count, delayMs, ensureContext, mode, selectedSentence, selectedTextId, sendOne, token, uiLangForBackend])

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      <div className="space-y-1">
        <div className="text-2xl font-bold text-gray-900">Chat Concurrency Sandbox</div>
        <div className="text-sm text-gray-600">
          Stress-test repeated chat sends while background tasks are running. Use `page=chatConcurrencySandbox`.
        </div>
      </div>

      {!token && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {tUI('请先登录后使用 AI 聊天')}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border bg-white p-4 space-y-3">
          <div className="text-sm font-semibold text-gray-900">Context</div>
          <div className="flex gap-2">
            <select
              className="border rounded px-2 py-1 text-sm flex-1"
              value={languageFilter}
              onChange={(e) => setLanguageFilter(e.target.value)}
              disabled={busy}
            >
              <option value="all">all</option>
              <option value="中文">中文</option>
              <option value="英文">英文</option>
              <option value="德文">德文</option>
              <option value="日语">日语</option>
              <option value="法语">法语</option>
              <option value="西班牙语">西班牙语</option>
            </select>
            <button
              className="border rounded px-3 py-1 text-sm"
              onClick={loadArticles}
              disabled={busy || !token}
              type="button"
            >
              Reload
            </button>
          </div>

          <select
            className="border rounded px-2 py-1 text-sm w-full"
            value={selectedTextId}
            onChange={(e) => setSelectedTextId(e.target.value)}
            disabled={busy || !token}
          >
            <option value="">Select text_id</option>
            {articles.map((a) => {
              const id = a.text_id || a.id || a.article_id
              const title = a.text_title || a.title || `text_${id}`
              return (
                <option key={String(id)} value={String(id)}>
                  {String(id)} — {String(title).slice(0, 60)}
                </option>
              )
            })}
          </select>

          <div className="flex gap-2 items-center">
            <div className="text-xs text-gray-500">Sentence</div>
            <input
              className="border rounded px-2 py-1 text-sm w-24"
              type="number"
              min="0"
              max={Math.max(0, (sentences?.length || 1) - 1)}
              value={selectedSentenceIdx}
              onChange={(e) => setSelectedSentenceIdx(Number(e.target.value))}
              disabled={busy || !token}
            />
            <div className="text-xs text-gray-500">/ {sentences.length || 0}</div>
          </div>

          <div className="rounded border bg-gray-50 p-2 text-xs text-gray-700 whitespace-pre-wrap max-h-32 overflow-auto">
            {(selectedSentence?.sentence_body || selectedSentence?.text || '').toString().slice(0, 500) || '(no sentence loaded)'}
          </div>
        </div>

        <div className="rounded-lg border bg-white p-4 space-y-3">
          <div className="text-sm font-semibold text-gray-900">Burst settings</div>
          <div className="grid gap-2">
            <label className="text-xs text-gray-600">
              Question template
              <input
                className="mt-1 border rounded px-2 py-1 text-sm w-full"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={busy}
              />
            </label>
            <div className="grid grid-cols-2 gap-2">
              <label className="text-xs text-gray-600">
                Count (1-50)
                <input
                  className="mt-1 border rounded px-2 py-1 text-sm w-full"
                  type="number"
                  min="1"
                  max="50"
                  value={count}
                  onChange={(e) => setCount(Number(e.target.value))}
                  disabled={busy}
                />
              </label>
              <label className="text-xs text-gray-600">
                Delay ms (staggered)
                <input
                  className="mt-1 border rounded px-2 py-1 text-sm w-full"
                  type="number"
                  min="0"
                  max="5000"
                  value={delayMs}
                  onChange={(e) => setDelayMs(Number(e.target.value))}
                  disabled={busy}
                />
              </label>
            </div>
            <label className="text-xs text-gray-600">
              Mode
              <select
                className="mt-1 border rounded px-2 py-1 text-sm w-full"
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                disabled={busy}
              >
                <option value="parallel">parallel (all at once)</option>
                <option value="sequential">sequential (await each)</option>
                <option value="staggered">staggered (i * delayMs)</option>
              </select>
            </label>
          </div>

          <button
            className="w-full rounded bg-gray-900 text-white py-2 text-sm disabled:opacity-60"
            onClick={runBurst}
            disabled={busy || !token}
            type="button"
          >
            {busy ? 'Running…' : 'Run burst'}
          </button>

          <div className="text-xs text-gray-500">
            Backend ui_language: <span className="font-medium">{uiLangForBackend}</span>
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4">
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold text-gray-900">Results (latest first)</div>
          <button
            className="border rounded px-3 py-1 text-sm"
            onClick={() => setLogs([])}
            type="button"
          >
            Clear
          </button>
        </div>
        <div className="mt-3 max-h-[420px] overflow-auto text-xs font-mono">
          {logs.length === 0 ? (
            <div className="text-gray-400">No logs yet.</div>
          ) : (
            logs.map((l, i) => (
              <div key={`${l.ts}-${i}`} className="py-1 border-b border-gray-100">
                <span className="text-gray-400">{l.ts}</span>{' '}
                <span className={l.type === 'ok' ? 'text-emerald-700' : l.type === 'fail' ? 'text-red-700' : 'text-gray-700'}>
                  [{l.type}]
                </span>{' '}
                {l.idx ? <span># {l.idx} </span> : null}
                {l.status != null ? <span>status={String(l.status)} </span> : null}
                {typeof l.ms === 'number' ? <span>{l.ms}ms </span> : null}
                {l.msg ? <span className="text-gray-700">{String(l.msg)}</span> : null}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

