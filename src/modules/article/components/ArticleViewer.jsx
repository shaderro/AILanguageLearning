import { useState } from 'react'
import { useArticle } from '../../../hooks/useApi'
import VocabExplanation from './VocabExplanation'

export default function ArticleViewer({ articleId, onTokenSelect }) {
  const { data, isLoading, isError, error } = useArticle(articleId)
  const [selectedTokens, setSelectedTokens] = useState(new Set())
  const [vocabPosition, setVocabPosition] = useState({ x: 0, y: 0 })
  const [showVocab, setShowVocab] = useState(false)
  const [currentVocabWord, setCurrentVocabWord] = useState('')
  const [currentVocabDefinition, setCurrentVocabDefinition] = useState('')

  // 重点词汇定义 (示例)
  const vocabDefinitions = {
    'der': '德语定冠词，阳性单数',
    'die': '德语定冠词，阴性单数或复数',
    'das': '德语定冠词，中性单数',
    'und': '德语连词，表示"和"',
    'ist': '德语动词"sein"的第三人称单数形式，表示"是"'
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex-1 min-w-0 flex items-center justify-center bg-white rounded-lg shadow-md h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading article...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (isError) {
    return (
      <div className="flex-1 min-w-0 flex items-center justify-center bg-white rounded-lg shadow-md h-full">
        <div className="text-center text-red-600">
          <div className="text-6xl mb-4"></div>
          <p className="text-lg font-semibold mb-2">Error loading article</p>
          <p className="text-sm">{String(error)}</p>
        </div>
      </div>
    )
  }

  const article = data?.data
  if (!article) {
    return (
      <div className="flex-1 min-w-0 flex items-center justify-center bg-white rounded-lg shadow-md h-full">
        <p className="text-gray-600">No article data available</p>
      </div>
    )
  }

  // Create unique key for each token (using global_token_id or fallback)
  const getTokenKey = (token, sentenceId, tokenIndex) => {
    return token.global_token_id !== undefined 
      ? `global-${token.global_token_id}`
      : `${sentenceId}-${tokenIndex}`
  }

  const handleTokenClick = (token, tokenKey) => {
    // Only allow clicking on selectable tokens
    if (!token.selectable) return

    const newSelectedTokens = new Set(selectedTokens)
    
    if (newSelectedTokens.has(tokenKey)) {
      newSelectedTokens.delete(tokenKey)
    } else {
      newSelectedTokens.add(tokenKey)
    }
    
    setSelectedTokens(newSelectedTokens)
    
    // Call the callback function with token body for compatibility
    if (onTokenSelect) {
      const selectedTokenBodies = new Set()
      // Rebuild the set of selected token bodies
      article.sentences?.forEach(sentence => {
        sentence.tokens?.forEach((t, idx) => {
          const key = getTokenKey(t, sentence.sentence_id, idx)
          if (newSelectedTokens.has(key)) {
            selectedTokenBodies.add(t.token_body)
          }
        })
      })
      onTokenSelect(token.token_body, selectedTokenBodies)
    }
  }

  const handleVocabHover = (event, token) => {
    const rect = event.currentTarget.getBoundingClientRect()
    setVocabPosition({
      x: rect.left + rect.width / 2,
      y: rect.top
    })
    setCurrentVocabWord(token.token_body)
    setCurrentVocabDefinition(vocabDefinitions[token.token_body] || '暂无定义')
    setShowVocab(true)
  }

  const handleVocabLeave = () => {
    setShowVocab(false)
  }

  // Count statistics
  const totalTokens = article.sentences?.reduce((sum, s) => sum + (s.tokens?.length || 0), 0) || 0
  const selectableTokens = article.sentences?.reduce((sum, s) => 
    sum + (s.tokens?.filter(t => t.selectable)?.length || 0), 0) || 0

  return (
    <div className="flex-1 min-w-0 flex flex-col gap-4 bg-white p-6 rounded-lg shadow-md overflow-y-auto h-full">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">
          {article.text_title || `Article ${article.text_id}`}
        </h2>
        <div className="flex gap-4 text-sm text-gray-600">
          <span>Sentences: {article.total_sentences || article.sentences?.length || 0}</span>
          <span>Total Tokens: {totalTokens}</span>
          <span>Selectable: {selectableTokens}</span>
        </div>
      </div>
      
      {/* Article Content */}
      <div className="space-y-4">
        {article.sentences?.map((sentence) => (
          <div key={sentence.sentence_id} className="mb-3">
            <div className="flex flex-wrap gap-1 leading-relaxed">
              {sentence.tokens?.map((token, tokenIndex) => {
                const tokenKey = getTokenKey(token, sentence.sentence_id, tokenIndex)
                const isSelected = selectedTokens.has(tokenKey)
                const isSelectable = token.selectable === true
                
                return (
                  <span
                    key={tokenKey}
                    onClick={isSelectable ? () => handleTokenClick(token, tokenKey) : undefined}
                    onMouseEnter={isSelectable ? (e) => handleVocabHover(e, token) : undefined}
                    onMouseLeave={isSelectable ? handleVocabLeave : undefined}
                    className={`transition-all duration-200 inline-block ${
                      isSelectable 
                        ? 'cursor-pointer hover:bg-yellow-100 px-1 rounded' 
                        : 'cursor-default'
                    } ${
                      isSelected 
                        ? 'bg-blue-200 text-blue-800' 
                        : ''
                    }`}
                    title={isSelectable ? `Click to select: ${token.token_body}` : `${token.token_type}: ${token.token_body}`}
                  >
                    {token.token_type === 'space' ? '\u00A0' : token.token_body}
                  </span>
                )
              })}
            </div>
          </div>
        ))}
      </div>
      
      {/* Statistics */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg border-t border-gray-200">
        <p className="text-sm text-gray-600">
          已选择 <span className="font-semibold text-blue-600">{selectedTokens.size}</span> 个词汇
          <span className="ml-4 text-gray-500">
            (共 {selectableTokens} 个可选择词汇)
          </span>
        </p>
        {selectedTokens.size > 0 && (
          <p className="text-xs text-gray-500 mt-1">
            选中: {Array.from(selectedTokens).map(key => {
              // Find the token body for this key
              for (const sentence of article.sentences || []) {
                for (const [idx, token] of (sentence.tokens || []).entries()) {
                  if (getTokenKey(token, sentence.sentence_id, idx) === key) {
                    return token.token_body
                  }
                }
              }
              return key
            }).join(', ')}
          </p>
        )}
      </div>

      {/* Vocab Explanation */}
      <VocabExplanation
        word={currentVocabWord}
        definition={currentVocabDefinition}
        isVisible={showVocab}
        position={vocabPosition}
      />
    </div>
  )
}
