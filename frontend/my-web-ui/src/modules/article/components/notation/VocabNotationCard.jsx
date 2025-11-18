import { useState, useEffect, useRef, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { apiService } from '../../../../services/api'

const DEFAULT_CARD_WIDTH = 320
const DEFAULT_CARD_MAX_HEIGHT = 320
const CARD_MARGIN = 8

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

/**
 * VocabNotationCard - 显示词汇注释卡片（由原 TokenNotation 重命名）
 * 
 * Props:
 * - isVisible: 是否显示
 * - note: 备用文本
 * - position: 定位信息（可选）
 * - textId, sentenceId, tokenIndex: 定位到具体词汇示例
 * - onMouseEnter, onMouseLeave: 悬停回调
 * - getVocabExampleForToken: 从缓存/后端获取示例
 */
export default function VocabNotationCard({ 
  isVisible = false, 
  note = "This is a test note", 
  position = null,
  textId = null,
  sentenceId = null,
  tokenIndex = null,
  onMouseEnter = null,
  onMouseLeave = null,
  getVocabExampleForToken = null,
  anchorRef = null
}) {
  const [show, setShow] = useState(false)
  const [vocabExample, setVocabExample] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [portalStyle, setPortalStyle] = useState({})
  const portalContainerRef = useRef(null)

  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(() => setShow(true), 150)

      // 🔧 每次显示时都尝试加载，如果已有数据则直接使用
      if (!vocabExample && !isLoading && !error) {
        if (getVocabExampleForToken) {
          setIsLoading(true)
          setError(null)
          getVocabExampleForToken(textId, sentenceId, tokenIndex)
            .then(example => {
              setVocabExample(example || null)
              setIsLoading(false)
            })
            .catch(error => {
              console.error('❌ [VocabNotationCard] Error fetching vocab example:', error)
              setError(error.message || 'Failed to load vocab example')
              setVocabExample(null)
              setIsLoading(false)
            })
        } else if (textId && sentenceId && tokenIndex) {
          setIsLoading(true)
          setError(null)
          apiService.getVocabExampleByLocation(textId, sentenceId, tokenIndex)
            .then(response => {
              if (response && response.vocab_id) {
                setVocabExample(response)
              } else {
                setVocabExample(null)
              }
              setIsLoading(false)
            })
            .catch(error => {
              console.error('❌ [VocabNotationCard] Error fetching vocab example:', error)
              setError(error.message || 'Failed to load vocab example')
              setIsLoading(false)
            })
        }
      }

      return () => clearTimeout(timer)
    } else {
      setShow(false)
      // 不再清空 vocabExample，保留缓存
    }
  }, [isVisible, textId, sentenceId, tokenIndex, getVocabExampleForToken])
  
  // 🔧 添加单独的 effect 来监听 vocabExample 的变化，如果从 null 变为有值，更新状态
  useEffect(() => {
    if (isVisible && vocabExample === null && !isLoading && !error) {
      // 如果example为null，尝试重新加载
      if (getVocabExampleForToken && textId && sentenceId && tokenIndex) {
        const checkInterval = setInterval(() => {
          getVocabExampleForToken(textId, sentenceId, tokenIndex)
            .then(example => {
              if (example && example.context_explanation) {
                setVocabExample(example)
                clearInterval(checkInterval)
              }
            })
            .catch(() => {
              // 忽略错误，继续轮询
            })
        }, 1000) // 每秒检查一次
        
        // 30秒后停止轮询
        const timeout = setTimeout(() => {
          clearInterval(checkInterval)
        }, 30000)
        
        return () => {
          clearInterval(checkInterval)
          clearTimeout(timeout)
        }
      }
    }
  }, [isVisible, vocabExample, isLoading, error, textId, sentenceId, tokenIndex, getVocabExampleForToken])

  useEffect(() => {
    if (typeof window === 'undefined') return
    if (!portalContainerRef.current) {
      let container = document.getElementById('notation-portal-root')
      if (!container) {
        container = document.createElement('div')
        container.id = 'notation-portal-root'
        container.style.position = 'relative'
        container.style.zIndex = '9999'
        document.body.appendChild(container)
      }
      portalContainerRef.current = container
    }
  }, [])

  const updatePosition = useCallback(() => {
    if (!anchorRef?.current || !portalContainerRef.current) return
    const rect = anchorRef.current.getBoundingClientRect()
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight
    const desiredLeft = rect.left
    const maxLeft = viewportWidth - DEFAULT_CARD_WIDTH - CARD_MARGIN
    const left = Math.max(CARD_MARGIN, Math.min(desiredLeft, maxLeft))
    let top = rect.bottom + CARD_MARGIN
    const maxTop = viewportHeight - CARD_MARGIN
    const estimatedHeight = DEFAULT_CARD_MAX_HEIGHT
    if (top + estimatedHeight > maxTop && rect.top > estimatedHeight + CARD_MARGIN) {
      top = rect.top - estimatedHeight - CARD_MARGIN
    }
    setPortalStyle({
      position: 'fixed',
      top: `${Math.max(CARD_MARGIN, top)}px`,
      left: `${left}px`,
      width: `${DEFAULT_CARD_WIDTH}px`,
      opacity: show ? 1 : 0,
      pointerEvents: show ? 'auto' : 'none',
      ...(position || {})
    })
  }, [anchorRef, show, position])

  useEffect(() => {
    if (!show) return
    updatePosition()
    const handleScroll = () => updatePosition()
    window.addEventListener('scroll', handleScroll, true)
    window.addEventListener('resize', handleScroll)
    return () => {
      window.removeEventListener('scroll', handleScroll, true)
      window.removeEventListener('resize', handleScroll)
    }
  }, [show, updatePosition])

  if (!show || !portalContainerRef.current) return null

  let displayContent = note

  if (isLoading) {
    // 🔧 显示"正在生成解释"的灰色文字
    displayContent = (
      <div className="flex items-center gap-2">
        <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-gray-500">正在生成解释...</span>
      </div>
    )
  } else if (error) {
    displayContent = (
      <div className="text-red-600">
        <div className="font-semibold">加载失败</div>
        <div className="text-xs mt-1">{error}</div>
      </div>
    )
  } else if (vocabExample && vocabExample.context_explanation) {
    displayContent = (
      <div>
        <div className="text-xs text-gray-500 mb-1">词汇解释</div>
        <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
          {parseExplanation(vocabExample.context_explanation)}
        </div>
        {vocabExample.vocab_id && (
          <div className="text-xs text-gray-400 mt-2">Vocab ID: {vocabExample.vocab_id}</div>
        )}
      </div>
    )
  } else if (vocabExample === null && !isLoading) {
    // 🔧 如果example为null且不在加载中，显示"正在生成解释"
    displayContent = (
      <div className="text-gray-500 text-sm">正在生成解释...</div>
    )
  }

  return createPortal(
    <div 
      className="transition-opacity duration-200 notation-card"
      style={portalStyle}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="absolute top-1 left-4 w-2 h-2 bg-gray-200 transform rotate-45 border-l border-t border-gray-300"></div>
      <div 
        className="bg-gray-100 border border-gray-300 rounded-lg shadow-lg p-3"
        style={{
          maxHeight: `${DEFAULT_CARD_MAX_HEIGHT}px`,
          overflowY: 'auto'
        }}
      >
        {displayContent}
      </div>
    </div>,
    portalContainerRef.current
  )
}


