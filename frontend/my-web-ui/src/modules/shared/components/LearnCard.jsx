import CardBase from './CardBase'

const LearnCard = ({ 
  data, 
  onClick, 
  type = 'vocab', // 'vocab' or 'grammar'
  loading = false,
  error = null,
  customContent = null
}) => {
  // 获取解释的第一行
  const getFirstLine = (text) => {
    if (!text) return ''
    return text.split('\n')[0].trim()
  }

  // 根据数据类型确定显示内容
  const getCardContent = () => {
    if (customContent) {
      return customContent
    }

    if (type === 'vocab') {
      return (
        <div className="space-y-3">
          {/* 词汇本身 */}
          <div className="text-lg font-semibold text-gray-900">
            {data?.vocab_body || 'Unknown Word'}
          </div>
          
          {/* 解释的第一行 */}
          {data?.explanation && (
            <div>
              <p className="text-gray-800 leading-relaxed text-sm">
                {getFirstLine(data.explanation)}
              </p>
            </div>
          )}
          
          {/* 第一个例子的第一行 */}
          {data?.examples && data.examples.length > 0 && data.examples[0]?.context_explanation && (
            <div>
              <p className="text-gray-600 italic leading-relaxed text-sm">
                {getFirstLine(data.examples[0].context_explanation)}
              </p>
            </div>
          )}
          
          <div className="flex justify-between items-center text-xs text-gray-500">
            <span>Source: {data?.source || 'unknown'}</span>
            {data?.is_starred && <span className="text-yellow-500">⭐</span>}
          </div>
        </div>
      )
    }

    if (type === 'grammar') {
      return (
        <div className="space-y-3">
          {/* 语法规则名称 */}
          <div className="text-lg font-semibold text-gray-900">
            {data?.name || 'Unknown Rule'}
          </div>
          
          {/* 解释的第一行 */}
          {data?.explanation && (
            <div>
              <p className="text-gray-800 leading-relaxed text-sm">
                {getFirstLine(data.explanation)}
              </p>
            </div>
          )}
          
          {/* 第一个例子的第一行 */}
          {data?.examples && data.examples.length > 0 && data.examples[0]?.explanation_context && (
            <div>
              <p className="text-gray-600 italic leading-relaxed text-sm">
                {getFirstLine(data.examples[0].explanation_context)}
              </p>
            </div>
          )}
          
          <div className="flex justify-between items-center text-xs text-gray-500">
            <span>Source: {data?.source || 'unknown'}</span>
            {data?.is_starred && <span className="text-yellow-500">⭐</span>}
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
