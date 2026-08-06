function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export default function GrammarCanonicalKeyTable({
  rows = [],
  selectedKey,
  selectedUngrouped,
  onSelect,
  loading,
}) {
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center px-4 text-sm text-zinc-500">
        Loading canonical keys…
      </div>
    )
  }

  if (!rows.length) {
    return (
      <div className="flex h-full items-center justify-center px-4 text-sm text-zinc-500">
        No matching grammar keys.
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto">
      <table className="min-w-full border-collapse text-left text-sm">
        <thead className="sticky top-0 z-10 bg-zinc-50/95 backdrop-blur">
          <tr className="border-b border-zinc-200 text-[11px] font-medium uppercase tracking-wide text-zinc-500">
            <th className="px-3 py-2.5">Canonical Key</th>
            <th className="px-3 py-2.5">Name</th>
            <th className="px-3 py-2.5">Level</th>
            <th className="px-3 py-2.5 text-right">Examples</th>
            <th className="px-3 py-2.5">Created</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const isSelected = row.is_ungrouped
              ? selectedUngrouped
              : selectedKey === row.canonical_key && !selectedUngrouped
            return (
              <tr
                key={row.is_ungrouped ? '__ungrouped__' : row.canonical_key}
                onClick={() => onSelect?.(row)}
                className={`cursor-pointer border-b border-zinc-100 transition-colors ${
                  isSelected ? 'bg-zinc-900 text-white' : 'hover:bg-zinc-50 text-zinc-800'
                }`}
              >
                <td className="px-3 py-2.5 align-top">
                  <div className={`font-mono text-xs ${isSelected ? 'text-zinc-100' : 'text-zinc-700'}`}>
                    {row.is_ungrouped ? (
                      <span className={isSelected ? 'text-amber-200' : 'text-amber-700'}>
                        (ungrouped)
                      </span>
                    ) : (
                      row.canonical_key
                    )}
                  </div>
                </td>
                <td className="px-3 py-2.5 align-top">
                  <div className="font-medium leading-snug">{row.title || row.rule_name || '—'}</div>
                  {row.description_preview ? (
                    <div
                      className={`mt-0.5 line-clamp-2 text-xs leading-relaxed ${
                        isSelected ? 'text-zinc-300' : 'text-zinc-500'
                      }`}
                    >
                      {row.description_preview}
                    </div>
                  ) : null}
                </td>
                <td className="px-3 py-2.5 align-top">
                  {(row.derived_levels || []).length ? (
                    <div className="flex flex-wrap gap-1">
                      {row.derived_levels.map((lv) => (
                        <span
                          key={lv}
                          className={`rounded px-1.5 py-0.5 text-[11px] ${
                            isSelected
                              ? 'bg-zinc-700 text-zinc-100'
                              : 'bg-zinc-100 text-zinc-600'
                          }`}
                        >
                          {lv}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className={isSelected ? 'text-zinc-400' : 'text-zinc-400'}>—</span>
                  )}
                </td>
                <td className="px-3 py-2.5 align-top text-right tabular-nums">
                  {row.example_count ?? 0}
                </td>
                <td
                  className={`px-3 py-2.5 align-top whitespace-nowrap text-xs ${
                    isSelected ? 'text-zinc-300' : 'text-zinc-500'
                  }`}
                >
                  {formatDate(row.created_at)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
