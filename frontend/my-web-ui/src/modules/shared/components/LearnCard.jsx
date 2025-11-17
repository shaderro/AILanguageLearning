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
  // 解析和格式化解释文本
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

  // 格式化学习状态显示文本
  const formatLearnStatus = (learnStatus) => {
    if (!learnStatus) return '未掌握'
    if (learnStatus === 'mastered') return '已掌握'
    if (learnStatus === 'not_mastered') return '未掌握'
    return '未掌握' // 默认值
  }

  // 获取学习状态显示颜色
  const getLearnStatusColor = (learnStatus) => {
    if (!learnStatus) return 'text-gray-500'
    if (learnStatus === 'mastered') return 'text-green-600'
    if (learnStatus === 'not_mastered') return 'text-gray-500'
    return 'text-gray-500'
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
              <div className="text-gray-800 leading-relaxed text-sm whitespace-pre-wrap">
                {parseExplanation(data.explanation)}
              </div>
            </div>
          )}
          
          <div className="flex flex-col space-y-1 mt-2">
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
            {/* 学习状态显示 */}
            <div className="text-xs">
              <span className={getLearnStatusColor(data?.learn_status)}>
                状态: {formatLearnStatus(data?.learn_status)}
              </span>
            </div>
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
              <div className="text-gray-800 leading-relaxed text-sm whitespace-pre-wrap">
                {parseExplanation(data.rule_summary)}
              </div>
            </div>
          )}
          
          <div className="flex flex-col space-y-1">
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
            {/* 学习状态显示 */}
            <div className="text-xs">
              <span className={getLearnStatusColor(data?.learn_status)}>
                状态: {formatLearnStatus(data?.learn_status)}
              </span>
            </div>
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
