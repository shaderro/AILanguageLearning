import { useCallback, useEffect, useMemo, useState } from 'react'
import { useUser } from '../../contexts/UserContext'
import { apiService } from '../../services/api'
import GrammarCanonicalKeyTable from './GrammarCanonicalKeyTable'
import GrammarCanonicalDetail from './GrammarCanonicalDetail'
import GrammarKnowledgeView from './knowledge/GrammarKnowledgeView'

const inputClass =
  'w-full rounded-md border border-zinc-200 bg-white px-2.5 py-1.5 text-sm text-zinc-800 outline-none placeholder:text-zinc-400 focus:border-zinc-400'

function selectionId(row) {
  if (!row) return null
  return row.is_ungrouped ? '__ungrouped__' : row.canonical_key
}

export default function GrammarDashboardPage() {
  const { isAuthenticated, isLoading: authLoading } = useUser()

  const [q, setQ] = useState('')
  const [canonicalKeyFilter, setCanonicalKeyFilter] = useState('')
  const [level, setLevel] = useState('')
  const [minExamples, setMinExamples] = useState('')
  const [sort, setSort] = useState('recent')
  const [includeUngrouped, setIncludeUngrouped] = useState(true)

  const [debouncedQ, setDebouncedQ] = useState('')
  const [debouncedKey, setDebouncedKey] = useState('')
  const [debouncedLevel, setDebouncedLevel] = useState('')

  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [listLoading, setListLoading] = useState(false)
  const [listError, setListError] = useState(null)

  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState(null)

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 250)
    return () => clearTimeout(t)
  }, [q])

  useEffect(() => {
    const t = setTimeout(() => setDebouncedKey(canonicalKeyFilter), 250)
    return () => clearTimeout(t)
  }, [canonicalKeyFilter])

  useEffect(() => {
    const t = setTimeout(() => setDebouncedLevel(level), 250)
    return () => clearTimeout(t)
  }, [level])

  const listParams = useMemo(
    () => ({
      q: debouncedQ || undefined,
      canonicalKey: debouncedKey || undefined,
      level: debouncedLevel || undefined,
      minExamples: minExamples === '' ? undefined : Number(minExamples),
      sort,
      includeUngrouped,
      limit: 500,
      skip: 0,
    }),
    [debouncedQ, debouncedKey, debouncedLevel, minExamples, sort, includeUngrouped]
  )

  const loadList = useCallback(async () => {
    if (!isAuthenticated) return
    setListLoading(true)
    setListError(null)
    try {
      const res = await apiService.getInternalGrammarKeys(listParams)
      const data = Array.isArray(res?.data) ? res.data : []
      setRows(data)
      setTotal(typeof res?.total === 'number' ? res.total : data.length)
    } catch (err) {
      const status = err?.response?.status
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Failed to load canonical keys'
      setListError(status === 401 ? 'Unauthorized. Please log in.' : String(msg))
      setRows([])
      setTotal(0)
    } finally {
      setListLoading(false)
    }
  }, [isAuthenticated, listParams])

  useEffect(() => {
    loadList()
  }, [loadList])

  // Keep selection in sync with refreshed list
  useEffect(() => {
    if (!selected) return
    const stillThere = rows.some((row) => selectionId(row) === selectionId(selected))
    if (!stillThere) {
      setSelected(null)
      setDetail(null)
      setDetailError(null)
    }
  }, [rows, selected])

  const loadDetail = useCallback(async (row) => {
    if (!row) {
      setDetail(null)
      setDetailError(null)
      return
    }
    setDetailLoading(true)
    setDetailError(null)
    try {
      const res = await apiService.getInternalGrammarKeyDetail({
        canonicalKey: row.is_ungrouped ? undefined : row.canonical_key,
        ungrouped: !!row.is_ungrouped,
      })
      setDetail(res?.data || null)
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Failed to load detail'
      setDetail(null)
      setDetailError(String(msg))
    } finally {
      setDetailLoading(false)
    }
  }, [])

  const handleSelect = (row) => {
    setSelected(row)
    loadDetail(row)
  }

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 text-sm text-zinc-500">
        Checking session…
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-6">
        <div className="max-w-md rounded-xl border border-zinc-200 bg-white p-8 text-center shadow-sm">
          <div className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">
            Internal
          </div>
          <h1 className="mt-2 text-lg font-semibold text-zinc-900">
            Grammar Canonical Dashboard
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-zinc-600">
            Login is required. Open the main app, sign in, then return to{' '}
            <span className="font-mono text-xs text-zinc-800">/internal/grammar-dashboard</span>.
          </p>
          <a
            href="/"
            className="mt-6 inline-flex rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800"
          >
            Go to main app
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50 text-zinc-900">
      <header className="border-b border-zinc-200 bg-white">
        <div className="flex flex-wrap items-end justify-between gap-3 px-5 py-4">
          <div>
            <div className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">
              Internal · read-only
            </div>
            <h1 className="mt-0.5 text-lg font-semibold tracking-tight">
              Grammar Canonical Keys
            </h1>
            <p className="mt-1 text-xs text-zinc-500">
              Sentence → Grammar Pattern → Canonical Key → Related Examples
            </p>
          </div>
          <div className="text-xs text-zinc-500">
            {listLoading ? 'Refreshing…' : `${total} group${total === 1 ? '' : 's'}`}
          </div>
        </div>

        <div className="grid gap-2 border-t border-zinc-100 px-5 py-3 sm:grid-cols-2 lg:grid-cols-6">
          <label className="block lg:col-span-2">
            <span className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-zinc-400">
              Search
            </span>
            <input
              className={inputClass}
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="key, name, explanation…"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-zinc-400">
              Canonical key
            </span>
            <input
              className={inputClass}
              value={canonicalKeyFilter}
              onChange={(e) => setCanonicalKeyFilter(e.target.value)}
              placeholder="e.g. ba_structure"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-zinc-400">
              Level
            </span>
            <input
              className={inputClass}
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              placeholder="hsk / beginner…"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-zinc-400">
              Min examples
            </span>
            <input
              className={inputClass}
              type="number"
              min={0}
              value={minExamples}
              onChange={(e) => setMinExamples(e.target.value)}
              placeholder="0"
            />
          </label>
          <label className="block">
            <span className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-zinc-400">
              Sort
            </span>
            <select
              className={inputClass}
              value={sort}
              onChange={(e) => setSort(e.target.value)}
            >
              <option value="recent">Recently created</option>
              <option value="examples">Number of examples</option>
              <option value="key">Canonical key</option>
            </select>
          </label>
        </div>

        <div className="flex items-center gap-4 border-t border-zinc-100 px-5 py-2.5">
          <label className="inline-flex items-center gap-2 text-xs text-zinc-600">
            <input
              type="checkbox"
              checked={includeUngrouped}
              onChange={(e) => setIncludeUngrouped(e.target.checked)}
              className="rounded border-zinc-300"
            />
            Include ungrouped (missing canonical_key)
          </label>
          <button
            type="button"
            onClick={loadList}
            className="rounded-md border border-zinc-200 bg-white px-2.5 py-1 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
          >
            Refresh
          </button>
          {listError ? <span className="text-xs text-red-600">{listError}</span> : null}
        </div>
      </header>

      <div className="grid min-h-[55vh] lg:grid-cols-[minmax(0,1.15fr)_minmax(340px,0.85fr)]">
        <div className="min-h-[45vh] border-b border-zinc-200 bg-white lg:min-h-0 lg:border-b-0 lg:border-r">
          <GrammarCanonicalKeyTable
            rows={rows}
            selectedKey={selected?.is_ungrouped ? null : selected?.canonical_key}
            selectedUngrouped={!!selected?.is_ungrouped}
            onSelect={handleSelect}
            loading={listLoading && !rows.length}
          />
        </div>
        <div className="min-h-[45vh] bg-zinc-50/80 lg:min-h-0">
          <GrammarCanonicalDetail
            detail={detail}
            loading={detailLoading}
            error={detailError}
          />
        </div>
      </div>

      <GrammarKnowledgeView
        rows={rows}
        selectedRow={selected}
        onSelectRow={handleSelect}
      />
    </div>
  )
}
