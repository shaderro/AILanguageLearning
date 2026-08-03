/**
 * Parse grammar explanation from a single rule_summary / grammar_explanation string.
 * Supports titled sections (Core Meaning, Structure, …) and legacy line-based output.
 */

import { splitExplanationLines, stripExplanationLinePrefix } from './explanationFormat'

export const GRAMMAR_SECTION_KEYS = [
  'coreMeaning',
  'structure',
  'sentenceMapping',
  'recognitionTip',
]

export const GRAMMAR_SECTION_TITLES = {
  coreMeaning: 'Core Meaning',
  structure: 'Structure',
  sentenceMapping: 'Sentence Mapping',
  recognitionTip: 'Recognition Tip',
}

/** Section heading copy keyed by explanation content language (not app UI language). */
export const GRAMMAR_SECTION_LABELS = {
  zh: {
    coreMeaning: '核心含义',
    structure: '结构',
    sentenceMapping: '句子映射',
    recognitionTip: '识别提示',
    examples: '例句',
    ruleDescription: '规则说明',
  },
  en: {
    coreMeaning: 'Core meaning',
    structure: 'Structure',
    sentenceMapping: 'Sentence mapping',
    recognitionTip: 'Recognition tip',
    examples: 'Example sentences',
    ruleDescription: 'Rule description',
  },
}

export function getGrammarSectionLabels(contentLanguage = 'zh') {
  return GRAMMAR_SECTION_LABELS[contentLanguage === 'en' ? 'en' : 'zh']
}

const SECTION_ALIASES = {
  coreMeaning: [
    'core meaning',
    '核心含义',
    'grammar explanation',
    '语法说明',
    'grammar',
    'observation',
    '观察指引',
  ],
  structure: ['structure', '结构'],
  sentenceMapping: ['sentence mapping', '句子映射'],
  recognitionTip: [
    'recognition tip',
    '识别提示',
    'memory',
    '记忆',
    '记忆提示',
  ],
}

/** Sections omitted from detail card (examples shown separately). */
const SKIP_SECTION_ALIASES = new Set([
  'example',
  'examples',
  '例句',
  'example sentence',
  'example sentences',
])

const EMPTY_STRUCTURED = {
  isStructured: false,
  coreMeaning: [],
  structure: [],
  sentenceMapping: '',
  recognitionTip: [],
  legacyText: '',
  sections: [],
  contentLanguage: 'zh',
  sectionLabels: GRAMMAR_SECTION_LABELS.zh,
}

function aliasLanguage(alias) {
  return /[\u4e00-\u9fff]/.test(alias) ? 'zh' : 'en'
}

function detectContentLanguage(text, headingLanguageVotes = { zh: 0, en: 0 }) {
  if (headingLanguageVotes.zh > headingLanguageVotes.en) return 'zh'
  if (headingLanguageVotes.en > headingLanguageVotes.zh) return 'en'

  const sample = String(text || '').slice(0, 2000)
  const cjkCount = (sample.match(/[\u4e00-\u9fff]/g) || []).length
  const latinWordCount = (sample.match(/\b[a-zA-Z]{2,}\b/g) || []).length

  if (cjkCount >= 2 && cjkCount >= latinWordCount) return 'zh'
  return 'en'
}

