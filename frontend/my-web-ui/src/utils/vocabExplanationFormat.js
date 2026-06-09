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
function tryParsePartialStructured(raw) {
  if (!raw || typeof raw !== 'string') return null
  const text = raw.trim()
  if (!text.startsWith('{') || !STRUCTURED_KEYS.some((key) => text.includes(`"${key}"`))) {
    return null
  }

  const partMatch = text.match(/"part_of_speech"\s*:\s*"((?:\\.|[^"\\])*)"/)
  const extractQuotedItems = (field) => {
    const match = text.match(new RegExp(`"${field}"\\s*:\\s*\\[([\\s\\S]*?)(?:\\]|$)`))
    if (!match) return []
    return [...match[1].matchAll(/"((?:\\.|[^"\\])*)"/g)]
      .map((item) => item[1].replace(/\\"/g, '"').replace(/\\n/g, '\n').trim())
      .filter(Boolean)
  }

  const definitions = extractQuotedItems('definitions')
  const wordFeatures = extractQuotedItems('word_features')
  if (!partMatch && definitions.length === 0 && wordFeatures.length === 0) {
    return null
  }

  return fromStructured({
    part_of_speech: partMatch?.[1]?.replace(/\\"/g, '"') || '',
    word_features: wordFeatures,
    definitions,
    rare_senses: extractQuotedItems('rare_senses'),
    collocations: extractQuotedItems('collocations'),
    grammar_notes: extractQuotedItems('grammar_notes'),
  })
}

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

  const partial = tryParsePartialStructured(text)
  if (partial) return partial

  return {
    ...EMPTY_STRUCTURED,
    legacyText: unwrapLegacyExplanation(text),
  }
}

/** Flatten structured or legacy vocab explanation for list-card preview text. */
export function formatVocabExplanationPreview(raw, { vocabBody = null } = {}) {
  const structured = parseStructuredVocabExplanation(raw)

  let text = ''
  if (structured.isStructured) {
    if (structured.definitions.length > 0) {
      text = structured.definitions.join('；')
    } else if (structured.partOfSpeech) {
      text = structured.partOfSpeech
    } else if (structured.wordFeatures.length > 0) {
      text = structured.wordFeatures.join('；')
    }
  } else {
    text = structured.legacyText || unwrapLegacyExplanation(raw)
  }

  if (vocabBody && text) {
    const escaped = String(vocabBody).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    text = text.replace(new RegExp(`^\\s*${escaped}\\s*[:：]?\\s*\\n?`, 'i'), '').trim()
  }

  return text.replace(/\\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim()
}

/** Convert structured JSON v2 into line-based text for review/detail UI renderers. */
export function formatVocabExplanationForDisplay(raw) {
  const structured = parseStructuredVocabExplanation(raw)

  if (!structured.isStructured) {
    return structured.legacyText || unwrapLegacyExplanation(raw)
  }

  const lines = []

  if (structured.partOfSpeech) {
    lines.push(structured.partOfSpeech)
  }

  if (structured.definitions.length > 0) {
    lines.push('Common senses:')
    structured.definitions.forEach((definition, index) => {
      lines.push(`${index + 1}. ${definition}`)
    })
  }

  if (structured.wordFeatures.length > 0) {
    lines.push('Word features:')
    structured.wordFeatures.forEach((item) => lines.push(`- ${item}`))
  }

  if (structured.rareSenses.length > 0) {
    lines.push('Rare sense:')
    structured.rareSenses.forEach((item) => lines.push(`- ${item}`))
  }

  if (structured.collocations.length > 0) {
    lines.push('Collocations:')
    structured.collocations.forEach((item) => lines.push(`- ${item}`))
  }

  if (structured.grammarNotes.length > 0) {
    lines.push('Grammar notes:')
    structured.grammarNotes.forEach((item) => lines.push(`- ${item}`))
  }

  return lines.join('\n').trim()
}
