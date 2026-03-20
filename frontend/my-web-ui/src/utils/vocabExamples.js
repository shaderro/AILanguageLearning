/**
 * 词汇例句字段兼容：列表接口 DTO 常与详情 API 字段不一致（缺 original_sentence）。
 */

export function pickExampleSentenceText(ex) {
  if (!ex || typeof ex !== 'object') return ''
  const candidates = [
    ex.original_sentence,
    ex.sentence_body,
    ex.sentence,
    ex.text,
    ex.original_text,
    ex.example_sentence,
  ]
  for (const c of candidates) {
    if (c != null && String(c).trim()) return String(c).trim()
  }
  return ''
}

/** 是否已有「可展示的原句」（非仅 text_id / context 元数据） */
export function hasAnyHydratedExampleSentence(vocabItem) {
  const list = vocabItem?.examples
  if (!Array.isArray(list) || list.length === 0) return false
  return list.some((ex) => Boolean(pickExampleSentenceText(ex)))
}

/** 兼容 axios 拦截器返回 { data: mappedVocab } 或裸对象 */
export function unwrapVocabDetailResponse(response) {
  if (!response) return null
  if (response.vocab_id != null && response.vocab_body !== undefined) return response
  if (response.data?.vocab_id != null && response.data?.vocab_body !== undefined) return response.data
  return response?.data?.data || response?.data || response
}