function createLanguageTracker() {
  return {
    zh: 0,
    en: 0,
    note(alias) {
      this[aliasLanguage(alias)] += 1
    },
  }
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

function normalizeHeadingKey(line) {
  return String(line || '')
    .trim()
    .replace(/^\*\*/, '')
    .replace(/\*\*$/, '')
    .replace(/[:：]\s*$/, '')
    .trim()
    .toLowerCase()
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function resolveSectionKey(line, languageTracker = null) {
  const trimmed = String(line || '').trim()
  if (!trimmed) return null

  const headingKey = normalizeHeadingKey(trimmed)
  if (SKIP_SECTION_ALIASES.has(headingKey)) {
    return { sectionKey: '__skip__', inlineContent: '' }
  }

  for (const [sectionKey, aliases] of Object.entries(SECTION_ALIASES)) {
    const matchedAlias = aliases.find((alias) => headingKey === alias)
    if (matchedAlias) {
      languageTracker?.note(matchedAlias)
      return { sectionKey, inlineContent: '' }
    }
  }

  for (const [sectionKey, aliases] of Object.entries(SECTION_ALIASES)) {
    for (const alias of aliases) {
      const pattern = new RegExp(
        `^\\*{0,2}${escapeRegExp(alias)}\\*{0,2}\\s*[:：]\\s*(.+)$`,
        'i',
      )
      const match = trimmed.match(pattern)
      if (match) {
        languageTracker?.note(alias)
        return { sectionKey, inlineContent: match[1].trim() }
      }
    }
  }

  return null
}

function joinSectionLines(lines) {
  return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim()
}

function toBulletPoints(text) {
  return splitExplanationLines(text)
}

function expandInlineSectionMarkers(text) {
  const labelPattern = (
    '(?:核心含义|core meaning|结构|structure|句子映射|sentence mapping|'
    + '识别提示|recognition tip|记忆|memory|记忆提示|语法说明|grammar explanation|grammar|'
    + 'observation|观察指引|example|examples|例句)'
  )
  return String(text || '')
    .replace(/\r\n/g, '\n')
    .replace(new RegExp(`\\s+(?=${labelPattern}\\s*[:：])`, 'gi'), '\n')
    .replace(new RegExp(`([。；;])\\s*(?=${labelPattern}\\s*[:：])`, 'gi'), '$1\n')
}

function isMappingLine(line) {
  const trimmed = String(line || '').trim()
  if (!trimmed) return false
  if (!/→|->|—>|=>/.test(trimmed)) return false

  const arrowCount = (trimmed.match(/→|->|—>|=>/g) || []).length
  if (arrowCount >= 2) return true
  if (/^(?:主语|宾语|Subject|Object|Agent|Patient|Predicate)/i.test(trimmed)) return true
  if (/（.+）\s*→/.test(trimmed)) return true

  return false
}

function isStructurePatternLine(line) {
  const trimmed = String(line || '').trim()
  if (!trimmed) return false
  if (/^(?:结构|structure)\s*[:：]/i.test(trimmed)) return true
  return /\+/.test(trimmed) && /[A-Za-z\u4e00-\u9fff]/.test(trimmed) && trimmed.length <= 80
}

function isGrammarRoleLine(line) {
  const trimmed = String(line || '').trim()
  return /\*\*.+\*\*\s*[=＝]/.test(trimmed) || /^.+\s*[=＝]\s*.+/.test(trimmed)
}

function parseBySectionHeadings(text) {
  const normalizedText = expandInlineSectionMarkers(text)
  const lines = normalizedText.split('\n')
  const languageTracker = createLanguageTracker()
  const buckets = {
    coreMeaning: [],
    structure: [],
    sentenceMapping: [],
    recognitionTip: [],
  }

  let currentKey = null

  const pushLine = (key, line) => {
    if (!line) return
    buckets[key].push(stripExplanationLinePrefix(line))
  }

  lines.forEach((rawLine) => {
    const trimmed = rawLine.trim()
    if (!trimmed) {
      if (currentKey && currentKey !== '__skip__' && buckets[currentKey].length > 0) {
        buckets[currentKey].push('')
      }
      return
    }

    const resolved = resolveSectionKey(trimmed, languageTracker)
    if (resolved) {
      if (resolved.sectionKey === '__skip__') {
        currentKey = '__skip__'
        return
      }
      currentKey = resolved.sectionKey
      if (resolved.inlineContent) {
        pushLine(currentKey, resolved.inlineContent)
      }
      return
    }

    if (currentKey === '__skip__') {
      return
    }

    if (currentKey) {
      pushLine(currentKey, trimmed)
    } else {
      pushLine('coreMeaning', trimmed)
    }
  })

  const hasExplicitHeading = lines.some((line) => resolveSectionKey(line))
  if (!hasExplicitHeading) return null

  const coreMeaning = toBulletPoints(joinSectionLines(buckets.coreMeaning))
  const structure = toBulletPoints(joinSectionLines(buckets.structure))
  const sentenceMapping = joinSectionLines(buckets.sentenceMapping)
  const recognitionTip = toBulletPoints(joinSectionLines(buckets.recognitionTip))

  const hasContent = (
    coreMeaning.length > 0
    || structure.length > 0
    || Boolean(sentenceMapping)
    || recognitionTip.length > 0
  )

  if (!hasContent) return null

  return {
    coreMeaning,
    structure,
    sentenceMapping,
    recognitionTip,
    headingLanguageVotes: languageTracker,
  }
}

function noteInlineLabelLanguage(label, languageTracker) {
  if (/[\u4e00-\u9fff]/.test(label)) {
    languageTracker.zh += 1
  } else {
    languageTracker.en += 1
  }
}

function parseLegacyHeuristic(text) {
  const normalizedText = expandInlineSectionMarkers(text)
  const lines = normalizedText
    .split('\n')
    .map((line) => stripExplanationLinePrefix(line))
    .filter(Boolean)

  if (lines.length === 0) return null

  const languageTracker = createLanguageTracker()
  const buckets = {
    coreMeaning: [],
    structure: [],
    sentenceMapping: [],
    recognitionTip: [],
  }

  let skippingExample = false

  lines.forEach((line) => {
    if (/^(?:example|examples|例句)\s*[:：]?$/i.test(line)) {
      if (/例句/.test(line)) languageTracker.note('例句')
      else languageTracker.note('example')
      skippingExample = true
      return
    }

    if (skippingExample) {
      if (
        /^(?:核心含义|core meaning|结构|structure|句子映射|sentence mapping|识别提示|recognition tip|记忆|memory|语法说明|grammar explanation|grammar|observation|观察指引)\s*[:：]/i.test(line)
        || isMappingLine(line)
        || isStructurePatternLine(line)
      ) {
        skippingExample = false
      } else {
        return
      }
    }

    if (/^(?:example|examples|例句)\s*[:：]\s*/i.test(line)) {
      return
    }

    const inlineStructure = line.match(/^(结构|structure)\s*[:：]\s*(.+)$/i)
    if (inlineStructure) {
      noteInlineLabelLanguage(inlineStructure[1], languageTracker)
      buckets.structure.push(inlineStructure[2].trim())
      return
    }

    const inlineMapping = line.match(/^(句子映射|sentence mapping)\s*[:：]\s*(.+)$/i)
    if (inlineMapping) {
      noteInlineLabelLanguage(inlineMapping[1], languageTracker)
      buckets.sentenceMapping.push(inlineMapping[2].trim())
      return
    }

    const inlineTip = line.match(/^(识别提示|recognition tip|记忆|memory)\s*[:：]\s*(.+)$/i)
    if (inlineTip) {
      noteInlineLabelLanguage(inlineTip[1], languageTracker)
      buckets.recognitionTip.push(inlineTip[2].trim())
      return
    }

    const inlineCore = line.match(
      /^(核心含义|core meaning|语法说明|grammar explanation|grammar|observation|观察指引)\s*[:：]\s*(.+)$/i,
    )
    if (inlineCore) {
      noteInlineLabelLanguage(inlineCore[1], languageTracker)
      buckets.coreMeaning.push(inlineCore[2].trim())
      return
    }

    if (isMappingLine(line)) {
      buckets.sentenceMapping.push(line)
      return
    }

    if (isStructurePatternLine(line)) {
      buckets.structure.push(line.replace(/^(?:结构|structure)\s*[:：]\s*/i, '').trim())
      return
    }

    if (isGrammarRoleLine(line)) {
      buckets.coreMeaning.push(line)
      return
    }

    buckets.coreMeaning.push(line)
  })

  const coreMeaning = buckets.coreMeaning.filter(Boolean)
  const structure = buckets.structure.filter(Boolean)
  const sentenceMapping = joinSectionLines(buckets.sentenceMapping)
  const recognitionTip = buckets.recognitionTip.filter(Boolean)

  const classifiedCount = [
    coreMeaning.length > 0,
    structure.length > 0,
    Boolean(sentenceMapping),
    recognitionTip.length > 0,
  ].filter(Boolean).length

  if (classifiedCount < 2 && !sentenceMapping) {
    return null
  }

  return {
    coreMeaning,
    structure,
    sentenceMapping,
    recognitionTip,
    headingLanguageVotes: languageTracker,
  }
}

function buildSections(
  { coreMeaning, structure, sentenceMapping, recognitionTip },
  contentLanguage = 'zh',
) {
  const labels = getGrammarSectionLabels(contentLanguage)
  const sections = []

  if (coreMeaning.length > 0) {
    sections.push({
      title: labels.coreMeaning,
      content: coreMeaning.join('\n'),
    })
  }
  if (structure.length > 0) {
    sections.push({
      title: labels.structure,
      content: structure.join('\n'),
    })
  }
  if (sentenceMapping) {
    sections.push({
      title: labels.sentenceMapping,
      content: sentenceMapping,
    })
  }
  if (recognitionTip.length > 0) {
    sections.push({
      title: labels.recognitionTip,
      content: recognitionTip.join('\n'),
    })
  }

  return sections
}

/** Extract explanation string from legacy {"grammar_explanation":"..."} wrapper. */
export function unwrapGrammarExplanation(raw) {
  if (raw == null) return ''
  if (typeof raw === 'object' && !Array.isArray(raw)) {
    if (raw.grammar_explanation != null) {
      return unwrapGrammarExplanation(String(raw.grammar_explanation))
    }
    if (raw.explanation != null) {
      return unwrapGrammarExplanation(String(raw.explanation))
    }
    return ''
  }
  if (typeof raw !== 'string') return String(raw).trim()

  let cleanText = raw.trim()
  if (!cleanText) return ''

  const extractWrappedField = (fieldName) => {
    if (!cleanText.includes(fieldName)) return null

    const parsed = tryParseJsonObject(cleanText)
    if (parsed?.[fieldName] != null) {
      return String(parsed[fieldName]).replace(/\\n/g, '\n').trim()
    }

    const patterns = [
      new RegExp(`['"]${fieldName}['"]\\s*:\\s*"([\\s\\S]*?)"\\s*[,}]`),
      new RegExp(`['"]${fieldName}['"]\\s*:\\s*"([\\s\\S]*?)$`),
      new RegExp(`['"]${fieldName}['"]\\s*:\\s*'([\\s\\S]*?)'\\s*[,}]`),
      new RegExp(`['"]${fieldName}['"]\\s*:\\s*'([\\s\\S]*?)$`),
    ]

    for (const pattern of patterns) {
      const match = cleanText.match(pattern)
      if (match?.[1]) {
        return match[1]
          .replace(/\\n/g, '\n')
          .replace(/\\'/g, "'")
          .replace(/\\"/g, '"')
          .trim()
      }
    }

    return null
  }

  if (cleanText.startsWith('{')) {
    const grammarText = extractWrappedField('grammar_explanation')
    if (grammarText) return grammarText

    const explanationText = extractWrappedField('explanation')
    if (explanationText) return explanationText
  }

  return cleanText.replace(/\\n/g, '\n').trim()
}

/** Parse grammar explanation into section buckets for Grammar Detail UI. */
export function parseStructuredGrammarExplanation(raw) {
  if (raw == null || raw === '') return { ...EMPTY_STRUCTURED }

  if (typeof raw === 'object' && !Array.isArray(raw)) {
    if (raw.grammar_explanation != null) {
      return parseStructuredGrammarExplanation(String(raw.grammar_explanation))
    }
    if (raw.explanation != null) {
      return parseStructuredGrammarExplanation(String(raw.explanation))
    }
  }

  const text = unwrapGrammarExplanation(raw)
  if (!text) return { ...EMPTY_STRUCTURED }

  const titled = parseBySectionHeadings(text)
  const parsed = titled || parseLegacyHeuristic(text)

  if (!parsed) {
    const contentLanguage = detectContentLanguage(text)
    return {
      ...EMPTY_STRUCTURED,
      legacyText: text,
      contentLanguage,
      sectionLabels: getGrammarSectionLabels(contentLanguage),
    }
  }

  const contentLanguage = detectContentLanguage(text, parsed.headingLanguageVotes)
  const sectionLabels = getGrammarSectionLabels(contentLanguage)
  const sections = buildSections(parsed, contentLanguage)

  return {
    isStructured: sections.length > 0,
    coreMeaning: parsed.coreMeaning,
    structure: parsed.structure,
    sentenceMapping: parsed.sentenceMapping,
    recognitionTip: parsed.recognitionTip,
    legacyText: '',
    sections,
    contentLanguage,
    sectionLabels,
  }
}

/** Parse into [{ title, content }] for generic section renderers. */
export function parseGrammarExplanationSections(raw) {
  const structured = parseStructuredGrammarExplanation(raw)
  if (structured.isStructured && structured.sections.length > 0) {
    return structured.sections
  }
  if (structured.legacyText) {
    return [{ title: '', content: structured.legacyText }]
  }
  return []
}

/** Flatten structured grammar explanation for list-card preview text. */
export function formatGrammarExplanationPreview(raw) {
  const structured = parseStructuredGrammarExplanation(raw)

  const cleanPreviewLine = (text) => (
    String(text || '')
      .replace(/\*\*/g, '')
      .replace(/\s+/g, ' ')
      .trim()
  )

  if (structured.isStructured) {
    if (structured.coreMeaning.length > 0) {
      return cleanPreviewLine(structured.coreMeaning.join(' '))
    }
    if (structured.sentenceMapping) {
      return cleanPreviewLine(structured.sentenceMapping.split('\n')[0])
    }
    if (structured.structure.length > 0) {
      return cleanPreviewLine(structured.structure.join(' '))
    }
    if (structured.recognitionTip.length > 0) {
      return cleanPreviewLine(structured.recognitionTip.join(' '))
    }
  }

  const fallback = structured.legacyText || unwrapGrammarExplanation(raw)
  if (!fallback) return ''

  const expanded = expandInlineSectionMarkers(fallback)
  const firstLine = expanded.split('\n').map((line) => line.trim()).find(Boolean) || fallback
  return cleanPreviewLine(
    firstLine
      .replace(/^(?:观察指引|核心含义|core meaning|grammar|grammar explanation|语法说明|observation)\s*[:：]\s*/i, '')
      .replace(/^(?:例句|example|examples)\s*[:：]\s*/i, ''),
  )
}
