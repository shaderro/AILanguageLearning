const LearnDetailPage = ({
  type = 'vocab', // 'vocab' | 'grammar'
  data,
  loading = false,
  error = null,
  onBack,
  customHeader = null,
  customContent = null
}) => {
  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-500 mb-4">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">加载失败</h3>
        <p className="text-gray-600 mb-4">{String(error)}</p>
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            返回
          </button>
        )}
      </div>
    )
  }

  const header = customHeader ?? (
    <div className="flex items-center justify-between mb-6">
      <h2 className="text-2xl font-bold text-gray-900">
        {type === 'vocab' ? (data?.vocab_body || 'Unknown Word') : (data?.rule_name || data?.rule || 'Unknown Rule')}
      </h2>
      {onBack && (
        <button
          onClick={onBack}
          className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition-colors"
        >
          返回
        </button>
      )}
    </div>
  )

  const content = customContent ?? (
    type === 'vocab' ? (
      <div className="space-y-6">
        <section>
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Definition</h3>
          <p className="text-gray-800 leading-relaxed">{data?.explanation || '暂无定义'}</p>
        </section>

        {Array.isArray(data?.examples) && data.examples.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Examples</h3>
            <ul className="space-y-2 list-disc pl-5 text-gray-700">
              {data.examples.map((ex, i) => (
                <li key={i} className="leading-relaxed">
                  {ex?.context_explanation || 'Example'}
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="text-sm text-gray-500 flex items-center justify-between">
          <span>Source: {data?.source || 'unknown'}</span>
          {data?.is_starred && <span className="text-yellow-500"></span>}
        </section>
      </div>
    ) : (
      <div className="space-y-6">
        <section>
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Structure</h3>
          <p className="text-gray-800 leading-relaxed">{data?.structure || '暂无结构说明'}</p>
        </section>
        <section>
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Usage</h3>
          <p className="text-gray-800 leading-relaxed">{data?.usage || '暂无用法说明'}</p>
        </section>
        {data?.example && (
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Example</h3>
            <p className="text-gray-600 italic leading-relaxed">"{data.example}"</p>
          </section>
        )}
        <section className="text-sm text-gray-500 flex items-center justify-between">
          <span>Source: {data?.source || 'unknown'}</span>
          {data?.is_starred && <span className="text-yellow-500"></span>}
        </section>
      </div>
    )
  )

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      {header}
      {content}
    </div>
  )
}

export default LearnDetailPage
