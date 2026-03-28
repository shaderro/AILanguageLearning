import { apiService } from '../services/api'

const PREVIEW_CACHE_KEY = 'articlePreviewCache'
const previewCache = new Map()
const inFlightRequests = new Map()
let previewCacheLoaded = false

const normalizeArticleId = (articleId) => String(articleId)

const extractFirstSentence = (response) => {
  const sentences =
    response?.data?.data?.sentences ||
    response?.data?.sentences ||
    response?.data ||
    response?.sentences ||
    []

  if (!Array.isArray(sentences) || sentences.length === 0) {
    return null
  }

  return sentences[0]?.sentence_body || sentences[0]?.text || sentences[0]?.sentence || null
}

export const ensureArticlePreviewCacheLoaded = () => {
  if (previewCacheLoaded || typeof window === 'undefined') {
    return
  }

  try {
    const raw = window.localStorage.getItem(PREVIEW_CACHE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      Object.entries(parsed).forEach(([id, value]) => {
        if (typeof value === 'string' && value.trim()) {
          previewCache.set(id, value)
        }
      })
    }
  } catch (error) {
    console.warn('⚠️ [ArticlePreviewCache] 读取摘要缓存失败:', error)
  } finally {
    previewCacheLoaded = true
  }
}

const persistArticlePreviewCache = () => {
  if (typeof window === 'undefined') {
    return
  }

  try {
    const serialized = JSON.stringify(Object.fromEntries(previewCache))
    window.localStorage.setItem(PREVIEW_CACHE_KEY, serialized)
  } catch (error) {
    console.warn('⚠️ [ArticlePreviewCache] 保存摘要缓存失败:', error)
  }
}

export const getCachedArticlePreview = (articleId) => {
  ensureArticlePreviewCacheLoaded()
  return previewCache.get(normalizeArticleId(articleId)) || null
}

export const hydrateArticlePreviewCache = (articles = []) => {
  ensureArticlePreviewCacheLoaded()

  let changed = false
  articles.forEach(({ id, preview }) => {
    if (!id || typeof preview !== 'string' || !preview.trim()) {
      return
    }

    const key = normalizeArticleId(id)
    if (previewCache.get(key) === preview) {
      return
    }

    previewCache.set(key, preview)
    changed = true
  })

  if (changed) {
    persistArticlePreviewCache()
  }
}

export const fetchArticlePreview = async (articleId) => {
  ensureArticlePreviewCacheLoaded()

  const key = normalizeArticleId(articleId)
  const cached = previewCache.get(key)
  if (cached) {
    return cached
  }

  if (inFlightRequests.has(key)) {
    return inFlightRequests.get(key)
  }

  const request = apiService.getArticleSentences(articleId, { limit: 1 })
    .then((response) => {
      const firstSentence = extractFirstSentence(response)
      if (firstSentence) {
        previewCache.set(key, firstSentence)
        persistArticlePreviewCache()
      }
      return firstSentence
    })
    .finally(() => {
      inFlightRequests.delete(key)
    })

  inFlightRequests.set(key, request)
  return request
}
