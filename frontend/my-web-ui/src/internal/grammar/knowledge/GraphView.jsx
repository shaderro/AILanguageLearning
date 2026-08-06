import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { apiService } from '../../../services/api'
import {
  buildHierarchicalGraph,
  layoutHierarchical,
  neighborsOf,
} from './buildHierarchicalGraph'
import { resolveHierarchyBucket } from './grammarHierarchy'
import { RELATION_META } from './relationSemantics'

const WIDTH = 960
const HEIGHT = 480

const NODE_STYLE = {
  category: {
    r: 28,
    fill: '#18181b',
    fillExpanded: '#27272a',
    text: '#fafafa',
    labelSize: 11,
  },
  grammar: {
    r: 14,
    fill: '#52525b',
    fillExpanded: '#3f3f46',
    text: '#27272a',
    labelSize: 10,
  },
  example: {
    r: 8,
    fill: '#a1a1aa',
    fillExpanded: '#71717a',
    text: '#52525b',
    labelSize: 9,
  },
}

function truncate(text, n) {
  const s = String(text || '')
  return s.length > n ? `${s.slice(0, n - 1)}…` : s
}

export default function GraphView({ rows = [], selectedId = null, onSelectRow }) {
  const [expandedCategories, setExpandedCategories] = useState(() => new Set())
  const [expandedPatterns, setExpandedPatterns] = useState(() => new Set())
  const [examplesByPattern, setExamplesByPattern] = useState(() => new Map())
  const [loadingPattern, setLoadingPattern] = useState(null)
  const [hoverId, setHoverId] = useState(null)
  const [focusId, setFocusId] = useState(null)
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 })
  const dragRef = useRef(null)
  const panRef = useRef(null)
  const svgRef = useRef(null)

  const { nodes: graphNodes, edges } = useMemo(
    () =>
      buildHierarchicalGraph({
        rows,
        expandedCategories,
        expandedPatterns,
        examplesByPattern,
        maxExamplesPerPattern: 5,
      }),
    [rows, expandedCategories, expandedPatterns, examplesByPattern]
  )

  const [simNodes, setSimNodes] = useState([])

  useEffect(() => {
    setSimNodes(layoutHierarchical(graphNodes, { width: WIDTH, height: HEIGHT }))
  }, [graphNodes])

  // Soft separation so siblings don't stack exactly
  useEffect(() => {
    if (simNodes.length < 2) return undefined
    let frame = 0
    let raf
    const tick = () => {
      frame += 1
      setSimNodes((prev) => {
        const next = prev.map((n) => ({ ...n }))
        for (let i = 0; i < next.length; i += 1) {
          for (let j = i + 1; j < next.length; j += 1) {
            let dx = next[i].x - next[j].x
            let dy = next[i].y - next[j].y
            let dist = Math.sqrt(dx * dx + dy * dy) || 0.01
            const minDist =
              (NODE_STYLE[next[i].type]?.r || 10) + (NODE_STYLE[next[j].type]?.r || 10) + 8
            if (dist < minDist) {
              const push = ((minDist - dist) / dist) * 0.35
              // Don't shove category nodes much
              const wi = next[i].type === 'category' ? 0.15 : 1
              const wj = next[j].type === 'category' ? 0.15 : 1
              next[i].x += dx * push * wi
              next[i].y += dy * push * wi
              next[j].x -= dx * push * wj
              next[j].y -= dy * push * wj
            }
          }
        }
        return next
      })
      if (frame < 40) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [graphNodes])

  const activeId = focusId || (selectedId ? `pat:${selectedId}` : null)
  const neighborSet = useMemo(
    () => (activeId ? neighborsOf(activeId, edges) : new Set()),
    [activeId, edges]
  )

  const hoverNode = simNodes.find((n) => n.id === hoverId)

  const resetView = () => {
    setExpandedCategories(new Set())
    setExpandedPatterns(new Set())
    setFocusId(null)
    setTransform({ x: 0, y: 0, k: 1 })
  }

  const loadExamples = useCallback(async (canonicalKey) => {
    if (!canonicalKey || examplesByPattern.has(canonicalKey)) return
    setLoadingPattern(canonicalKey)
    try {
      const res = await apiService.getInternalGrammarKeyDetail({ canonicalKey })
      const examples = Array.isArray(res?.data?.examples) ? res.data.examples : []
      setExamplesByPattern((prev) => {
        const next = new Map(prev)
        next.set(canonicalKey, examples)
        return next
      })
    } catch {
      setExamplesByPattern((prev) => {
        const next = new Map(prev)
        next.set(canonicalKey, [])
        return next
      })
    } finally {
      setLoadingPattern(null)
    }
  }, [examplesByPattern])

  const toggleCategory = (bucketId) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev)
      if (next.has(bucketId)) {
        next.delete(bucketId)
        setExpandedPatterns((pats) => {
          const np = new Set(pats)
          for (const row of rows) {
            if (!row?.canonical_key || row.is_ungrouped) continue
            if (resolveHierarchyBucket(row) === bucketId) {
              np.delete(row.canonical_key)
            }
          }
          return np
        })
      } else {
        next.add(bucketId)
      }
      return next
    })
    setFocusId(`cat:${bucketId}`)
  }

  const togglePattern = async (row) => {
    if (!row?.canonical_key) return
    onSelectRow?.(row)
    setFocusId(`pat:${row.canonical_key}`)
    const key = row.canonical_key
    setExpandedPatterns((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
    if (!expandedPatterns.has(key)) {
      await loadExamples(key)
    }
  }

  const onWheel = (e) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setTransform((t) => ({
      ...t,
      k: Math.max(0.4, Math.min(2.8, t.k * delta)),
    }))
  }

  const onBackgroundPointerDown = (e) => {
    if (e.target !== svgRef.current && e.target?.dataset?.role !== 'bg') return
    panRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      ox: transform.x,
      oy: transform.y,
    }
  }

  useEffect(() => {
    const onMove = (e) => {
      if (dragRef.current) {
        const { id, ox, oy, sx, sy } = dragRef.current
        const dx = (e.clientX - sx) / transform.k
        const dy = (e.clientY - sy) / transform.k
        setSimNodes((prev) =>
          prev.map((n) => (n.id === id ? { ...n, x: ox + dx, y: oy + dy } : n))
        )
        return
      }
      if (panRef.current) {
        const { startX, startY, ox, oy } = panRef.current
        setTransform((t) => ({
          ...t,
          x: ox + (e.clientX - startX),
          y: oy + (e.clientY - startY),
        }))
      }
    }
    const onUp = () => {
      dragRef.current = null
      panRef.current = null
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  }, [transform.k])

  const categoryOnly = expandedCategories.size === 0

  if (!graphNodes.some((n) => n.type === 'category')) {
    return (
      <div className="flex h-[420px] items-center justify-center text-sm text-zinc-500">
        No categorized canonical keys to explore. Keys without{' '}
        <code className="mx-1 font-mono text-xs">canonical_key</code> stay in Tree → Ungrouped.
      </div>
    )
  }

  return (
    <div className="relative overflow-hidden rounded-lg border border-zinc-200 bg-zinc-50">
      <div className="absolute left-3 top-3 z-10 flex max-w-[70%] flex-wrap items-center gap-2">
        <div className="rounded bg-white/95 px-2 py-1 text-[11px] text-zinc-500 shadow-sm">
          {categoryOnly
            ? 'Cluster view · click a category to expand patterns'
            : `${graphNodes.filter((n) => n.type === 'category').length} categories · ${
                graphNodes.filter((n) => n.type === 'grammar').length
              } patterns · ${graphNodes.filter((n) => n.type === 'example').length} examples`}
          {loadingPattern ? ' · loading examples…' : ''}
        </div>
        <button
          type="button"
          onClick={resetView}
          className="rounded border border-zinc-200 bg-white px-2 py-1 text-[11px] font-medium text-zinc-700 shadow-sm hover:bg-zinc-50"
        >
          Reset to clusters
        </button>
      </div>

      <div className="absolute right-3 top-3 z-10 rounded bg-white/95 px-2 py-1.5 text-[10px] text-zinc-500 shadow-sm">
        <div className="mb-1 font-medium uppercase tracking-wide text-zinc-400">Relations</div>
        {Object.entries(RELATION_META).map(([key, meta]) => (
          <div key={key} className="flex items-center gap-2 py-0.5">
            <svg width="28" height="8" aria-hidden>
              <line
                x1="0"
                y1="4"
                x2="28"
                y2="4"
                stroke={meta.stroke}
                strokeWidth={meta.width}
                strokeDasharray={meta.dash || undefined}
              />
            </svg>
            <span>{meta.label}</span>
          </div>
        ))}
        <div className="mt-1.5 border-t border-zinc-100 pt-1.5 text-zinc-400">
          ○ category · ● pattern · ◦ example
        </div>
      </div>

      <svg
        ref={svgRef}
        width="100%"
        height={HEIGHT}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="block cursor-grab active:cursor-grabbing touch-none"
        onWheel={onWheel}
        onPointerDown={onBackgroundPointerDown}
      >
        <rect data-role="bg" x="0" y="0" width={WIDTH} height={HEIGHT} fill="transparent" />
        <g transform={`translate(${transform.x} ${transform.y}) scale(${transform.k})`}>
          {edges.map((e) => {
            const a = simNodes.find((n) => n.id === e.source)
            const b = simNodes.find((n) => n.id === e.target)
            if (!a || !b) return null
            const meta = RELATION_META[e.relation] || RELATION_META.related_to
            const involved =
              !activeId ||
              e.source === activeId ||
              e.target === activeId ||
              neighborSet.has(e.source) ||
              neighborSet.has(e.target)
            return (
              <g key={e.id} opacity={involved ? 0.95 : 0.18}>
                <line
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  stroke={meta.stroke}
                  strokeWidth={meta.width}
                  strokeDasharray={meta.dash || undefined}
                />
              </g>
            )
          })}

          {simNodes.map((n) => {
            const style = NODE_STYLE[n.type] || NODE_STYLE.grammar
            const isFocused = activeId === n.id
            const isNeighbor = neighborSet.has(n.id)
            const dimmed = activeId && !isFocused && !isNeighbor
            const filled = n.expanded ? style.fillExpanded : style.fill
            const r = style.r

            return (
              <g
                key={n.id}
                transform={`translate(${n.x} ${n.y})`}
                className="cursor-pointer"
                opacity={dimmed ? 0.22 : 1}
                onPointerDown={(e) => {
                  e.stopPropagation()
                  dragRef.current = {
                    id: n.id,
                    ox: n.x,
                    oy: n.y,
                    sx: e.clientX,
                    sy: e.clientY,
                  }
                }}
                onClick={(e) => {
                  e.stopPropagation()
                  if (n.type === 'category') {
                    toggleCategory(n.bucketId)
                  } else if (n.type === 'grammar') {
                    togglePattern(n._row)
                  } else if (n.type === 'example') {
                    const parent = rows.find((r) => r.canonical_key === n.canonical_key)
                    if (parent) onSelectRow?.(parent)
                    setFocusId(n.id)
                  }
                }}
                onMouseEnter={() => setHoverId(n.id)}
                onMouseLeave={() => setHoverId((cur) => (cur === n.id ? null : cur))}
              >
                {n.type === 'category' ? (
                  <rect
                    x={-r}
                    y={-r * 0.72}
                    width={r * 2}
                    height={r * 1.44}
                    rx={10}
                    fill={filled}
                    stroke={isFocused ? '#fafafa' : '#fff'}
                    strokeWidth={isFocused ? 2 : 1}
                  />
                ) : n.type === 'example' ? (
                  <polygon
                    points={`0,${-r} ${r},0 0,${r} ${-r},0`}
                    fill={filled}
                    stroke={isFocused ? '#18181b' : '#fff'}
                    strokeWidth={isFocused ? 1.5 : 1}
                  />
                ) : (
                  <circle
                    r={r}
                    fill={filled}
                    stroke={isFocused ? '#fafafa' : '#fff'}
                    strokeWidth={isFocused ? 2 : 1}
                  />
                )}

                <text
                  y={n.type === 'category' ? 4 : r + 12}
                  textAnchor="middle"
                  className="select-none"
                  fill={n.type === 'category' ? style.text : dimmed ? '#d4d4d8' : style.text}
                  fontSize={style.labelSize}
                  fontWeight={n.type === 'category' ? 600 : 400}
                >
                  {truncate(
                    n.type === 'category'
                      ? `${n.label}${n.expanded ? ' −' : ' +'}`
                      : n.label,
                    n.type === 'example' ? 16 : 18
                  )}
                </text>
                {n.type === 'category' && !n.expanded ? (
                  <text
                    y={r * 0.55}
                    textAnchor="middle"
                    fill="#a1a1aa"
                    fontSize="9"
                    className="select-none"
                  >
                    {n.patternCount} patterns
                  </text>
                ) : null}
              </g>
            )
          })}
        </g>
      </svg>

      {hoverNode ? (
        <div className="pointer-events-none absolute bottom-3 left-3 max-w-md rounded-md border border-zinc-200 bg-white px-3 py-2 text-xs shadow-sm">
          <div className="text-[10px] font-medium uppercase tracking-wide text-zinc-400">
            {hoverNode.type === 'category'
              ? 'Category cluster'
              : hoverNode.type === 'grammar'
                ? 'Grammar pattern'
                : 'Example'}
          </div>
          <div className="mt-0.5 font-medium text-zinc-900">
            {hoverNode.type === 'example' ? hoverNode.fullSentence || hoverNode.label : hoverNode.label}
          </div>
          {hoverNode.canonical_key ? (
            <div className="mt-0.5 font-mono text-[11px] text-zinc-500">{hoverNode.canonical_key}</div>
          ) : null}
          {hoverNode.type === 'category' ? (
            <div className="mt-1 text-zinc-600">
              {hoverNode.patternCount} patterns · {hoverNode.example_count} examples · click to{' '}
              {hoverNode.expanded ? 'collapse' : 'expand'}
            </div>
          ) : null}
          {hoverNode.type === 'grammar' ? (
            <div className="mt-1 text-zinc-600">
              {[hoverNode.category, hoverNode.subtype, hoverNode.function].filter(Boolean).join(' · ') ||
                'No metadata'}
              {' · '}
              {hoverNode.example_count} examples · click to{' '}
              {hoverNode.expanded ? 'hide' : 'load'} sentences
            </div>
          ) : null}
          {hoverNode.type === 'example' && hoverNode.article_title ? (
            <div className="mt-1 text-zinc-500">Source: {hoverNode.article_title}</div>
          ) : null}
        </div>
      ) : (
        <div className="pointer-events-none absolute bottom-3 left-3 text-[11px] text-zinc-400">
          Progressive explore: Category → Pattern → Example · scroll zoom · drag to pan
        </div>
      )}
    </div>
  )
}
