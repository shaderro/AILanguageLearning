import { useEffect, useMemo, useState } from 'react'
import { buildTreeFromRows } from './buildTreeFromRows'

function TreeNode({ node, depth, selectedId, onSelect, expanded, toggle }) {
  const hasChildren = Array.isArray(node.children) && node.children.length > 0
  const isOpen = expanded.has(node.id)
  const isGrammar = node.type === 'grammar'
  const isSelected =
    isGrammar &&
    (selectedId === node.id ||
      (selectedId === '__ungrouped__' && !!node.row?.is_ungrouped))

  return (
    <li>
      <div
        className={`flex items-start gap-1 rounded px-1.5 py-1 text-sm ${
          isSelected ? 'bg-zinc-900 text-white' : 'hover:bg-zinc-100 text-zinc-800'
        }`}
        style={{ paddingLeft: `${depth * 14 + 6}px` }}
      >
        {hasChildren ? (
          <button
            type="button"
            className={`mt-0.5 h-5 w-5 shrink-0 rounded text-xs ${
              isSelected ? 'text-zinc-300' : 'text-zinc-400 hover:text-zinc-700'
            }`}
            onClick={() => toggle(node.id)}
            aria-label={isOpen ? 'Collapse' : 'Expand'}
          >
            {isOpen ? '▾' : '▸'}
          </button>
        ) : (
          <span className="mt-0.5 inline-block h-5 w-5 shrink-0" />
        )}

        <button
          type="button"
          className="min-w-0 flex-1 text-left"
          onClick={() => {
            if (isGrammar) onSelect?.(node.row)
            else if (hasChildren) toggle(node.id)
          }}
        >
          <div className={`leading-snug ${node.type === 'root' ? 'font-semibold' : ''}`}>
            {node.label}
          </div>
          {isGrammar ? (
            <div
              className={`mt-0.5 font-mono text-[11px] ${
                isSelected ? 'text-zinc-300' : 'text-zinc-500'
              }`}
            >
              {node.meta?.canonical_key || '(ungrouped)'}
              {typeof node.meta?.example_count === 'number'
                ? ` · ${node.meta.example_count} ex`
                : ''}
            </div>
          ) : null}
          {node.type === 'category' ? (
            <div className={`text-[11px] ${isSelected ? 'text-zinc-300' : 'text-zinc-400'}`}>
              {node.children.length} key{node.children.length === 1 ? '' : 's'}
            </div>
          ) : null}
        </button>
      </div>

      {hasChildren && isOpen ? (
        <ul>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              expanded={expanded}
              toggle={toggle}
            />
          ))}
        </ul>
      ) : null}
    </li>
  )
}

export default function TreeView({ rows = [], selectedId = null, onSelectRow }) {
  const tree = useMemo(() => buildTreeFromRows(rows), [rows])
  const [expanded, setExpanded] = useState(() => new Set([tree.id]))

  // Ensure root + category buckets stay open when tree data refreshes
  useEffect(() => {
    setExpanded((prev) => {
      const next = new Set(prev)
      next.add(tree.id)
      for (const child of tree.children || []) next.add(child.id)
      return next
    })
  }, [tree])

  const toggle = (id) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  if (!tree.children?.length) {
    return (
      <div className="flex h-[320px] items-center justify-center text-sm text-zinc-500">
        No grammar keys available for the tree.
      </div>
    )
  }

  return (
    <div className="max-h-[480px] overflow-auto rounded-lg border border-zinc-200 bg-white px-2 py-3">
      <ul>
        <TreeNode
          node={tree}
          depth={0}
          selectedId={selectedId}
          onSelect={onSelectRow}
          expanded={expanded}
          toggle={toggle}
        />
      </ul>
      <p className="mt-3 border-t border-zinc-100 px-2 pt-3 text-[11px] leading-relaxed text-zinc-400">
        Hierarchy uses a temporary frontend mapping (`grammarHierarchy.js`) and existing{' '}
        <code className="font-mono">canonical_category</code> / subtype fields. It does not change
        backend taxonomy.
      </p>
    </div>
  )
}
