import { apiService } from '../services/api'

/** 浏览器标签页内共享的语法详情缓存（刷新页面后清空） */
const cache = new Map()
const inFlight = new Map()

const normalizeGrammarId = (grammarId) => Number(grammarId)

export const hasGrammarExamples = (grammar) => {
  const examples = grammar?.examples
  return Array.isArray(examples) && examples.length > 0
}

export const unwrapGrammarDetailResponse = (response) => {
  if (!response) return null
  if (response.rule_id != null && (response.rule_name !== undefined || response.name !== undefined)) {
    return response
  }
  return response?.data?.data || response?.data || response
}

export const getCachedGrammarDetail = (grammarId) => {
  if (grammarId == null) return null
  return cache.get(normalizeGrammarId(grammarId)) || null
}

export const setCachedGrammarDetail = (grammarId, data) => {
  if (grammarId == null || !data) return
  cache.set(normalizeGrammarId(grammarId), data)
}

/** 若已有完整详情则直接返回，否则请求 API 并写入缓存（同 id 并发请求会去重） */
export const fetchGrammarDetail = async (grammarId, { baseGrammar = null } = {}) => {
  const id = normalizeGrammarId(grammarId)
  if (Number.isNaN(id)) return baseGrammar

  const cached = cache.get(id)
  if (cached && hasGrammarExamples(cached)) {
    return baseGrammar ? { ...baseGrammar, ...cached } : cached
  }

  if (inFlight.has(id)) {
    const detailData = await inFlight.get(id)
    if (!detailData) return baseGrammar
    const merged = baseGrammar ? { ...baseGrammar, ...detailData } : detailData
    cache.set(id, merged)
    return merged
  }

  const request = apiService
    .getGrammarById(id)
    .then((response) => unwrapGrammarDetailResponse(response))
    .catch((error) => {
      console.warn('⚠️ [GrammarDetailSessionCache] Failed to load grammar detail:', error)
      return null
    })
    .finally(() => {
      inFlight.delete(id)
    })

  inFlight.set(id, request)

  const detailData = await request
  if (!detailData) {
    if (baseGrammar) {
      cache.set(id, baseGrammar)
      return baseGrammar
    }
    return null
  }

  const merged = baseGrammar ? { ...baseGrammar, ...detailData } : detailData
  cache.set(id, merged)
  return merged
}
