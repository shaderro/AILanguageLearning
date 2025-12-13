/**
 * TokenInlineTranslation - 模块化的内联翻译组件
 * 提供 hover 单词显示翻译的功能
 * 
 * @param {object} props
 * @param {string} props.word - 要翻译的单词
 * @param {string} props.sourceLang - 源语言代码 (e.g., 'de', 'en', 'zh')
 * @param {string} props.targetLang - 目标语言代码 (e.g., 'en', 'zh')
 * @param {boolean} props.enabled - 是否启用翻译功能
 * @param {number} props.hoverDelay - hover延迟时间（毫秒），默认250ms
 * @param {string} props.tooltipPosition - tooltip位置 ('top' | 'bottom' | 'left' | 'right')，默认'bottom'
 * @param {Function} props.onTranslationStart - 翻译开始时的回调
 * @param {Function} props.onTranslationComplete - 翻译完成时的回调
 * @param {Function} props.debugLogger - 调试日志函数（可选）
 * @param {Function} props.vocabListGetter - 获取本地词汇列表的函数（可选）
 * @param {Function} props.apiProvider - 自定义API提供者（可选）
 * @param {React.ReactNode} props.children - 子元素（通常是单词文本）
 */
import { useState, useRef, useCallback, useEffect } from 'react'
import QuickTranslationTooltip from '../../QuickTranslationTooltip'
import { getQuickTranslation } from '../../../services/translationService'

export default function TokenInlineTranslation({
  word,
  sourceLang = 'de',
  targetLang = null,
  enabled = true,
  hoverDelay = 250,
  tooltipPosition = 'bottom',
  onTranslationStart = null,
  onTranslationComplete = null,
  debugLogger = null,
  vocabListGetter = null,
  apiProvider = null,
  children
}) {
  const [quickTranslation, setQuickTranslation] = useState(null)
  const [showQuickTranslation, setShowQuickTranslation] = useState(false)
  const hoverTranslationTimerRef = useRef(null)
  const translationQueryRef = useRef(null)
  const anchorRef = useRef(null)

  // 辅助函数：记录日志
  const logger = useCallback((level, message, data) => {
    if (debugLogger) {
      debugLogger(level, `[TokenInlineTranslation] ${message}`, data)
    }
  }, [debugLogger])

  // 清理定时器
  const clearTranslationTimer = useCallback(() => {
    if (hoverTranslationTimerRef.current) {
      clearTimeout(hoverTranslationTimerRef.current)
      hoverTranslationTimerRef.current = null
    }
  }, [])

  // 清理翻译状态
  const clearTranslation = useCallback(() => {
    clearTranslationTimer()
    setShowQuickTranslation(false)
    setQuickTranslation(null)
    translationQueryRef.current = null
  }, [clearTranslationTimer])

  // 查询翻译
  const queryQuickTranslation = useCallback(async (wordToTranslate) => {
    if (!wordToTranslate || wordToTranslate.trim().length === 0) {
      return
    }

    // 取消之前的查询
    if (translationQueryRef.current) {
      translationQueryRef.current = null
    }

    const currentQuery = {}
    translationQueryRef.current = currentQuery

    try {
      // 确保 targetLang 有值
      const finalTargetLang = targetLang || 'en'
      const logData = { word: wordToTranslate, sourceLang, targetLang: finalTargetLang }
      logger('info', `开始查询翻译: "${wordToTranslate}"`, logData)
      
      if (onTranslationStart) {
        onTranslationStart(wordToTranslate)
      }
      
      // 构建 options，只有当 apiProvider 是函数时才传递
      const translationOptions = {
        debugLogger: (level, message, data) => logger(level, message, data),
        vocabListGetter
      }
      
      // 只有当 apiProvider 是函数时才添加到 options
      if (apiProvider && typeof apiProvider === 'function') {
        translationOptions.apiProvider = apiProvider
      }
      
      const translation = await getQuickTranslation(
        wordToTranslate,
        sourceLang,
        finalTargetLang,
        translationOptions
      )

      const resultData = { word: wordToTranslate, translation, sourceLang, targetLang: finalTargetLang }
      logger(translation ? 'success' : 'warning', `翻译查询完成: "${wordToTranslate}"`, resultData)

      // 检查查询是否已被取消
      if (translationQueryRef.current === currentQuery) {
        setQuickTranslation(translation)
        // 只有当有翻译结果时才显示 tooltip
        setShowQuickTranslation(!!translation)
        logger('info', `Tooltip状态更新: ${translation ? '显示' : '隐藏'}`, {
          ...resultData,
          showQuickTranslation: !!translation,
          hasTranslation: !!translation
        })
        translationQueryRef.current = null

        if (onTranslationComplete) {
          onTranslationComplete(wordToTranslate, translation)
        }
      } else {
        logger('warning', '翻译查询已被取消，忽略结果', { word: wordToTranslate })
      }
    } catch (error) {
      const errorData = { word: wordToTranslate, error: error.message }
      logger('error', `翻译查询失败: "${wordToTranslate}"`, errorData)
      
      if (translationQueryRef.current === currentQuery) {
        setQuickTranslation(null)
        setShowQuickTranslation(false)
        translationQueryRef.current = null
      }
    }
  }, [sourceLang, targetLang, logger, vocabListGetter, apiProvider, onTranslationStart, onTranslationComplete])

  // 处理 hover 进入
  const handleMouseEnter = useCallback(() => {
    if (!enabled || !word || word.trim().length === 0) {
      logger('warning', `Hover未触发: 条件不满足`, { enabled, word, wordLength: word?.trim().length })
      return
    }

    clearTranslationTimer()
    const finalTargetLang = targetLang || 'en'
    logger('info', `Hover触发: "${word}"`, { word, sourceLang, targetLang: finalTargetLang })

    // 延迟触发翻译查询
    hoverTranslationTimerRef.current = setTimeout(() => {
      logger('info', `延迟${hoverDelay}ms后开始查询: "${word}"`, { word })
      queryQuickTranslation(word)
    }, hoverDelay)
  }, [enabled, word, sourceLang, targetLang, hoverDelay, clearTranslationTimer, queryQuickTranslation, logger])

  // 处理 hover 离开
  const handleMouseLeave = useCallback(() => {
    if (word && word.trim().length > 0) {
      logger('info', `Hover离开: "${word}"`, { word })
    }
    clearTranslation()
  }, [word, clearTranslation, logger])

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      clearTranslationTimer()
      translationQueryRef.current = null
    }
  }, [clearTranslationTimer])

  // 如果没有启用或没有单词，直接渲染子元素
  if (!enabled || !word) {
    return <span ref={anchorRef}>{children}</span>
  }

  return (
    <>
      <span
        ref={anchorRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="inline-block"
      >
        {children}
      </span>
      {showQuickTranslation && quickTranslation && (
        <QuickTranslationTooltip
          word={word}
          translation={quickTranslation}
          isVisible={showQuickTranslation}
          anchorRef={anchorRef}
          position={tooltipPosition}
        />
      )}
    </>
  )
}

