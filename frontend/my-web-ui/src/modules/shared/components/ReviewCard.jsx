import { useMemo } from 'react'

const ReviewCard = ({
  type = 'vocab', // 'vocab' | 'grammar'
  item,            // 当前复习对象：词汇或语法
  index = 0,       // 当前题目索引（从0）
  total = 1,       // 总题目数
  onAnswer,        // function(choice: 'know' | 'fuzzy' | 'unknown')
  onNext,          // 进入下一题
  onComplete,      // 复习完成回调
  showDefinition = true,
}) => {
  const title = useMemo(() => {
    if (type === 'vocab') return item?.vocab_body || 'Unknown Word'
    return item?.rule_name || item?.rule || 'Unknown Rule'
  }, [type, item])

  const content = useMemo(() => {
    if (type === 'vocab') {
      return (
        <div className="space-y-4">
          {showDefinition && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Definition</h3>
              <p className="text-gray-800 leading-relaxed">{item?.explanation || '暂无定义'}</p>
            </div>
          )}
          {Array.isArray(item?.examples) && item.examples.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Example</h3>
              <p className="text-gray-600 italic leading-relaxed">{item.examples[0]?.context_explanation || 'Example'}</p>
            </div>
          )}
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {showDefinition && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Structure</h3>
            <p className="text-gray-800 leading-relaxed">{item?.structure || '暂无结构说明'}</p>
          </div>
        )}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Usage</h3>
          <p className="text-gray-800 leading-relaxed">{item?.usage || '暂无用法说明'}</p>
        </div>
        {item?.example && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Example</h3>
            <p className="text-gray-600 italic leading-relaxed">"{item.example}"</p>
          </div>
        )}
      </div>
    )
  }, [type, item, showDefinition])

  const handleClick = (choice) => {
    onAnswer?.(choice)
    if (index + 1 < total) {
      onNext?.()
    } else {
      onComplete?.()
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      {/* Header with progress */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">{title}</h2>
        <span className="text-sm text-gray-500">{index + 1} / {total}</span>
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