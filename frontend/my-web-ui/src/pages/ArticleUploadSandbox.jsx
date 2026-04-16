import { useState, useMemo } from 'react'
import { apiService } from '../services/api'
import { useUser } from '../contexts/UserContext'
import { useLanguage } from '../contexts/LanguageContext'
import { useUIText } from '../i18n/useUIText'
import { BackButton } from '../components/base'

/** 与后端 main.py MAX_SEGMENT_CHARS 保持一致 */
export const MAX_SEGMENT_CHARS = 2000
/** Sandbox 总长度上限（超出将自动截断） */
export const MAX_SANDBOX_TOTAL_CHARS = 30000

const SEGMENT_JOB_KEY = 'article_segment_job_'
const SEGMENT_RUNNING_KEY = 'article_segment_running_'
const AVAILABLE_LANGUAGES = ['中文', '英文', '德文', '西班牙语', '法语', '日语', '韩语', '葡萄牙语', '意大利语', '俄语']
const SPLIT_MODE_OPTIONS = [
  { id: 'punctuation', labelKey: 'articleSplitModePunctuation' },
  { id: 'line', labelKey: 'articleSplitModeLine' },
]

function isSentenceBoundaryChar(ch) {
  return ['.', '!', '?', ';', '。', '！', '？', '；', '…'].includes(ch)
}

function findSafePunctuationBoundary(slice) {
  // 从后往前找句末标点，避免把一句话切断
  for (let i = slice.length - 1; i >= 0; i -= 1) {
    if (isSentenceBoundaryChar(slice[i])) {
      return i + 1
    }
  }
  return -1
}

function getTransportLength(text) {
  return String(text || '').replace(/\r?\n/g, '\r\n').length
}

async function runSegmentAppendLoop(articleId) {
  const key = `${SEGMENT_JOB_KEY}${articleId}`
  const runningKey = `${SEGMENT_RUNNING_KEY}${articleId}`
  if (localStorage.getItem(runningKey) === '1') return
  localStorage.setItem(runningKey, '1')
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return
    let job
    try {
      job = JSON.parse(raw)
    } catch {
      localStorage.removeItem(key)
      return
    }
    let queue = Array.isArray(job.remaining) ? [...job.remaining] : []
    let completed = Number(job.completedPages || 1)
    let total = Number(job.totalPages || completed + queue.length)
    while (queue.length > 0) {
      // 轻微节流，避免瞬时洪峰请求把其它接口挤进同一限流窗口
      await new Promise((resolve) => setTimeout(resolve, 120))
      const nextItem = queue[0]
      const content = typeof nextItem === 'string' ? nextItem : nextItem?.content
      const pageIndex = typeof nextItem === 'string' ? completed + 1 : Number(nextItem?.pageIndex || completed + 1)
      if (!content) {
        queue.shift()
        continue
      }
      const safeContent = String(content)
      if (getTransportLength(safeContent) > MAX_SEGMENT_CHARS) {
        let parts = splitArticleIntoSegmentsByMode(safeContent, job.splitMode || 'punctuation')
        // 兜底：若边界切分未缩短（常见于 CRLF 扩容），强制二分，避免循环停滞
        if (parts.length <= 1) {
          const pivot = Math.max(1, Math.floor(safeContent.length / 2))
          parts = [safeContent.slice(0, pivot), safeContent.slice(pivot)].filter(Boolean)
        }
        const tail = queue.slice(1)
        const replacement = parts.map((p, idx) => ({ content: p, pageIndex: pageIndex + idx }))
        const delta = Math.max(0, replacement.length - 1)
        const shiftedTail = tail.map((it, idx) => {
          if (typeof it === 'string') {
            return { content: it, pageIndex: pageIndex + replacement.length + idx }
          }
          return { ...it, pageIndex: Number(it.pageIndex || (pageIndex + replacement.length + idx)) + delta }
        })
        queue = [...replacement, ...shiftedTail]
        total += delta
        localStorage.setItem(
          key,
          JSON.stringify({
            ...job,
            remaining: queue,
            completedPages: completed,
            totalPages: total,
          })
        )
        continue
      }
      const res = await apiService.appendArticleSegment(safeContent, articleId, job.language, pageIndex, job.splitMode || 'punctuation')
      const ok = res?.status === 'success'
      if (!ok) {
        const msg = String(res?.error || res?.message || '')
        // 后端报超长时，自动拆分重试，避免循环终止卡住
        if (msg.includes('超出限制') && safeContent.length > 1) {
          let parts = splitArticleIntoSegmentsByMode(safeContent, job.splitMode || 'punctuation')
          // 兜底：边界切分无效时强制二分，保证任务可继续推进
          if (parts.length <= 1) {
            const pivot = Math.max(1, Math.floor(safeContent.length / 2))
            parts = [safeContent.slice(0, pivot), safeContent.slice(pivot)].filter(Boolean)
          }
          const tail = queue.slice(1)
          const replacement = parts.map((p, idx) => ({ content: p, pageIndex: pageIndex + idx }))
          const delta = Math.max(0, replacement.length - 1)
          const shiftedTail = tail.map((it, idx) => {
            if (typeof it === 'string') {
              return { content: it, pageIndex: pageIndex + replacement.length + idx }
            }
            return { ...it, pageIndex: Number(it.pageIndex || (pageIndex + replacement.length + idx)) + delta }
          })
          queue = [...replacement, ...shiftedTail]
          total += delta
          localStorage.setItem(
            key,
            JSON.stringify({
              ...job,
              remaining: queue,
              completedPages: completed,
              totalPages: total,
            })
          )
          continue
        }
        break
      }
      queue.shift()
      completed += 1
      if (queue.length === 0) {
        localStorage.removeItem(key)
      } else {
        localStorage.setItem(
          key,
          JSON.stringify({
            ...job,
            remaining: queue,
            completedPages: completed,
            totalPages: total,
          })
        )
      }
    }
  } finally {
    localStorage.removeItem(runningKey)
  }
}

