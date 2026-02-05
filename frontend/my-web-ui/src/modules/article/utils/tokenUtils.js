/**
 * Token utility functions for ArticleViewer
 */

/**
 * Generate unique key for token rendering
 *
 * 🔧 重要：key 必须只依赖「不会变」的标识，否则一旦
 * token 对象在后续被扩展（例如挂上 vocab/grammar 信息），
 * React 会认为这是一个全新的元素，从而卸载 / 重新挂载
 * 对应的 `TokenSpan`，导致其内部 state（如 showNotation）丢失。
 *
 * 这里我们只使用句子索引 + sentence_token_id（或退化到 tokenIdx）
 * 来构造 key，保证在同一篇文章生命周期内是稳定的。
 */
export const getTokenKey = (sentIdx, token, tokenIdx) => {
  const base = `${sentIdx}-`

  // 纯字符串 token（例如空格、标点）没有 sentence_token_id，用索引即可
  if (typeof token === 'string') return `${base}${tokenIdx}`

  if (token && typeof token === 'object') {
    const sid = token?.sentence_token_id
    if (sid != null) {
      return `${base}${sid}`
    }
    // 理论上不应该走到这里，兜底使用 tokenIdx，至少在同一句内部稳定
    return `${base}${tokenIdx}`
  }

  return `${base}${tokenIdx}`
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

