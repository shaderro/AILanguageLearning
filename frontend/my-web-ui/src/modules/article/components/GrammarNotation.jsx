import { useState, useEffect, useRef } from 'react'
import { apiService } from '../../../services/api'
import GrammarNotationCard from './GrammarNotationCard'

/**
 * GrammarNotation - 显示语法注释的下划线组件
 * 
 * Props:
 * - isVisible: 是否显示
 * - textId: 文章ID
 * - sentenceId: 句子ID
 * - grammarId: 语法规则ID
 * - markedTokenIds: 标记的token ID列表
 * - onMouseEnter: 鼠标进入的回调
 * - onMouseLeave: 鼠标离开的回调
 */
export default function GrammarNotation({ 
  isVisible = false, 
  textId = null,
  sentenceId = null,
  grammarId = null,
  markedTokenIds = [],
  onMouseEnter = null,
  onMouseLeave = null
}) {
  const [grammarRule, setGrammarRule] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // 卡片相关状态
  const [showCard, setShowCard] = useState(false)
  const [cardPosition, setCardPosition] = useState({ top: 0, left: 0, right: 'auto' })
  const elementRef = useRef(null)

  useEffect(() => {
    if (isVisible && grammarId) {
      setIsLoading(true)
      setError(null)
      
      // 获取语法规则信息
      apiService.getGrammarById(grammarId)
        .then(response => {
          if (response && response.data) {
            setGrammarRule(response.data)
          } else {
            setGrammarRule(null)
          }
          setIsLoading(false)
        })
        .catch(error => {
          console.error('Error fetching grammar rule:', error)
          setError(error.message || 'Failed to load grammar rule')
          setIsLoading(false)
        })
    } else {
      setGrammarRule(null)
      setError(null)
    }
  }, [isVisible, grammarId])

  // 计算卡片位置
  const calculateCardPosition = () => {
    if (!elementRef.current) return { top: 0, left: 0, right: 'auto' }
    
    const rect = elementRef.current.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const cardWidth = 400 // 预估卡片宽度
    const cardHeight = 300 // 预估卡片高度
    
    let top = rect.bottom + 8 // 在元素下方8px
    let left = rect.left
    let right = 'auto'
    
    // 如果卡片会超出右边界，则左对齐
    if (left + cardWidth > viewportWidth) {
      left = 'auto'
      right = viewportWidth - rect.right
    }
    
    // 如果卡片会超出下边界，则显示在上方
    if (top + cardHeight > viewportHeight) {
      top = rect.top - cardHeight - 8
    }
    
    return { top, left, right }
  }

  // 处理鼠标进入
  const handleMouseEnter = (e) => {
    // 检查是否悬停在vocab notation或asked token上
    const target = e.target
    const isVocabNotation = target.closest('.vocab-notation')
    const isAskedToken = target.closest('.asked-token')
    
    // 只有在没有悬停在vocab notation或asked token上时才显示卡片
    if (!isVocabNotation && !isAskedToken) {
      const position = calculateCardPosition()
      setCardPosition(position)
      setShowCard(true)
    }
    
    // 调用外部传入的回调
    if (onMouseEnter) {
      onMouseEnter(e)
    }
  }

  // 处理鼠标离开
  const handleMouseLeave = (e) => {
    // 延迟隐藏卡片，给用户时间移动到卡片上
    setTimeout(() => {
      setShowCard(false)
    }, 100)
    
    // 调用外部传入的回调
    if (onMouseLeave) {
      onMouseLeave(e)
    }
  }

  // 关闭卡片
  const handleCloseCard = () => {
    setShowCard(false)
  }

  if (!isVisible) return null

  return (
    <>
      <div 
        ref={elementRef}
        className="absolute left-0 right-0 h-0.5 bg-gray-400"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        title={grammarRule ? grammarRule.rule_summary : '语法注释'}
        style={{ 
          bottom: '0px', // 与绿色下划线在同一水平线
          zIndex: 1 // 确保在asked token下划线之上
        }}
      >
        {/* 可选的悬停提示 */}
        {grammarRule && (
          <div className="absolute bottom-full left-0 mb-1 opacity-0 hover:opacity-100 transition-opacity duration-200 pointer-events-none">
            <div className="bg-gray-800 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
              {grammarRule.rule_name}: {grammarRule.rule_summary}
            </div>
          </div>
        )}
      </div>

      {/* 语法注释卡片 */}
      <GrammarNotationCard
        isVisible={isVisible && showCard}
        textId={textId}
        sentenceId={sentenceId}
        position={cardPosition}
        onClose={handleCloseCard}
      />
    </>
  )
}
