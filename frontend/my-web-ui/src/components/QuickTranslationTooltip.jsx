/**
 * QuickTranslationTooltip - 轻量级翻译tooltip组件
 * 显示单词和简短翻译，不包含例句，不调用AI
 */
import { useEffect, useState, useRef } from 'react'

export default function QuickTranslationTooltip({
  word,
  translation,
  translationSource = null, // 'dictionary' | 'translation' | null
  isVisible,
  anchorRef,
  position = 'top', // 'top' | 'bottom' | 'left' | 'right'
  showWord = true, // 是否显示原文/单词，默认显示
  isLoading = false, // 是否正在加载翻译
  onSpeak = null, // 朗读回调函数（可选）
  onMouseEnter = null, // tooltip hover 进入回调
  onMouseLeave = null, // tooltip hover 离开回调
  onAskAI = null, // AI详细解释回调函数（可选，可以接收 (word) 或 (token, sentenceIdx)）
  isTokenInsufficient = false // 🔧 Token是否不足（用于禁用AI详细解释按钮）
}) {
  const [tooltipPosition, setTooltipPosition] = useState({ top: -9999, left: -9999 })
  const [isPositioned, setIsPositioned] = useState(false)
  const tooltipRef = useRef(null)

  // 计算tooltip位置
  useEffect(() => {
    if (!isVisible || !anchorRef?.current || !tooltipRef?.current) {
      return
    }

    // 使用 requestAnimationFrame 确保 DOM 已经更新
    const updatePosition = () => {
      if (!anchorRef?.current || !tooltipRef?.current) {
        return
      }

      const anchorRect = anchorRef.current.getBoundingClientRect()
      const tooltipRect = tooltipRef.current.getBoundingClientRect()
      const scrollY = window.scrollY || window.pageYOffset
      const scrollX = window.scrollX || window.pageXOffset

      let top = 0
      let left = 0

      switch (position) {
        case 'top':
          top = anchorRect.top + scrollY - tooltipRect.height - 8
          left = anchorRect.left + scrollX + (anchorRect.width / 2) - (tooltipRect.width / 2)
          break
        case 'bottom':
          top = anchorRect.bottom + scrollY + 8
          left = anchorRect.left + scrollX + (anchorRect.width / 2) - (tooltipRect.width / 2)
          break
        case 'left':
          top = anchorRect.top + scrollY + (anchorRect.height / 2) - (tooltipRect.height / 2)
          left = anchorRect.left + scrollX - tooltipRect.width - 8
          break
        case 'right':
          top = anchorRect.top + scrollY + (anchorRect.height / 2) - (tooltipRect.height / 2)
          left = anchorRect.right + scrollX + 8
          break
        default:
          top = anchorRect.top + scrollY - tooltipRect.height - 8
          left = anchorRect.left + scrollX + (anchorRect.width / 2) - (tooltipRect.width / 2)
      }

      // 确保tooltip不会超出视口
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight

      if (left < 8) {
        left = 8
      } else if (left + tooltipRect.width > viewportWidth - 8) {
        left = viewportWidth - tooltipRect.width - 8
      }

      if (top < scrollY + 8) {
        top = scrollY + 8
      } else if (top + tooltipRect.height > scrollY + viewportHeight - 8) {
        top = scrollY + viewportHeight - tooltipRect.height - 8
      }

      setTooltipPosition({ top, left })
      setIsPositioned(true)
    }

    // 延迟一帧确保 DOM 已渲染
    requestAnimationFrame(() => {
      requestAnimationFrame(updatePosition)
    })
  }, [isVisible, anchorRef, position, word, translation, isLoading])
  
  // 当 tooltip 隐藏时重置位置状态
  useEffect(() => {
    if (!isVisible) {
      setIsPositioned(false)
      setTooltipPosition({ top: -9999, left: -9999 })
    }
  }, [isVisible])

  // 🔧 修复：如果不可见，则不显示
  // 如果可见但没有翻译且不在加载，仍然显示（可能是查询失败，显示空状态）
  if (!isVisible) {
    return null
  }
  
  // 调试日志：检查按钮渲染条件
  console.log('🔍 [QuickTranslationTooltip] 渲染tooltip，检查AI按钮条件', {
    word,
    translation,
    hasOnAskAI: !!onAskAI,
    shouldShowButton: !!(onAskAI && word && translation)
  })

  // 调试日志
  console.log('🔍 [QuickTranslationTooltip] 渲染tooltip:', {
    word,
    translation,
    isVisible,
    position: tooltipPosition,
    hasAnchor: !!anchorRef?.current
  })

  return (
    <div
      ref={tooltipRef}
      className="fixed z-[9999] bg-white border border-gray-300 rounded-lg shadow-lg max-w-xs p-3"
      style={{
        top: `${tooltipPosition.top}px`,
        left: `${tooltipPosition.left}px`,
        transform: 'translate(0, 0)', // 确保使用计算后的位置
        visibility: isPositioned ? 'visible' : 'hidden',
        opacity: isPositioned ? 1 : 0,
        transition: 'opacity 0.1s ease-in-out',
        pointerEvents: isPositioned ? 'auto' : 'none' // 允许交互
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {/* 单词和翻译 */}
      <div>
        {showWord && word && (
          <div className="font-semibold text-sm text-gray-900 mb-1">{word}</div>
        )}
        {isLoading ? (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm text-gray-600">正在翻译...</span>
          </div>
        ) : translation ? (
          <div className="flex items-center gap-2">
            <div className="text-sm text-gray-800 leading-relaxed flex-1">{translation}</div>
            {/* 朗读图标（只在有 onSpeak 回调且有翻译结果时显示） */}
            {onSpeak && word && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onSpeak(word)
                }}
                className="flex-shrink-0 p-1 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                title="朗读"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              </button>
            )}
          </div>
        ) : (
          // 🔧 修复：如果没有翻译且不在加载，显示提示信息
          <div className="text-sm text-gray-500 italic">
            暂无翻译
            <div className="text-xs text-gray-400 mt-1">可能原因：网络问题、API限制或单词无法翻译</div>
          </div>
        )}
      </div>
      {/* 🔧 显示来源信息：词典或翻译 */}
      <div className="text-[0.5rem] text-gray-500 mt-1">
        {translationSource === 'dictionary' ? '词典' : translationSource === 'translation' ? '翻译' : '自动翻译'}
      </div>
      {/* AI详细解释按钮 - 幽灵按钮样式 */}
      {(() => {
        const shouldShowButton = onAskAI && word && translation
        console.log('🔍 [QuickTranslationTooltip] 检查AI按钮渲染条件', {
          hasOnAskAI: !!onAskAI,
          hasWord: !!word,
          hasTranslation: !!translation,
          shouldShowButton,
          wordValue: word,
          translationValue: translation
        })
        
        if (!shouldShowButton) {
          console.log('⚠️ [QuickTranslationTooltip] 按钮不渲染，条件不满足', {
            hasOnAskAI: !!onAskAI,
            hasWord: !!word,
            hasTranslation: !!translation
          })
          return null
        }
        
        console.log('✅ [QuickTranslationTooltip] 按钮将渲染')
        
        return (
          <button
            onClick={(e) => {
              e.stopPropagation()
              e.preventDefault()
              // 🔧 如果token不足，不执行任何操作
              if (isTokenInsufficient) {
                console.log('⚠️ [QuickTranslationTooltip] Token不足，无法使用AI详细解释功能')
                return
              }
              console.log('🔘 [QuickTranslationTooltip] AI详细解释按钮被点击', { 
                word, 
                translation,
                hasOnAskAI: !!onAskAI,
                onAskAIType: typeof onAskAI
              })
              // 🔧 调用 onAskAI
              // TokenSpan 已经将 onAskAI 包装成箭头函数，会传递 token 和 sentenceIdx
              // 所以这里直接调用即可，不需要传递参数
              if (typeof onAskAI === 'function') {
                try {
                  console.log('🔘 [QuickTranslationTooltip] 准备调用 onAskAI', {
                    hasOnAskAI: !!onAskAI,
                    onAskAIType: typeof onAskAI,
                    word
                  })
                  // 🔧 直接调用，TokenSpan 已经包装了参数
                  const result = onAskAI()
                  console.log('✅ [QuickTranslationTooltip] onAskAI 调用成功', { result })
                  
                  // 🔧 如果是 Promise，等待完成
                  if (result && typeof result.then === 'function') {
                    result.catch(err => {
                      console.error('❌ [QuickTranslationTooltip] onAskAI Promise 失败', err)
                    })
                  }
                } catch (error) {
                  console.error('❌ [QuickTranslationTooltip] onAskAI 调用失败', {
                    error: error.message,
                    stack: error.stack,
                    word
                  })
                }
              } else {
                console.warn('⚠️ [QuickTranslationTooltip] onAskAI 不是函数', { 
                  onAskAI,
                  onAskAIType: typeof onAskAI,
                  word
                })
              }
            }}
            onMouseDown={(e) => {
              e.stopPropagation()
              console.log('🔘 [QuickTranslationTooltip] AI详细解释按钮 onMouseDown', { word })
            }}
            disabled={isTokenInsufficient}
            className={`mt-2 w-full px-2 py-1 text-xs rounded transition-colors border ${
              isTokenInsufficient 
                ? 'text-gray-400 bg-gray-50 border-gray-200 cursor-not-allowed' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-transparent hover:border-gray-300'
            }`}
            title={isTokenInsufficient ? "积分不足" : "AI详细解释"}
          >
            AI详细解释
          </button>
        )
      })()}
      {/* 小箭头指示器 - 白色背景，灰色边框 */}
      {position === 'bottom' && (
        <>
          {/* 灰色边框箭头 */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 w-0 h-0 border-4 border-transparent border-b-gray-300" style={{ marginBottom: '-1px' }} />
          {/* 白色填充箭头 */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 w-0 h-0 border-4 border-transparent border-b-white" style={{ marginBottom: '3px' }} />
        </>
      )}
      {position === 'top' && (
        <>
          {/* 灰色边框箭头 */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-4 border-transparent border-t-gray-300" style={{ marginTop: '-1px' }} />
          {/* 白色填充箭头 */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-4 border-transparent border-t-white" style={{ marginTop: '3px' }} />
        </>
      )}
      {position === 'left' && (
        <>
          {/* 灰色边框箭头 */}
          <div className="absolute left-full top-1/2 -translate-y-1/2 w-0 h-0 border-4 border-transparent border-l-gray-300" style={{ marginLeft: '-1px' }} />
          {/* 白色填充箭头 */}
          <div className="absolute left-full top-1/2 -translate-y-1/2 w-0 h-0 border-4 border-transparent border-l-white" style={{ marginLeft: '3px' }} />
        </>
      )}
      {position === 'right' && (
        <>
          {/* 灰色边框箭头 */}
          <div className="absolute right-full top-1/2 -translate-y-1/2 w-0 h-0 border-4 border-transparent border-r-gray-300" style={{ marginRight: '-1px' }} />
          {/* 白色填充箭头 */}
          <div className="absolute right-full top-1/2 -translate-y-1/2 w-0 h-0 border-4 border-transparent border-r-white" style={{ marginRight: '3px' }} />
        </>
      )}
    </div>
  )
}

