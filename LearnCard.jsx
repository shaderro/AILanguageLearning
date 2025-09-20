import CardBase from './CardBase'

const LearnCard = ({ 
  data, 
  onClick, 
  type = 'vocab', // 'vocab' or 'grammar'
  loading = false,
  error = null,
  customContent = null
}) => {
  // 根据数据类型确定显示内容
  const getCardContent = () => {
    if (customContent) {
      return customContent
    }

    if (type === 'vocab') {
      return (
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Definition
            </h3>
            <p className="text-gray-800 leading-relaxed">
              {data?.explanation || '暂无定义'}
            </p>
          </div>
          
          {data?.examples && data.examples.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
                Examples
              </h3>
              <div className="space-y-2">
                {data.examples.slice(0, 2).map((example, index) => (
                  <div key={index} className="text-gray-600 italic leading-relaxed">
                    {example.context_explanation ? (
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Context:</p>
                        <p className="text-sm">{example.context_explanation}</p>
                      </div>
                    ) : (
                      <p className="text-sm">Example {index + 1}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="flex justify-between items-center text-sm text-gray-500">
            <span>Source: {data?.source || 'unknown'}</span>
            {data?.is_starred && <span className="text-yellow-500"></span>}
          </div>
        </div>
      )
    }

    if (type === 'grammar') {
      return (
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Structure
            </h3>
            <p className="text-gray-800 leading-relaxed">
              {data?.structure || '暂无结构说明'}
            </p>
          </div>
          
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Usage
            </h3>
            <p className="text-gray-800 leading-relaxed">
              {data?.usage || '暂无用法说明'}
            </p>
          </div>
          
          {data?.example && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
                Example
              </h3>
              <p className="text-gray-600 italic leading-relaxed">
                "{data.example}"
              </p>
            </div>
          )}
          
          <div className="flex justify-between items-center text-sm text-gray-500">
            <span>Source: {data?.source || 'unknown'}</span>
            {data?.is_starred && <span className="text-yellow-500"></span>}
          </div>
        </div>
      )
    }

    return null
  }

  // 获取卡片标题
  const getCardTitle = () => {
    if (type === 'vocab') {
      return data?.vocab_body || 'Unknown Word'
    }
    if (type === 'grammar') {
      return data?.rule_name || data?.rule || 'Unknown Rule'
    }
    return 'Unknown'
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
