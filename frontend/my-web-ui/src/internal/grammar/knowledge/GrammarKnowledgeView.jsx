import { useState } from 'react'
import GraphView from './GraphView'
import TreeView from './TreeView'

const tabs = [
  { id: 'network', label: 'Network View' },
  { id: 'tree', label: 'Tree View' },
]

export default function GrammarKnowledgeView({
  rows = [],
  selectedRow = null,
  onSelectRow,
}) {
  const [tab, setTab] = useState('network')
  const selectedId = selectedRow?.is_ungrouped
    ? '__ungrouped__'
    : selectedRow?.canonical_key || null

  return (
    <section className="border-t border-zinc-200 bg-white">
      <div className="flex flex-wrap items-end justify-between gap-3 px-5 py-4">
        <div>
          <div className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">
            Experiment · frontend-only
          </div>
          <h2 className="mt-0.5 text-base font-semibold tracking-tight text-zinc-900">
            Grammar Knowledge Structure
          </h2>
          <p className="mt-1 max-w-2xl text-xs text-zinc-500">
            Hierarchical exploration: start from category clusters, expand into grammar patterns,
            then example sentences. Relations (
            <span className="font-mono">belongs_to / similar_to / contrast_with / related_to</span>
            ) are inferred in the browser from existing metadata.
          </p>
        </div>
        <div className="inline-flex rounded-md border border-zinc-200 bg-zinc-50 p-0.5">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                tab === t.id
                  ? 'bg-white text-zinc-900 shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-800'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="px-5 pb-5">
        {tab === 'network' ? (
          <GraphView rows={rows} selectedId={selectedId} onSelectRow={onSelectRow} />
        ) : (
          <TreeView rows={rows} selectedId={selectedId} onSelectRow={onSelectRow} />
        )}
      </div>
    </section>
  )
}
