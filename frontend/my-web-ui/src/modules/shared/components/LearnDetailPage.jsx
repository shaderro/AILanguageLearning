const LearnDetailPage = ({
  type = 'vocab', // 'vocab' | 'grammar'
  data,
  loading = false,
  error = null,
  onBack,
  customHeader = null,
  customContent = null,
  onToggleStar = null, // 新增收藏切换回调
}) => {
  // 解析和格式化解释文本（与 LearnCard 中的逻辑一致）
  const parseExplanation = (text) => {
    if (!text) return ''
    
    let cleanText = text
    
    // 1. 处理字典格式的字符串（如 "{'explanation': '...'}" 或 '{"explanation": "..."}'）
    if (text.includes("'explanation'") || text.includes('"explanation"')) {
      try {
        // 尝试解析 JSON 格式
        const jsonMatch = text.match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          const jsonStr = jsonMatch[0]
          // 先尝试标准 JSON 解析
          try {
            const parsed = JSON.parse(jsonStr)
            cleanText = parsed.explanation || parsed.definition || text
          } catch (e) {
            // 如果不是标准 JSON，尝试处理 Python 字典格式（单引号）
            // 使用更智能的方法：只替换键和字符串分隔符的单引号
            // 先尝试直接提取 explanation 字段的值（支持多行和转义字符）
            const explanationMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)['"]\s*[,}]/s)
            if (explanationMatch) {
              cleanText = explanationMatch[1]
                .replace(/\\n/g, '\n')  // 处理转义的换行符
                .replace(/\\'/g, "'")   // 处理转义的单引号
                .replace(/\\"/g, '"')   // 处理转义的双引号
            } else {
              // 如果正则匹配失败，尝试将单引号替换为双引号（简单处理）
              const normalized = jsonStr.replace(/'/g, '"')
              try {
                const parsed = JSON.parse(normalized)
                cleanText = parsed.explanation || parsed.definition || text
              } catch (e2) {
                // 如果还是失败，使用原始文本
                cleanText = text
              }
            }
          }
        }
      } catch (e) {
        // 解析失败，使用原始文本
      }
    }
    
    // 2. 处理代码块格式（```json ... ```）
    if (cleanText.includes('```json') && cleanText.includes('```')) {
      try {
        const jsonMatch = cleanText.match(/```json\n(.*?)\n```/s)
        if (jsonMatch) {
          const jsonStr = jsonMatch[1]
          const parsed = JSON.parse(jsonStr)
          cleanText = parsed.explanation || parsed.definition || cleanText
        }
      } catch (e) {
        // 解析失败，继续使用 cleanText
      }
    }
    
    // 3. 清理多余的转义字符和格式化
    // 将 \n 转换为实际的换行
    cleanText = cleanText.replace(/\\n/g, '\n')
    // 移除多余的空白行（连续两个以上的换行符）
    cleanText = cleanText.replace(/\n{3,}/g, '\n\n')
    // 去除首尾空白
    cleanText = cleanText.trim()
    
    return cleanText
  }
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
          : (data?.rule_name || 'Unknown Rule')}
      </h2>
      <div className="flex items-center space-x-3">
        {onToggleStar && (
          <button
            onClick={() => onToggleStar(type === 'vocab' ? data.vocab_id : data.rule_id, data.is_starred)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            title={data?.is_starred ? "取消收藏" : "收藏"}
          >
            {data?.is_starred ? (
              <svg className="w-6 h-6 text-yellow-500 fill-current" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ) : (
              <svg className="w-6 h-6 text-gray-400 hover:text-yellow-500 transition-colors" viewBox="0 0 20 20">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            )}
          </button>
        )}
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            返回
          </button>
        )}
      </div>
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
            </div>
          </div>
        </section>

        {/* 完整解释 */}
        {data?.explanation && (
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">完整解释</h3>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {parseExplanation(data.explanation)}
              </div>
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
                  <div className="text-sm text-gray-600 mb-1">
                    <span className="font-medium">original sentence: </span>
                    <span>{example.original_sentence ?? 'null'}</span>
                  </div>
                  {example.original_sentence && example.original_sentence !== 'null' && example.text_id && (
                    <div className="mt-2 mb-2">
                      <button
                        onClick={() => {
                          // 在新标签页打开原文 chat view
                          const url = `${window.location.origin}${window.location.pathname}?page=article&articleId=${example.text_id}${example.sentence_id ? `&sentenceId=${example.sentence_id}` : ''}`
                          window.open(url, '_blank')
                        }}
                        className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors flex items-center space-x-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        <span>转到原文</span>
                      </button>
                    </div>
                  )}
                  <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {parseExplanation(example.context_explanation)}
                  </div>
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
            <h3 className="text-lg font-semibold text-gray-900">{data?.rule_name}</h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">ID: {data?.rule_id}</span>
            </div>
          </div>
        </section>

        {/* 完整解释 */}
        {data?.rule_summary && (
          <section>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">规则解释</h3>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {parseExplanation(data.rule_summary)}
              </div>
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
                  <div className="text-sm text-gray-600 mb-1">
                    <span className="font-medium">original sentence: </span>
                    <span>{example.original_sentence ?? 'null'}</span>
                  </div>
                  {example.original_sentence && example.original_sentence !== 'null' && example.text_id && (
                    <div className="mt-2 mb-2">
                      <button
                        onClick={() => {
                          // 在新标签页打开原文 chat view
                          const url = `${window.location.origin}${window.location.pathname}?page=article&articleId=${example.text_id}${example.sentence_id ? `&sentenceId=${example.sentence_id}` : ''}`
                          window.open(url, '_blank')
                        }}
                        className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors flex items-center space-x-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        <span>转到原文</span>
                      </button>
                    </div>
                  )}
                  <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                    {parseExplanation(example.explanation_context)}
                  </div>
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
