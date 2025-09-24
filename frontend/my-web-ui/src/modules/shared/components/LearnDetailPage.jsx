const LearnDetailPage = ({
  type = 'vocab', // 'vocab' | 'grammar'
  data,
  loading = false,
  error = null,
  onBack,
  customHeader = null,
  customContent = null,
}) => {
  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    );
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
    );
  }

  const header = customHeader ?? (
    <div className="flex items-center justify-between mb-6">
      <h2 className="text-2xl font-bold text-gray-900">
        {type === 'vocab'
          ? (data?.vocab_body || 'Unknown Word')
          : (data?.name || 'Unknown Rule')}
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
  );

  const content = customContent ?? (
    type === 'vocab' ? (
      <div className="space-y-6">
        {/* 词汇基本信息 */}
        <section className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">{data?.vocab_body}</h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">ID: {data?.vocab_id}</span>
              {data?.is_starred && <span className="text-yellow-500">⭐</span>}
            </div>
          </div>
        </section>

        {/* 完整解释 */}
        {data?.explanation && (
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">完整解释</h3>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-gray-800 leading-relaxed whitespace-pre-line">{data.explanation}</p>
            </div>
          </section>
        )}

        {/* 所有例子 */}
        {Array.isArray(data?.examples) && data.examples.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">使用例子</h3>
            <div className="space-y-4">
              {data.examples.map((example, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-lg border-l-4 border-blue-400">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-600">例子 {index + 1}</span>
                    <div className="text-xs text-gray-500">
                      <span>文章ID: {example.text_id}</span>
                      <span className="mx-2">|</span>
                      <span>句子ID: {example.sentence_id}</span>
                    </div>
                  </div>
                  <p className="text-gray-800 leading-relaxed whitespace-pre-line">
                    {example.context_explanation}
                  </p>
                  {example.token_indices && example.token_indices.length > 0 && (
                    <div className="mt-2 text-xs text-gray-500">
                      相关词汇位置: {example.token_indices.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 元信息 */}
        <section className="text-sm text-gray-500 flex items-center justify-between pt-4 border-t">
          <span>来源: {data?.source || 'unknown'}</span>
          <span>词汇ID: {data?.vocab_id}</span>
        </section>
      </div>
    ) : (
      <div className="space-y-6">
        {/* 语法规则基本信息 */}
        <section className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">{data?.name}</h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">ID: {data?.rule_id}</span>
              {data?.is_starred && <span className="text-yellow-500">⭐</span>}
            </div>
          </div>
        </section>

        {/* 完整解释 */}
        {data?.explanation && (
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">规则解释</h3>
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-gray-800 leading-relaxed whitespace-pre-line">{data.explanation}</p>
            </div>
          </section>
        )}

        {/* 所有例子 */}
        {Array.isArray(data?.examples) && data.examples.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">使用例子</h3>
            <div className="space-y-4">
              {data.examples.map((example, index) => (
                <div key={index} className="bg-gray-50 p-4 rounded-lg border-l-4 border-green-400">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-600">例子 {index + 1}</span>
                    <div className="text-xs text-gray-500">
                      <span>文章ID: {example.text_id}</span>
                      <span className="mx-2">|</span>
                      <span>句子ID: {example.sentence_id}</span>
                    </div>
                  </div>
                  <p className="text-gray-800 leading-relaxed whitespace-pre-line">
                    {example.explanation_context}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 元信息 */}
        <section className="text-sm text-gray-500 flex items-center justify-between pt-4 border-t">
          <span>来源: {data?.source || 'unknown'}</span>
          <span>规则ID: {data?.rule_id}</span>
        </section>
      </div>
    )
  );

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      {header}
      {content}
    </div>
  );
};

export default LearnDetailPage;
