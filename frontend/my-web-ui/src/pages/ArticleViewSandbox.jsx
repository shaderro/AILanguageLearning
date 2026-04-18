import { useEffect, useMemo, useState } from 'react'
import ArticleChatView from '../modules/article/ArticleChatView'
import { apiService } from '../services/api'

export default function ArticleViewSandbox({ onBack }) {
  const [articleIdInput, setArticleIdInput] = useState('')
  const [activeArticleId, setActiveArticleId] = useState(null)
  const [articles, setArticles] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    let mounted = true
    const loadArticles = async () => {
      setIsLoading(true)
      setErrorMsg('')
      try {
        const resp = await apiService.getArticlesList()
        const raw = resp?.data?.data || resp?.data || []
        const list = Array.isArray(raw) ? raw : []
        if (mounted) {
          setArticles(list)
        }
      } catch (err) {
        if (mounted) {
          setErrorMsg(err?.response?.data?.detail || err?.message || 'Failed to load articles')
        }
      } finally {
        if (mounted) setIsLoading(false)
      }
    }
    void loadArticles()
    return () => {
      mounted = false
    }
  }, [])

  const recentArticles = useMemo(() => articles.slice(0, 12), [articles])

  if (activeArticleId) {
    return (
      <ArticleChatView
        articleId={activeArticleId}
        isUploadMode={false}
        onBack={() => setActiveArticleId(null)}
        onUploadComplete={() => {}}
        enableAutoAnnotationHint={true}
      />
    )
  }

  return (
    <div className="mx-auto max-w-3xl rounded-lg border border-gray-200 bg-white p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Article View Sandbox</h1>
        <button
          type="button"
          onClick={onBack}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
        >
          Back
        </button>
      </div>

      <p className="mb-4 text-sm text-gray-600">
        Input an existing article ID or choose one below to open the full article reader view.
      </p>

      <div className="mb-6 flex gap-2">
        <input
          type="text"
          value={articleIdInput}
          onChange={(e) => setArticleIdInput(e.target.value)}
          placeholder="Enter article ID"
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={() => {
            const id = articleIdInput.trim()
            if (!id) return
            setActiveArticleId(id)
          }}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Open
        </button>
      </div>

      <div className="rounded-lg border border-gray-200">
        <div className="border-b border-gray-200 px-4 py-2 text-sm font-medium text-gray-700">
          Recent Articles
        </div>
        {isLoading && <div className="px-4 py-3 text-sm text-gray-500">Loading...</div>}
        {!isLoading && errorMsg && <div className="px-4 py-3 text-sm text-red-600">{errorMsg}</div>}
        {!isLoading && !errorMsg && recentArticles.length === 0 && (
          <div className="px-4 py-3 text-sm text-gray-500">No article found.</div>
        )}
        {!isLoading && !errorMsg && recentArticles.length > 0 && (
          <div className="max-h-80 overflow-auto">
            {recentArticles.map((item) => {
              const id = String(item.text_id ?? item.id ?? '')
              const title = item.text_title || item.title || '(untitled)'
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => setActiveArticleId(id)}
                  className="flex w-full items-start justify-between border-b border-gray-100 px-4 py-3 text-left hover:bg-gray-50"
                >
                  <span className="truncate pr-3 text-sm text-gray-800">{title}</span>
                  <span className="shrink-0 text-xs text-gray-500">{id}</span>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
