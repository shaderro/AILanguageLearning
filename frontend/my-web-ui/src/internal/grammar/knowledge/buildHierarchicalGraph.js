/**
 * Hierarchical graph model for progressive exploration.
 * Default: category clusters only. Expand → patterns → examples.
 */
import { labelForBucket, resolveHierarchyBucket } from './grammarHierarchy'
import {
  RELATION,
  inferPatternRelation,
  isContrastCategoryPair,
} from './relationSemantics'

export function groupRowsByCategory(rows = []) {
  const map = new Map()
  for (const row of rows || []) {
    if (!row || row.is_ungrouped || !row.canonical_key) continue
    const bucket = resolveHierarchyBucket(row)
    if (!map.has(bucket)) map.set(bucket, [])
    map.get(bucket).push(row)
  }
  return map
}

function edgeId(source, target, relation) {
  return `${source}|${relation}|${target}`
}

/**
 * @param {object} opts
 * @param {Array} opts.rows - dashboard list rows
 * @param {Set<string>} opts.expandedCategories - bucket ids
 * @param {Set<string>} opts.expandedPatterns - canonical_key
 * @param {Map<string, Array>} opts.examplesByPattern - canonical_key -> examples
 * @param {number} [opts.maxExamplesPerPattern=5]
 */
export function buildHierarchicalGraph({
  rows = [],
  expandedCategories = new Set(),
  expandedPatterns = new Set(),
  examplesByPattern = new Map(),
  maxExamplesPerPattern = 5,
} = {}) {
  const groups = groupRowsByCategory(rows)
  const nodes = []
  const edges = []
  const nodeIds = new Set()

  const addNode = (node) => {
    if (nodeIds.has(node.id)) return
    nodeIds.add(node.id)
    nodes.push(node)
  }

  const addEdge = (source, target, relation) => {
    if (!nodeIds.has(source) || !nodeIds.has(target) || source === target) return
    const id = edgeId(source, target, relation)
    if (edges.some((e) => e.id === id)) return
    edges.push({ id, source, target, relation })
  }

  const categoryIds = Array.from(groups.keys())

  // --- Category cluster nodes (always visible) ---
  for (const bucketId of categoryIds) {
    const bucketRows = groups.get(bucketId) || []
    const exampleTotal = bucketRows.reduce((s, r) => s + (r.example_count || 0), 0)
    const levels = new Set()
    for (const r of bucketRows) {
      for (const lv of r.derived_levels || []) levels.add(lv)
    }
    addNode({
      id: `cat:${bucketId}`,
      type: 'category',
      bucketId,
      label: labelForBucket(bucketId),
      patternCount: bucketRows.length,
      example_count: exampleTotal,
      derived_levels: Array.from(levels),
      expanded: expandedCategories.has(bucketId),
    })
  }

  // Category ↔ category edges (sparse): contrast + weak related via shared levels
  for (let i = 0; i < categoryIds.length; i += 1) {
    for (let j = i + 1; j < categoryIds.length; j += 1) {
      const a = categoryIds[i]
      const b = categoryIds[j]
      if (isContrastCategoryPair(a, b)) {
        addEdge(`cat:${a}`, `cat:${b}`, RELATION.CONTRAST_WITH)
        continue
      }
      const levelsA = new Set(
        (groups.get(a) || []).flatMap((r) => (r.derived_levels || []).map((x) => String(x).toLowerCase()))
      )
      const shared = (groups.get(b) || []).some((r) =>
        (r.derived_levels || []).some((lv) => levelsA.has(String(lv).toLowerCase()))
      )
      if (shared) {
        addEdge(`cat:${a}`, `cat:${b}`, RELATION.RELATED_TO)
      }
    }
  }

  // --- Expanded category → grammar patterns ---
  for (const bucketId of categoryIds) {
    if (!expandedCategories.has(bucketId)) continue
    const bucketRows = groups.get(bucketId) || []
    const catNodeId = `cat:${bucketId}`

    for (const row of bucketRows) {
      const patternId = `pat:${row.canonical_key}`
      addNode({
        id: patternId,
        type: 'grammar',
        label: row.title || row.display_name || row.rule_name || row.canonical_key,
        canonical_key: row.canonical_key,
        category: row.canonical_category,
        subtype: row.canonical_subtype,
        function: row.canonical_function,
        example_count: row.example_count ?? 0,
        derived_levels: row.derived_levels || [],
        description_preview: row.description_preview || '',
        parentCategoryId: catNodeId,
        expanded: expandedPatterns.has(row.canonical_key),
        _row: row,
      })
      addEdge(patternId, catNodeId, RELATION.BELONGS_TO)
    }

    // Intra-category pattern relations (only among visible patterns)
    for (let i = 0; i < bucketRows.length; i += 1) {
      for (let j = i + 1; j < bucketRows.length; j += 1) {
        const rel = inferPatternRelation(bucketRows[i], bucketRows[j])
        if (!rel) continue
        addEdge(`pat:${bucketRows[i].canonical_key}`, `pat:${bucketRows[j].canonical_key}`, rel)
      }
    }
  }

  // Cross-category contrast between visible patterns
  const visiblePatterns = nodes.filter((n) => n.type === 'grammar')
  for (let i = 0; i < visiblePatterns.length; i += 1) {
    for (let j = i + 1; j < visiblePatterns.length; j += 1) {
      const a = visiblePatterns[i]
      const b = visiblePatterns[j]
      if (a.parentCategoryId === b.parentCategoryId) continue
      if (inferPatternRelation(a._row, b._row) === RELATION.CONTRAST_WITH) {
        addEdge(a.id, b.id, RELATION.CONTRAST_WITH)
      }
    }
  }

  // --- Expanded pattern → examples ---
  for (const patternKey of expandedPatterns) {
    const patternId = `pat:${patternKey}`
    if (!nodeIds.has(patternId)) continue
    const examples = examplesByPattern.get(patternKey) || []
    const limited = examples.slice(0, maxExamplesPerPattern)
    limited.forEach((ex, idx) => {
      const exId = `ex:${patternKey}:${ex.example_id ?? idx}`
      const sentence = ex.sentence || ex.original_sentence || ''
      const short =
        sentence.length > 28 ? `${sentence.slice(0, 26)}…` : sentence || `Example ${idx + 1}`
      addNode({
        id: exId,
        type: 'example',
        label: short,
        fullSentence: sentence,
        article_title: ex.article_title || null,
        parentPatternId: patternId,
        canonical_key: patternKey,
        example: ex,
      })
      addEdge(exId, patternId, RELATION.BELONGS_TO)
    })
  }

  return {
    nodes,
    edges,
    categoryCount: categoryIds.length,
    groups,
  }
}

