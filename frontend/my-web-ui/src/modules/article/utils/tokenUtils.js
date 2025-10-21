/**
 * Token utility functions for ArticleViewer
 */

/**
 * Generate unique key for token rendering
 */
export const getTokenKey = (sentIdx, token, tokenIdx) => {
  const base = `${sentIdx}-`
  if (typeof token === 'string') return `${base}-`
  if (token && typeof token === 'object') {
    const t = token?.token_body ?? ''
    const gid = token?.global_token_id ?? ''
    const sid = token?.sentence_token_id ?? ''
    return `${base}-${t}-${gid}-${sid}`
  }
  return base
}

/**
 * Get unique identifier for a token object
 * 使用 句子维度复合键：`${sentenceIdx}-${sentence_token_id}`
 */
export const getTokenId = (token, sentenceIdx) => {
  if (!token || typeof token !== 'object') return undefined
  const sid = token?.sentence_token_id
  if (sid == null) return undefined
  // 如果提供了句子索引，则返回复合键，避免跨句冲突
  if (sentenceIdx != null) return `${sentenceIdx}-${sid}`
  // 向后兼容（不推荐）：仅返回 sentence_token_id
  const fallback = String(sid)
  console.debug('[tokenUtils.getTokenId] Missing sentenceIdx, fallback to sid only:', fallback)
  return fallback
}

/**
 * Check if two rectangles overlap
 */
export const rectsOverlap = (a, b) => {
  return !(b.left > a.right ||
           b.right < a.left ||
           b.top > a.bottom ||
           b.bottom < a.top)
}

