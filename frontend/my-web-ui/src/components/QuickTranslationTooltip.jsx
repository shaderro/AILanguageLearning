/**
 * QuickTranslationTooltip - 轻量级翻译tooltip组件
 * 显示单词和简短翻译，不包含例句，不调用AI
 */
import { useEffect, useState, useRef } from 'react'
import { useUIText } from '../i18n/useUIText'

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
  isTokenInsufficient = false, // 🔧 Token是否不足（用于禁用AI详细解释按钮）
  fullWidth = false, // 🔧 是否使用全宽模式（与 anchor 宽度一致）
  uiScale = 1 // 🔧 UI缩放（仅影响 tooltip 自身字体/间距）
}) {
  const t = useUIText()
  const [tooltipPosition, setTooltipPosition] = useState({ top: -9999, left: -9999, width: null })
  const [isPositioned, setIsPositioned] = useState(false)
  const tooltipRef = useRef(null)
  const shouldCompactPaddingY = uiScale < 1 && !fullWidth

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
      let width = null

      // 🔧 如果使用全宽模式，设置宽度为 anchor 的宽度
      if (fullWidth) {
        width = anchorRect.width
      }

      switch (position) {
        case 'top':
          top = anchorRect.top + scrollY - tooltipRect.height - 8
          if (fullWidth) {
            left = anchorRect.left + scrollX
          } else {
            left = anchorRect.left + scrollX + (anchorRect.width / 2) - (tooltipRect.width / 2)
          }
          break
        case 'bottom':
          top = anchorRect.bottom + scrollY + 8
          if (fullWidth) {
            left = anchorRect.left + scrollX
          } else {
            left = anchorRect.left + scrollX + (anchorRect.width / 2) - (tooltipRect.width / 2)
          }
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
          if (fullWidth) {
            left = anchorRect.left + scrollX
          } else {
            left = anchorRect.left + scrollX + (anchorRect.width / 2) - (tooltipRect.width / 2)
          }
      }

      // 确保tooltip不会超出视口
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight

      if (fullWidth) {
        // 全宽模式：确保不超出视口，但保持左对齐
        if (left < 8) {
          left = 8
        } else if (left + width > viewportWidth - 8) {
          width = viewportWidth - left - 8
        }
      } else {
        // 非全宽模式：保持原有逻辑
        if (left < 8) {
          left = 8
        } else if (left + tooltipRect.width > viewportWidth - 8) {
          left = viewportWidth - tooltipRect.width - 8
        }
      }

      if (top < scrollY + 8) {
        top = scrollY + 8
      } else if (top + tooltipRect.height > scrollY + viewportHeight - 8) {
        top = scrollY + viewportHeight - tooltipRect.height - 8
      }

      setTooltipPosition({ top, left, width })
      setIsPositioned(true)
    }

    // 延迟一帧确保 DOM 已渲染
    requestAnimationFrame(() => {
      requestAnimationFrame(updatePosition)
    })
  }, [isVisible, anchorRef, position, word, translation, isLoading, fullWidth, uiScale])
  
  // 当 tooltip 隐藏时重置位置状态
  useEffect(() => {
    if (!isVisible) {
      setIsPositioned(false)
      setTooltipPosition({ top: -9999, left: -9999, width: null })
    }
  }, [isVisible])

  // 🔧 修复：如果不可见，则不显示
  // 如果可见但没有翻译且不在加载，仍然显示（可能是查询失败，显示空状态）
  if (!isVisible) {
    return null
  }

  return (
    <div
      ref={tooltipRef}
      className={`fixed z-[9999] bg-white border border-gray-300 rounded-lg shadow-lg ${
        // 🔧 仅缩减“词汇 tooltip”的上下边距到约 2/3（12px -> 8px）
        // 不缩放字号，不缩放整体框
        shouldCompactPaddingY ? 'px-3 py-2' : 'p-3'
      } ${fullWidth ? '' : 'max-w-xs'}`}
      style={{
        top: `${tooltipPosition.top}px`,
        left: `${tooltipPosition.left}px`,
        width: tooltipPosition.width ? `${tooltipPosition.width}px` : undefined,
        transform: 'translate(0, 0)', // 保持原始字号与整体尺寸
        visibility: isPositioned ? 'visible' : 'hidden',
        opacity: isPositioned ? 1 : 0,
        transition: 'opacity 0.1s ease-in-out',
        pointerEvents: isPositioned ? 'auto' : 'none' // 允许交互
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={(e) => e.stopPropagation()}
    >
      {/* 单词和翻译 */}
      <div>
        {showWord && word && (
          <div className="font-semibold text-sm text-gray-900 mb-1">{word}</div>
        )}
        {isLoading ? (
          <div className="text-sm text-gray-500">{t('正在翻译')}</div>
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
                title={t('朗读')}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              </button>
            )}
          </div>
        ) : (
          <div className="text-sm text-gray-500">{t('翻译失败')}</div>
        )}
      </div>
      {/* AI详细解释按钮 - 幽灵按钮样式 */}
      {onAskAI && word && translation ? (
        <button
          onClick={(e) => {
            e.stopPropagation()
            e.preventDefault()
            if (isTokenInsufficient) return
            if (typeof onAskAI === 'function') {
              try {
                const result = onAskAI()
                if (result && typeof result.then === 'function') {
                  result.catch(() => {})
                }
              } catch {
                // ignore
              }
            }
          }}
          onMouseDown={(e) => {
            e.stopPropagation()
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
      ) : null}
      {/* 小箭头指示器 - 白色背景，灰色边框 */}
      {position === 'bottom' && (
        <>
          {/* 灰色边框箭头 */}
          <div 
            className={`absolute bottom-full w-0 h-0 border-4 border-transparent border-b-gray-300 ${
              fullWidth ? 'left-4' : 'left-1/2 -translate-x-1/2'
            }`}
            style={{ marginBottom: '-1px' }}
          />
          {/* 白色填充箭头 */}
          <div 
            className={`absolute bottom-full w-0 h-0 border-4 border-transparent border-b-white ${
              fullWidth ? 'left-4' : 'left-1/2 -translate-x-1/2'
            }`}
            style={{ marginBottom: '3px' }}
          />
        </>
      )}
      {position === 'top' && (
        <>
          {/* 灰色边框箭头 */}
          <div 
            className={`absolute top-full w-0 h-0 border-4 border-transparent border-t-gray-300 ${
              fullWidth ? 'left-4' : 'left-1/2 -translate-x-1/2'
            }`}
            style={{ marginTop: '-1px' }}
          />
          {/* 白色填充箭头 */}
          <div 
            className={`absolute top-full w-0 h-0 border-4 border-transparent border-t-white ${
              fullWidth ? 'left-4' : 'left-1/2 -translate-x-1/2'
            }`}
            style={{ marginTop: '3px' }}
          />
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