export function neighborsOf(nodeId, edges = []) {
  const set = new Set()
  for (const e of edges) {
    if (e.source === nodeId) set.add(e.target)
    if (e.target === nodeId) set.add(e.source)
  }
  return set
}

/**
 * Deterministic hierarchical layout: categories on a ring;
 * patterns orbit their category; examples orbit their pattern.
 */
export function layoutHierarchical(nodes, { width = 960, height = 480 } = {}) {
  const cx = width / 2
  const cy = height / 2
  const positioned = new Map()

  const categories = nodes.filter((n) => n.type === 'category')
  const catR = Math.min(width, height) * 0.28
  categories.forEach((n, i) => {
    const angle = (i / Math.max(categories.length, 1)) * Math.PI * 2 - Math.PI / 2
    positioned.set(n.id, {
      ...n,
      x: cx + Math.cos(angle) * catR,
      y: cy + Math.sin(angle) * catR,
      vx: 0,
      vy: 0,
    })
  })

  const patterns = nodes.filter((n) => n.type === 'grammar')
  const byParent = new Map()
  for (const p of patterns) {
    const pid = p.parentCategoryId
    if (!byParent.has(pid)) byParent.set(pid, [])
    byParent.get(pid).push(p)
  }
  for (const [parentId, children] of byParent) {
    const parent = positioned.get(parentId)
    if (!parent) continue
    const r = 78 + Math.min(40, children.length * 4)
    children.forEach((child, i) => {
      const angle = (i / Math.max(children.length, 1)) * Math.PI * 2
      positioned.set(child.id, {
        ...child,
        x: parent.x + Math.cos(angle) * r,
        y: parent.y + Math.sin(angle) * r,
        vx: 0,
        vy: 0,
      })
    })
  }

  const examples = nodes.filter((n) => n.type === 'example')
  const byPattern = new Map()
  for (const ex of examples) {
    const pid = ex.parentPatternId
    if (!byPattern.has(pid)) byPattern.set(pid, [])
    byPattern.get(pid).push(ex)
  }
  for (const [parentId, children] of byPattern) {
    const parent = positioned.get(parentId)
    if (!parent) continue
    const r = 48
    children.forEach((child, i) => {
      const angle = (i / Math.max(children.length, 1)) * Math.PI * 2 - Math.PI / 2
      positioned.set(child.id, {
        ...child,
        x: parent.x + Math.cos(angle) * r,
        y: parent.y + Math.sin(angle) * r,
        vx: 0,
        vy: 0,
      })
    })
  }

  // Any leftover nodes
  for (const n of nodes) {
    if (!positioned.has(n.id)) {
      positioned.set(n.id, { ...n, x: cx, y: cy, vx: 0, vy: 0 })
    }
  }

  return Array.from(positioned.values())
}
