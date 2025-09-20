import CardBase from '../../shared/components/CardBase'

const WordCard = ({ word, onClick }) => {
  // 如果word是字符串，显示简单的单词卡片
  // 如果word是对象，显示完整的词汇信息
  const isWordObject = typeof word === 'object' && word !== null
  
  if (isWordObject) {
    // 处理词汇对象
    const vocab = word
    return (
      <CardBase
        title={vocab.vocab_body}
        data={vocab}
        loading={false}
        error={null}
        onClick={onClick}
      >
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Definition
            </h3>
            <p className="text-gray-800 leading-relaxed">
              {vocab.explanation || '暂无定义'}
            </p>
          </div>
          
          {vocab.examples && vocab.examples.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
                Examples
              </h3>
              <div className="space-y-2">
                {vocab.examples.map((example, index) => (
                  <div key={index} className="text-gray-600 italic leading-relaxed">
                    {example.context_explanation ? (
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Context:</p>
                        <p>{example.context_explanation}</p>
                      </div>
                    ) : (
                      <p>Example {index + 1}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="flex justify-between items-center text-sm text-gray-500">
            <span>Source: {vocab.source}</span>
            {vocab.is_starred && <span className="text-yellow-500"></span>}
          </div>
        </div>
      </CardBase>
    )
  }
  
  // 处理字符串单词（保持原有逻辑）
  return (
    <CardBase
      title={word}
      data={null}
      loading={false}
      error={null}
      onClick={onClick}
    >
      <div className="text-center text-gray-600">
        <p>Click to view details</p>
      </div>
    </CardBase>
  )
}

export default WordCard
