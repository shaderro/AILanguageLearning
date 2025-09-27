import CardBase from './CardBase'

const LearnCard = ({ 
  data, 
  onClick, 
  type = 'vocab', // 'vocab' or 'grammar'
  loading = false,
  error = null,
  customContent = null,
  onToggleStar = null // 新增收藏切换回调
}) => {
  // 解析 JSON 格式的解释文本
  const parseExplanation = (text) => {
    if (!text) return ''
    
    // 如果是 JSON 格式的字符串，尝试解析
    if (text.includes('```json') && text.includes('```')) {
      try {
        const jsonMatch = text.match(/```json\n(.*?)\n```/s)
        if (jsonMatch) {
          const jsonStr = jsonMatch[1]
          const parsed = JSON.parse(jsonStr)
          return parsed.explanation || parsed.definition || ''
        }
      } catch (e) {
        // 如果解析失败，返回原始文本的第一行
        return text.split('\n')[0].trim()
      }
    }
    
    // 如果不是 JSON 格式，返回第一行
    return text.split('\n')[0].trim()
  }

  // 根据数据类型确定显示内容
  const getCardContent = () => {
    if (customContent) {
      return customContent
    }

    if (type === 'vocab') {
      return (
        <div className="space-y-2">
          {/* 词汇本身 */}
          <div className="text-lg font-semibold text-gray-900">
            {data?.vocab_body || 'Unknown Word'}
          </div>
          
          {/* 解释内容 */}
          {data?.explanation && (
            <div>
              <p className="text-gray-800 leading-relaxed text-sm">
                {parseExplanation(data.explanation)}
              </p>
            </div>
          )}
          
          <div className="flex justify-between items-center text-xs text-gray-500 mt-2">
            <span>Source: {data?.source || 'unknown'}</span>
            {onToggleStar && (
              <button
                onClick={(e) => {
                  e.stopPropagation(); // 阻止触发卡片的 onClick
                  onToggleStar(type === 'vocab' ? data.vocab_id : data.rule_id, data.is_starred);
                }}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
                title={data?.is_starred ? "取消收藏" : "收藏"}
              >
                {data?.is_starred ? (
                  <svg className="w-4 h-4 text-yellow-500 fill-current" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-gray-400 hover:text-yellow-500 transition-colors" viewBox="0 0 20 20">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                  </svg>
                )}
              </button>
            )}
          </div>
        </div>
      )
    }

    if (type === 'grammar') {
      return (
        <div className="space-y-3">
          {/* 语法规则名称 */}
          <div className="text-lg font-semibold text-gray-900">
            {data?.rule_name || 'Unknown Rule'}
          </div>
          
          {/* 解释内容 */}
          {data?.rule_summary && (
            <div>
              <p className="text-gray-800 leading-relaxed text-sm">
                {data.rule_summary}
              </p>
            </div>
          )}
          
          <div className="flex justify-between items-center text-xs text-gray-500">
            <span>Source: {data?.source || 'unknown'}</span>
            {onToggleStar && (
              <button
                onClick={(e) => {
                  e.stopPropagation(); // 阻止触发卡片的 onClick
                  onToggleStar(type === 'vocab' ? data.vocab_id : data.rule_id, data.is_starred);
                }}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
                title={data?.is_starred ? "取消收藏" : "收藏"}
              >
                {data?.is_starred ? (
                  <svg className="w-4 h-4 text-yellow-500 fill-current" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-gray-400 hover:text-yellow-500 transition-colors" viewBox="0 0 20 20">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                  </svg>
                )}
              </button>
            )}
          </div>
        </div>
      )
    }

    return null
  }

  // 获取卡片标题 - 现在标题已经在内容中显示，所以返回空字符串
  const getCardTitle = () => {
    return ''
  }

  return (
    <CardBase
      title={getCardTitle()}
      data={data}
      loading={loading}
      error={error}
      onClick={onClick}
    >
      {getCardContent()}
    </CardBase>
  )
}

export default LearnCard