export function splitArticleIntoSegments(text) {
  return splitArticleIntoSegmentsByMode(text, 'punctuation')
}

export function splitArticleIntoSegmentsByMode(text, splitMode = 'punctuation') {
  const t = (text || '').trim()
  if (!t) return []
  if (t.length <= MAX_SEGMENT_CHARS) return [t]
  const out = []
  let start = 0
  while (start < t.length) {
    let end = Math.min(start + MAX_SEGMENT_CHARS, t.length)
    if (end < t.length) {
      const slice = t.slice(start, end)
      const mode = (splitMode || 'punctuation').toLowerCase()
      let breakAt = -1
      if (mode === 'line') {
        const para = slice.lastIndexOf('\n\n')
        const line = slice.lastIndexOf('\n')
        if (para >= Math.floor(slice.length * 0.5)) breakAt = para + 2
        else if (line >= Math.floor(slice.length * 0.5)) breakAt = line + 1
      } else {
        const punct = findSafePunctuationBoundary(slice)
        if (punct >= Math.floor(slice.length * 0.4)) {
          breakAt = punct
        } else {
          const lastSpace = slice.lastIndexOf(' ')
          if (lastSpace >= Math.floor(slice.length * 0.7)) breakAt = lastSpace + 1
        }
      }
      if (breakAt > 0) end = start + breakAt
    }
    out.push(t.slice(start, end))
    start = end
  }
  return out
}

/**
 * 开发用 Sandbox：长文按字数分段上传，首段完成后跳转阅读页，其余段后台续传。
 * 访问：/?page=articleUploadSandbox
 */
