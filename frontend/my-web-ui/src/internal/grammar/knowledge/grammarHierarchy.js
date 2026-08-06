/**
 * Temporary frontend taxonomy for Tree View.
 * Isolated so it can be replaced when a backend grammar taxonomy exists.
 * Keys may be full canonical_key, subtype slug, or canonical_category.
 */
export const GRAMMAR_CATEGORY_LABELS = {
  clause: 'Modifier / Clause',
  structure: 'Sentence Structure',
  voice: 'Voice',
  aspect: 'Aspect',
  particle: 'Particle',
  complement: 'Complement',
  comparison: 'Comparison',
  disposal: 'Disposal Structure',
  passive: 'Passive',
  question: 'Question Forms',
  tense: 'Tense',
  mood: 'Mood',
  other: 'Other',
}

/**
 * Optional parent overrides by subtype (last segment of canonical_key)
 * or full canonical_key. Values are category bucket ids used in GRAMMAR_CATEGORY_LABELS.
 */
export const GRAMMAR_KEY_PARENT = {
  ba_structure: 'disposal',
  bei_passive: 'passive',
  relative_clause: 'clause',
  relative_clause_de: 'clause',
  shi_de_construction: 'structure',
}

export function subtypeFromCanonicalKey(canonicalKey) {
  if (!canonicalKey) return null
  const parts = String(canonicalKey).split('::').filter(Boolean)
  return parts.length ? parts[parts.length - 1] : null
}

export function resolveHierarchyBucket(row) {
  if (!row || row.is_ungrouped) return 'other'
  const subtype = subtypeFromCanonicalKey(row.canonical_key) || row.canonical_subtype
  if (subtype && GRAMMAR_KEY_PARENT[subtype]) return GRAMMAR_KEY_PARENT[subtype]
  if (row.canonical_key && GRAMMAR_KEY_PARENT[row.canonical_key]) {
    return GRAMMAR_KEY_PARENT[row.canonical_key]
  }
  const cat = (row.canonical_category || '').trim().toLowerCase()
  if (cat && GRAMMAR_CATEGORY_LABELS[cat]) return cat
  if (cat) return cat
  return 'other'
}

export function labelForBucket(bucketId) {
  return GRAMMAR_CATEGORY_LABELS[bucketId] || bucketId || 'Other'
}
