function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function MetaRow({ label, children }) {
  return (
    <div className="grid grid-cols-[110px_1fr] gap-3 border-b border-zinc-100 py-2 text-sm last:border-b-0">
      <div className="text-xs font-medium uppercase tracking-wide text-zinc-400">{label}</div>
      <div className="min-w-0 text-zinc-800">{children}</div>
    </div>
  )
}

export default function GrammarCanonicalDetail({ detail, loading, error }) {
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center px-6 text-sm text-zinc-500">
        Loading detail…
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center px-6 text-sm text-red-600">
        {error}
      </div>
    )
  }

  if (!detail) {
    return (
      <div className="flex h-full items-center justify-center px-6 text-sm text-zinc-500">
        Select a canonical key to inspect examples.
      </div>
    )
  }

  const levels = detail.derived_levels || []
  const examples = detail.examples || []
  const rules = detail.rules || []

  return (
    <div className="h-full overflow-auto px-6 py-5">
      <div className="mb-5">
        <div className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">
          Grammar
        </div>
        <h2 className="mt-1 text-xl font-semibold tracking-tight text-zinc-900">
          {detail.title || detail.display_name || detail.rule_name || '—'}
        </h2>
      </div>

      <div className="mb-6 rounded-lg border border-zinc-200 bg-white">
        <div className="px-4 py-1">
          <MetaRow label="Canonical Key">
            {detail.is_ungrouped ? (
              <span className="font-mono text-xs text-amber-700">(ungrouped)</span>
            ) : (
              <span className="break-all font-mono text-xs text-zinc-700">
                {detail.canonical_key || '—'}
              </span>
            )}
          </MetaRow>
          <MetaRow label="Language">{detail.language || '—'}</MetaRow>
          <MetaRow label="Category">
            {[detail.canonical_category, detail.canonical_subtype, detail.canonical_function]
              .filter(Boolean)
              .join(' · ') || '—'}
          </MetaRow>
          <MetaRow label="Level (derived)">
            {levels.length ? (
              <div className="flex flex-wrap gap-1">
                {levels.map((lv) => (
                  <span
                    key={lv}
                    className="rounded bg-zinc-100 px-1.5 py-0.5 text-xs text-zinc-600"
                  >
                    {lv}
                  </span>
                ))}
              </div>
            ) : (
              '—'
            )}
          </MetaRow>
          <MetaRow label="Rules">{detail.rule_count ?? rules.length}</MetaRow>
          <MetaRow label="Examples">{detail.example_count ?? examples.length}</MetaRow>
          <MetaRow label="Created">{formatDate(detail.created_at)}</MetaRow>
        </div>
      </div>

      <section className="mb-6">
        <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wide text-zinc-400">
          Explanation
        </h3>
        <div className="whitespace-pre-wrap rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm leading-relaxed text-zinc-700">
          {detail.description || detail.explanation || 'No explanation stored.'}
        </div>
      </section>

      {rules.length > 1 ? (
        <section className="mb-6">
          <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wide text-zinc-400">
            Related Rules ({rules.length})
          </h3>
          <ul className="space-y-2">
            {rules.map((rule) => (
              <li
                key={rule.rule_id}
                className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
              >
                <div className="font-medium text-zinc-800">
                  #{rule.rule_id} {rule.display_name || rule.rule_name}
                </div>
                <div className="mt-0.5 text-xs text-zinc-500">
                  {rule.source || '—'} · {rule.learn_status || '—'} · {formatDate(rule.created_at)}
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section>
        <h3 className="mb-2 text-[11px] font-medium uppercase tracking-wide text-zinc-400">
          Examples ({examples.length})
        </h3>
        {!examples.length ? (
          <div className="rounded-lg border border-dashed border-zinc-200 px-4 py-8 text-center text-sm text-zinc-500">
            No examples linked to this key.
          </div>
        ) : (
          <div className="space-y-3">
            {examples.map((ex) => (
              <article
                key={ex.example_id || `${ex.rule_id}-${ex.text_id}-${ex.sentence_id}`}
                className="rounded-lg border border-zinc-200 bg-white px-4 py-3"
              >
                <div className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">
                  Original sentence
                </div>
                <p className="mt-1 text-sm leading-relaxed text-zinc-900">
                  {ex.sentence || ex.original_sentence || '—'}
                </p>

                <div className="mt-3 grid gap-2 text-xs text-zinc-600 sm:grid-cols-2">
                  <div>
                    <span className="text-zinc-400">Source article: </span>
                    {ex.article_title || `text_${ex.text_id ?? '—'}`}
                  </div>
                  <div>
                    <span className="text-zinc-400">Level: </span>
                    {(ex.derived_levels || []).join(', ') ||
                      [ex.article_exam_content, ex.article_difficulty].filter(Boolean).join(', ') ||
                      '—'}
                  </div>
                </div>

                {ex.annotation?.pattern ? (
                  <div className="mt-3 rounded bg-zinc-50 px-3 py-2 text-xs text-zinc-700">
                    <span className="text-zinc-400">Highlighted structure: </span>
                    {ex.annotation.pattern}
                  </div>
                ) : null}

                {ex.explanation_context ? (
                  <div className="mt-3">
                    <div className="text-[11px] font-medium uppercase tracking-wide text-zinc-400">
                      Related extracted knowledge
                    </div>
                    <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap rounded bg-zinc-50 px-3 py-2 font-sans text-xs leading-relaxed text-zinc-600">
                      {ex.explanation_context}
                    </pre>
                  </div>
                ) : null}

                {Array.isArray(ex.marked_token_ids) && ex.marked_token_ids.length ? (
                  <div className="mt-2 font-mono text-[11px] text-zinc-400">
                    marked_token_ids: [{ex.marked_token_ids.join(', ')}]
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
