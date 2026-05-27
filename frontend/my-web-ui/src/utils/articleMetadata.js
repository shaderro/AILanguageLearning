import presetArticleMetadata from '../data/presetArticleMetadata.json'

const DIFFICULTY_SLUGS = new Set(['beginner', 'intermediate', 'advanced'])

const LANGUAGE_ALIASES = {
  中文: 'zh',
  英文: 'en',
  英语: 'en',
  德文: 'de',
  德语: 'de',
  西班牙语: 'es',
  法语: 'fr',
  日语: 'ja',
  日文: 'ja',
  韩语: 'ko',
  阿拉伯语: 'ar',
  俄语: 'ru',
}

const presetLookup = new Map()
for (const row of presetArticleMetadata) {
  const title = String(row.title || '').trim()
  const code = row.language_code || LANGUAGE_ALIASES[row.language_name] || null
  if (!title) continue
  if (code) presetLookup.set(`${code}\0${title}`, row)
  if (row.language_name) presetLookup.set(`${row.language_name}\0${title}`, row)
}

export const normalizeDifficultySlug = (value) => {
  if (value === undefined || value === null || value === '') return null
  const slug = String(value).trim().toLowerCase()
  return DIFFICULTY_SLUGS.has(slug) ? slug : null
}

export const lookupPresetArticleMetadata = (language, title) => {
  const trimmedTitle = String(title || '').trim()
  if (!trimmedTitle) return null

  const code = LANGUAGE_ALIASES[language] || null
  if (code) {
    const hit = presetLookup.get(`${code}\0${trimmedTitle}`)
    if (hit) return hit
  }
  if (language) {
    const hit = presetLookup.get(`${language}\0${trimmedTitle}`)
    if (hit) return hit
  }
  return null
}

/** Resolve difficulty for list cards: API field first, then preset catalog fallback. */
export const resolveArticleDifficulty = (article) => {
  if (!article) return null

  const fromApi = normalizeDifficultySlug(
    article.difficulty ?? article.difficulty_level ?? article.level,
  )
  if (fromApi) return fromApi

  const title = article.text_title || article.title
  const language = article.language
  const preset = lookupPresetArticleMetadata(language, title)
  return normalizeDifficultySlug(preset?.difficulty)
}

export const enrichArticleListItem = (item) => {
  if (!item || typeof item !== 'object') return item
  const difficulty = resolveArticleDifficulty(item)
  return difficulty ? { ...item, difficulty } : item
}
