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
 */
export const getTokenId = (token) => {
  if (!token || typeof token !== 'object') return undefined
  const gid = token?.global_token_id
  const sid = token?.sentence_token_id
  return (gid != null && sid != null) ? `${gid}-${sid}` : undefined
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

