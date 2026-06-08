/**
 * Parse vocab explanation from DB: structured JSON v2 or legacy plain text.
 */

const STRUCTURED_KEYS = [
  'part_of_speech',
  'word_features',
  'definitions',
  'rare_senses',
  'collocations',
  'grammar_notes',
]

const EMPTY_STRUCTURED = {
  isStructured: false,
  partOfSpeech: '',
  wordFeatures: [],
  definitions: [],
  rareSenses: [],
  collocations: [],
  grammarNotes: [],
  legacyText: '',
}

function coerceStringList(value) {
  if (value == null) return []
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean)
  }
  if (typeof value === 'string') {
    const text = value.trim()
    return text ? [text] : []
  }
  if (typeof value === 'object') {
    return Object.values(value)
      .map((item) => String(item).trim())
      .filter(Boolean)
  }
  const text = String(value).trim()
  return text ? [text] : []
}

function tryParseJsonObject(raw) {
  if (!raw || typeof raw !== 'string') return null
  const text = raw.trim()
  if (!text.startsWith('{')) return null
  try {
    const parsed = JSON.parse(text)
    return parsed && typeof parsed === 'object' ? parsed : null
  } catch {
    return null
  }
}

function isStructuredPayload(data) {
  return STRUCTURED_KEYS.some((key) => key in data)
}

function fromStructured(data) {
  return {
    isStructured: true,
    partOfSpeech: String(data.part_of_speech || '').trim(),
    wordFeatures: coerceStringList(data.word_features),
    definitions: coerceStringList(data.definitions),
    rareSenses: coerceStringList(data.rare_senses),
    collocations: coerceStringList(data.collocations),
    grammarNotes: coerceStringList(data.grammar_notes),
    legacyText: '',
  }
}

/** Extract explanation string from legacy {"explanation":"..."} wrapper. */
export function unwrapLegacyExplanation(raw) {
  if (raw == null) return ''
  if (typeof raw !== 'string') return String(raw).trim()

  let cleanText = raw.trim()
  if (!cleanText) return ''

  if (cleanText.startsWith('{') && cleanText.includes('explanation')) {
    const parsed = tryParseJsonObject(cleanText)
    if (parsed?.explanation != null && !isStructuredPayload(parsed)) {
      return String(parsed.explanation).trim()
    }
  }

  return cleanText.replace(/\\n/g, '\n').trim()
}

/**
 * Main entry: structured JSON v2 preferred; legacy text returned in legacyText.
 */
export function parseStructuredVocabExplanation(raw) {
  if (raw == null || raw === '') return { ...EMPTY_STRUCTURED }

  if (typeof raw === 'object' && !Array.isArray(raw)) {
    if (isStructuredPayload(raw)) return fromStructured(raw)
    if (raw.explanation != null) {
      return parseStructuredVocabExplanation(String(raw.explanation))
    }
  }

  const text = String(raw).trim()
  if (!text) return { ...EMPTY_STRUCTURED }

  const parsed = tryParseJsonObject(text)
  if (parsed) {
    if (isStructuredPayload(parsed)) return fromStructured(parsed)
    if (parsed.explanation != null) {
      return parseStructuredVocabExplanation(String(parsed.explanation))
    }
  }

  return {
    ...EMPTY_STRUCTURED,
    legacyText: unwrapLegacyExplanation(text),
  }
}
