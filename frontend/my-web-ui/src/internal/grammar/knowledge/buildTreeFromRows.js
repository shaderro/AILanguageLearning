import {
  labelForBucket,
  resolveHierarchyBucket,
} from './grammarHierarchy'

/**
 * Build a temporary tree from dashboard rows + frontend hierarchy mapping.
 *
 * Grammar
 * └── <Category bucket label>
 *     └── <grammar title node>
 */
export function buildTreeFromRows(rows = []) {
  const items = (rows || []).filter((r) => r && !r.is_ungrouped && r.canonical_key)
  const buckets = new Map()

  for (const row of items) {
    const bucketId = resolveHierarchyBucket(row)
    if (!buckets.has(bucketId)) buckets.set(bucketId, [])
    buckets.get(bucketId).push(row)
  }

  const children = Array.from(buckets.entries())
    .sort((a, b) => labelForBucket(a[0]).localeCompare(labelForBucket(b[0])))
    .map(([bucketId, bucketRows]) => ({
      id: `bucket:${bucketId}`,
      type: 'category',
      label: labelForBucket(bucketId),
      children: bucketRows
        .slice()
        .sort((a, b) =>
          String(a.title || a.canonical_key).localeCompare(String(b.title || b.canonical_key))
        )
        .map((row) => ({
          id: row.canonical_key,
          type: 'grammar',
          label: row.title || row.display_name || row.rule_name || row.canonical_key,
          meta: {
            canonical_key: row.canonical_key,
            example_count: row.example_count ?? 0,
            category: row.canonical_category,
          },
          row,
          children: [],
        })),
    }))

  const ungrouped = (rows || []).filter((r) => r?.is_ungrouped)
  if (ungrouped.length) {
    children.push({
      id: 'bucket:ungrouped',
      type: 'category',
      label: 'Ungrouped (no canonical_key)',
      children: ungrouped.map((row, idx) => ({
        id: `__ungrouped__:${idx}`,
        type: 'grammar',
        label: row.title || 'Ungrouped',
        meta: { canonical_key: null, example_count: row.example_count ?? 0 },
        row,
        children: [],
      })),
    })
  }

  return {
    id: 'root:grammar',
    type: 'root',
    label: 'Grammar',
    children,
  }
}
