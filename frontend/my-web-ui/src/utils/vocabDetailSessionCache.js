import { apiService } from '../services/api'
import { hasAnyHydratedExampleSentence, unwrapVocabDetailResponse } from './vocabExamples'

/** 浏览器标签页内共享的词汇详情缓存（刷新页面后清空） */
const cache = new Map()
const inFlight = new Map()

const normalizeVocabId = (vocabId) => Number(vocabId)

export const getCachedVocabDetail = (vocabId) => {
  if (vocabId == null) return null
  return cache.get(normalizeVocabId(vocabId)) || null
}

export const setCachedVocabDetail = (vocabId, data) => {
  if (vocabId == null || !data) return
  cache.set(normalizeVocabId(vocabId), data)
}

/** 若已有完整详情则直接返回，否则请求 API 并写入缓存（同 id 并发请求会去重） */
export const fetchVocabDetail = async (vocabId, { baseVocab = null } = {}) => {
  const id = normalizeVocabId(vocabId)
  if (Number.isNaN(id)) return baseVocab

  const cached = cache.get(id)
  if (cached && hasAnyHydratedExampleSentence(cached)) {
    return baseVocab ? { ...baseVocab, ...cached } : cached
  }

  if (inFlight.has(id)) {
    const detailData = await inFlight.get(id)
    if (!detailData) return baseVocab
    const merged = baseVocab ? { ...baseVocab, ...detailData } : detailData
    cache.set(id, merged)
    return merged
  }

  const request = apiService.getVocabById(id)
    .then((response) => unwrapVocabDetailResponse(response))
    .catch((error) => {
      console.warn('⚠️ [VocabDetailSessionCache] Failed to load vocab detail:', error)
      return null
    })
    .finally(() => {
      inFlight.delete(id)
    })

  inFlight.set(id, request)

  const detailData = await request
  if (!detailData) {
    if (baseVocab) {
      cache.set(id, baseVocab)
      return baseVocab
    }
    return null
  }

  const merged = baseVocab ? { ...baseVocab, ...detailData } : detailData
  cache.set(id, merged)
  return merged
}
