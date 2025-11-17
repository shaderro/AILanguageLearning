import { useMemo, useState, useEffect } from 'react'

const ReviewCard = ({
  type = 'vocab', // 'vocab' | 'grammar'
  item,            // 当前复习对象：词汇或语法
  index = 0,       // 当前题目索引（从0）
  total = 1,       // 总题目数
  onAnswer,        // function(choice: 'know' | 'fuzzy' | 'unknown')
  onNext,          // 回答后自动进入下一题
  onComplete,      // 复习完成回调
  onBack,          // 返回卡片预览页面
  onPrevCard,      // 手动上一题
  onNextCard,      // 手动下一题
  showDefinition = true,
}) => {
  const [showExplanation, setShowExplanation] = useState(false)

  // 每换一张卡片（index 或 item 变化）时，重置解释为折叠状态
  useEffect(() => {
    setShowExplanation(false)
  }, [index, item])

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

  const title = useMemo(() => {
    if (type === 'vocab') return item?.vocab_body || 'Unknown Word'
    return item?.rule_name || item?.rule || 'Unknown Rule'
  }, [type, item])

  const shouldShowExplanation = showDefinition && showExplanation

  const content = useMemo(() => {
    if (type === 'vocab') {
      return (
        <div className="space-y-4">
          {shouldShowExplanation && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Definition</h3>
              <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {parseExplanation(item?.explanation || '暂无定义')}
              </div>
            </div>
          )}
          {Array.isArray(item?.examples) && item.examples.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Example</h3>
              <div className="text-gray-600 italic leading-relaxed whitespace-pre-wrap">
                {parseExplanation(item.examples[0]?.context_explanation || 'Example')}
              </div>
            </div>
          )}
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {shouldShowExplanation && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">规则解释</h3>
            <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
              {parseExplanation(item?.rule_summary || item?.explanation || '暂无解释')}
            </div>
          </div>
        )}
        {Array.isArray(item?.examples) && item.examples.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">使用例子</h3>
            <div className="text-gray-600 italic leading-relaxed whitespace-pre-wrap">
              {parseExplanation(item.examples[0]?.explanation_context || 'Example')}
            </div>
          </div>
        )}
      </div>
    )
  }, [type, item, shouldShowExplanation])

  const handleClick = (choice) => {
    // 先记录答案
    onAnswer?.(choice)
    
    // 延迟一下再进入下一题，让用户看到反馈
    setTimeout(() => {
      if (index + 1 < total) {
        onNext?.()
      } else {
        onComplete?.()
      }
    }, 300)
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      {/* Header with progress */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* 上一题箭头 */}
          {onPrevCard && (
            <button
              type="button"
              onClick={onPrevCard}
              disabled={index <= 0}
              className={`px-2 py-1 rounded-lg border text-sm transition-colors ${
                index <= 0
                  ? 'border-gray-200 text-gray-300 cursor-not-allowed'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-100'
              }`}
              title="上一题"
            >
              ←
            </button>
          )}
          {/* 返回按钮 */}
          {onBack && (
            <button
              onClick={onBack}
              className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              title="返回"
            >
              返回列表
            </button>
          )}
          <div className="flex flex-col gap-1">
            <h2 className="text-xl font-bold text-gray-900">{title}</h2>
            {!showExplanation && (
              <button
                type="button"
                onClick={() => setShowExplanation(true)}
                className="self-start text-xs px-2 py-1 border border-blue-300 text-blue-600 rounded hover:bg-blue-50 transition-colors"
              >
                see explanation
              </button>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{index + 1} / {total}</span>
          {/* 下一题箭头 */}
          {onNextCard && (
            <button
              type="button"
              onClick={onNextCard}
              disabled={index >= total - 1}
              className={`px-2 py-1 rounded-lg border text-sm transition-colors ${
                index >= total - 1
                  ? 'border-gray-200 text-gray-300 cursor-not-allowed'
                  : 'border-gray-300 text-gray-600 hover:bg-gray-100'
              }`}
              title="下一题"
            >
              →
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="mb-6">
        {content}
      </div>

      {/* Answer Buttons */}
      <div className="grid grid-cols-3 gap-3">
        <button
          onClick={() => handleClick('unknown')}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          不认识
        </button>
        <button
          onClick={() => handleClick('fuzzy')}
          className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors"
        >
          模糊
        </button>
        <button
          onClick={() => handleClick('know')}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          认识
        </button>
      </div>
    </div>
  )
}

export default ReviewCard 