export default function ArticleUploadSandbox({ onNavigateToArticle, onBack }) {
  const t = useUIText()
  const { isGuest } = useUser()
  const { selectedLanguage } = useLanguage()
  const [language, setLanguage] = useState(
    AVAILABLE_LANGUAGES.includes(selectedLanguage) ? selectedLanguage : '德文'
  )

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [url, setUrl] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadMethod, setUploadMethod] = useState('text') // text | file | url
  const [splitMode, setSplitMode] = useState('punctuation')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const extractLengthErrorPayload = (res) => {
    const data = res?.data
    if (!data || typeof data !== 'object') return null
    if (data.error_code !== 'CONTENT_TOO_LONG') return null
    if (typeof data.original_content !== 'string' || !data.original_content.trim()) return null
    return data
  }

  const tryAutoTruncateAndUpload = async (res, articleTitle) => {
    const payload = extractLengthErrorPayload(res)
    if (!payload) return false
    const truncated = payload.original_content.slice(0, MAX_SANDBOX_TOTAL_CHARS).trim()
    if (!truncated) return false
    await handleSegmentedTextUpload(truncated, articleTitle)
    return true
  }

  const bodySnapshot = useMemo(() => {
    const trimmed = (body || '').trim()
    if (!trimmed) {
      return {
        contentForUpload: '',
        originalLength: 0,
        finalLength: 0,
        wasTruncated: false,
      }
    }
    if (trimmed.length <= MAX_SANDBOX_TOTAL_CHARS) {
      return {
        contentForUpload: trimmed,
        originalLength: trimmed.length,
        finalLength: trimmed.length,
        wasTruncated: false,
      }
    }
    return {
      contentForUpload: trimmed.slice(0, MAX_SANDBOX_TOTAL_CHARS),
      originalLength: trimmed.length,
      finalLength: MAX_SANDBOX_TOTAL_CHARS,
      wasTruncated: true,
    }
  }, [body])

  const previewSegments = useMemo(
    () => splitArticleIntoSegmentsByMode(bodySnapshot.contentForUpload, splitMode),
    [bodySnapshot.contentForUpload, splitMode]
  )

  const handleSegmentedTextUpload = async (plainText, articleTitle) => {
    const segments = splitArticleIntoSegmentsByMode(plainText, splitMode)
    if (segments.length === 0) {
      setError(t('articleUploadSandboxEmpty'))
      return
    }
    const first = segments[0]
    const res = await apiService.uploadText(
      first,
      articleTitle,
      language,
      true,
      { totalPages: segments.length, pageIndex: 1 },
      splitMode
    )
    const ok = res?.status === 'success' || res?.success
    if (!ok) {
      setError(res?.error || res?.message || t('上传失败'))
      return
    }
    const data = res.data || res
    const articleId = data.article_id ?? data.text_id
    if (!articleId) {
      setError(t('上传失败'))
      return
    }
    if (segments.length > 1) {
      const key = `${SEGMENT_JOB_KEY}${articleId}`
      localStorage.setItem(
        key,
        JSON.stringify({
          remaining: segments.slice(1).map((content, idx) => ({
            content,
            pageIndex: idx + 2,
          })),
          language,
          title: articleTitle,
          splitMode,
          totalPages: segments.length,
          completedPages: 1,
        })
      )
      void runSegmentAppendLoop(articleId)
    }
    if (typeof onNavigateToArticle === 'function') {
      onNavigateToArticle(String(articleId))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (isGuest) {
      setError(t('articleUploadSandboxGuest'))
      return
    }
    setBusy(true)
    try {
      const articleTitle = (title || '').trim() || 'Sandbox Article'
      if (uploadMethod === 'text') {
        await handleSegmentedTextUpload(bodySnapshot.contentForUpload, articleTitle)
      } else if (uploadMethod === 'file') {
        if (!selectedFile) {
          setError(t('articleUploadSandboxFileRequired'))
          return
        }
        const fileName = (selectedFile.name || '').toLowerCase()
        if (fileName.endsWith('.txt') || fileName.endsWith('.md')) {
          const text = await selectedFile.text()
          const trimmed = text.trim().slice(0, MAX_SANDBOX_TOTAL_CHARS)
          await handleSegmentedTextUpload(trimmed, articleTitle)
        } else {
          const res = await apiService.uploadFile(selectedFile, articleTitle, language, splitMode)
          const ok = res?.status === 'success' || res?.success
          if (!ok) {
            const recovered = await tryAutoTruncateAndUpload(res, articleTitle)
            if (recovered) return
            setError(res?.error || res?.message || t('上传失败'))
            return
          }
          const data = res.data || res
          const articleId = data.article_id ?? data.text_id
          if (articleId && typeof onNavigateToArticle === 'function') {
            onNavigateToArticle(String(articleId))
          }
        }
      } else {
        if (!url.trim()) {
          setError(t('articleUploadSandboxUrlRequired'))
          return
        }
        const res = await apiService.uploadUrl(url.trim(), articleTitle, language, splitMode)
        const ok = res?.status === 'success' || res?.success
        if (!ok) {
          const recovered = await tryAutoTruncateAndUpload(res, articleTitle)
          if (recovered) return
          setError(res?.error || res?.message || t('上传失败'))
          return
        }
        const data = res.data || res
        const articleId = data.article_id ?? data.text_id
        if (articleId && typeof onNavigateToArticle === 'function') {
          onNavigateToArticle(String(articleId))
        }
      }
    } catch (err) {
      console.error(err)
      setError(err?.message || String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="mb-6 flex items-center gap-3">
        <BackButton
          onClick={() => {
            if (typeof onBack === 'function') onBack()
          }}
        >
          {t('返回')}
        </BackButton>
        <h1 className="text-xl font-semibold text-gray-900">{t('articleUploadSandboxTitle')}</h1>
      </div>

      <p className="text-sm text-gray-600 mb-4">{t('articleUploadSandboxHint')}</p>

      <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900 mb-4">
        {t('articleUploadSandboxMeta').replace('{n}', String(MAX_SEGMENT_CHARS))} ·{' '}
        {t('articleUploadSandboxSegments').replace('{count}', String(previewSegments.length))} ·{' '}
        {t('articleUploadSandboxTotalLimit').replace('{n}', String(MAX_SANDBOX_TOTAL_CHARS))}
      </div>
      {bodySnapshot.wasTruncated && (
        <div className="rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 text-sm text-orange-900 mb-4">
          {t('articleUploadSandboxAutoTruncated')
            .replace('{original}', String(bodySnapshot.originalLength))
            .replace('{limit}', String(MAX_SANDBOX_TOTAL_CHARS))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center gap-2">
          {['text', 'file', 'url'].map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setUploadMethod(m)}
              className={`px-3 py-1.5 rounded-md text-sm border ${
                uploadMethod === m ? 'bg-green-50 border-green-300 text-green-800' : 'bg-white border-gray-300 text-gray-700'
              }`}
            >
              {m === 'text' ? t('articleUploadMethodText') : m === 'file' ? t('articleUploadMethodFile') : t('articleUploadMethodUrl')}
            </button>
          ))}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t('articleUploadSandboxFieldTitle')}</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="Sandbox Article"
            maxLength={80}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t('语言:')}</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-white"
          >
            {AVAILABLE_LANGUAGES.map((lang) => (
              <option key={lang} value={lang}>
                {t(lang)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t('articleSplitModeLabel')}</label>
          <select
            value={splitMode}
            onChange={(e) => setSplitMode(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-white"
          >
            {SPLIT_MODE_OPTIONS.map((mode) => (
              <option key={mode.id} value={mode.id}>
                {t(mode.labelKey)}
              </option>
            ))}
          </select>
        </div>
        {uploadMethod === 'text' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('articleUploadSandboxFieldBody')}</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={16}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono"
              placeholder={t('articleUploadSandboxPlaceholder')}
            />
          </div>
        )}
        {uploadMethod === 'file' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('articleUploadFileLabel')}</label>
            <input
              type="file"
              accept=".txt,.md,.pdf"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-white"
            />
          </div>
        )}
        {uploadMethod === 'url' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('articleUploadUrlLabel')}</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              placeholder="https://..."
            />
          </div>
        )}
        {error && <div className="text-sm text-red-600">{error}</div>}
        <button
          type="submit"
          disabled={busy}
          className="px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: '#16a34a' }}
        >
          {busy ? t('上传中...') : t('articleUploadSandboxSubmit')}
        </button>
      </form>
    </div>
  )
}
