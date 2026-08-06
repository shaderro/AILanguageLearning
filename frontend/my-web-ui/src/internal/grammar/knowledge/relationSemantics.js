/**
 * Semantic relation helpers for the hierarchical graph.
 * Frontend-only heuristics — replace when backend taxonomy/relations exist.
 */

/** Subtype pairs that contrast with each other (belongs to different patterns). */
export const CONTRAST_SUBTYPE_PAIRS = [
  ['ba_structure', 'bei_passive'],
  ['disposal', 'passive'],
]

/** Category-level contrast clusters. */
export const CONTRAST_CATEGORY_PAIRS = [['disposal', 'passive']]

export const RELATION = {
  BELONGS_TO: 'belongs_to',
  SIMILAR_TO: 'similar_to',
  CONTRAST_WITH: 'contrast_with',
  RELATED_TO: 'related_to',
}

export const RELATION_META = {
  belongs_to: { label: 'belongs to', stroke: '#a1a1aa', dash: '', width: 1.6 },
  similar_to: { label: 'similar to', stroke: '#64748b', dash: '4 3', width: 1.2 },
  contrast_with: { label: 'contrast', stroke: '#b45309', dash: '2 3', width: 1.4 },
  related_to: { label: 'related', stroke: '#d4d4d8', dash: '1 4', width: 1 },
}

function norm(s) {
  return String(s || '')
    .trim()
    .toLowerCase()
}

export function subtypeSlug(rowOrKey) {
  if (!rowOrKey) return ''
  if (typeof rowOrKey === 'string') {
    const parts = rowOrKey.split('::').filter(Boolean)
    return norm(parts[parts.length - 1] || rowOrKey)
  }
  const fromKey = subtypeSlug(rowOrKey.canonical_key)
  if (fromKey) return fromKey
  return norm(rowOrKey.canonical_subtype)
}

export function isContrastPair(a, b) {
  const sa = subtypeSlug(a)
  const sb = subtypeSlug(b)
  if (!sa || !sb || sa === sb) return false
  return CONTRAST_SUBTYPE_PAIRS.some(
    ([x, y]) => (sa === x && sb === y) || (sa === y && sb === x)
  )
}

export function isContrastCategoryPair(a, b) {
  const ca = norm(a)
  const cb = norm(b)
  if (!ca || !cb || ca === cb) return false
  return CONTRAST_CATEGORY_PAIRS.some(
    ([x, y]) => (ca === x && cb === y) || (ca === y && cb === x)
  )
}

/**
 * Relation between two grammar-pattern rows (neither is category/example).
 */
export function inferPatternRelation(a, b) {
  if (isContrastPair(a, b)) return RELATION.CONTRAST_WITH

  const fnA = norm(a.canonical_function || a.function)
  const fnB = norm(b.canonical_function || b.function)
  if (fnA && fnB && fnA === fnB) return RELATION.SIMILAR_TO

  const levelsA = new Set((a.derived_levels || []).map(norm))
  for (const lv of b.derived_levels || []) {
    if (levelsA.has(norm(lv))) return RELATION.RELATED_TO
  }

  const catA = norm(a.canonical_category || a.category)
  const catB = norm(b.canonical_category || b.category)
  if (catA && catB && catA === catB) return RELATION.RELATED_TO

  return null
}
