/**
 * ⚠️ IMPORTANT: Language Logic Safety Boundaries
 * 
 * UI language ≠ System language
 * 
 * This component uses useTranslate() for presentation-only purposes:
 * - Displaying suggested questions in the appropriate language
 * - Showing UI labels and placeholders
 * 
 * 🚫 STRICTLY FORBIDDEN:
 * - ❌ Do NOT affect data fetching logic (React Query, useArticle, useApi)
 * - ❌ Do NOT affect hooks lifecycle (enabled, queryKey, useEffect dependencies)
 * - ❌ Do NOT affect conditional rendering related to loading / error states
 * 
 * Language is presentation-only and MUST NOT affect:
 * - React Query queryKeys
 * - useArticle / useApi enabled states
 * - isLoading / early return logic
 * - Data fetching dependencies
 */

import { useState, useEffect, useMemo } from 'react'
import { colors } from '../../../design-tokens'
import { useTranslate } from '../../../i18n/useTranslate'
import { useUiLanguage } from '../../../contexts/UiLanguageContext'

const SelectionType = Object.freeze({
  WORD: 'WORD',
  PHRASE: 'PHRASE',
  SENTENCE: 'SENTENCE',
  LONG_SPAN: 'LONG_SPAN',
})

const WORD_PROMPTS = [
  { zh: '这个词在这里是什么意思？', en: 'What does this word mean here?' },
  { zh: '这部分在句子里起什么作用？', en: 'What role does this part play in the sentence?' },
]

const PHRASE_PROMPTS = [
  { zh: '这部分在句子里起什么作用？', en: 'What role does this part play in the sentence?' },
  { zh: '这部分在这里是什么意思？', en: 'What does this part mean here?' },
]

const SENTENCE_PROMPTS = [
  { zh: '这句话是什么意思？', en: 'What does this sentence mean?' },
  { zh: '你能拆解一下这句话吗？', en: 'Can you break down this sentence?' },
]

const LONG_SPAN_PROMPTS = [
  { zh: '你能拆解一下这部分吗？', en: 'Can you break down this part?' },
  { zh: '这部分的结构是什么？', en: 'What is the structure of this part?' },
]

const promptPoolByType = {
  [SelectionType.WORD]: WORD_PROMPTS,
  [SelectionType.PHRASE]: PHRASE_PROMPTS,
  [SelectionType.SENTENCE]: SENTENCE_PROMPTS,
  [SelectionType.LONG_SPAN]: LONG_SPAN_PROMPTS,
}

const hashString = (value = '') => {
  let hash = 0
  const text = String(value)
  for (let i = 0; i < text.length; i += 1) {
    hash = ((hash << 5) - hash + text.charCodeAt(i)) | 0
  }
  return Math.abs(hash)
}

const diversify = (pool, seed = '') => {
  const shuffled = [...pool]
  if (shuffled.length <= 1) {
    return shuffled
  }

  let currentSeed = hashString(seed || shuffled.map((item) => `${item.zh}|${item.en}`).join('||'))
  for (let i = shuffled.length - 1; i > 0; i -= 1) {
    currentSeed = (currentSeed * 1664525 + 1013904223) % 4294967296
    const j = currentSeed % (i + 1)
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }

  return shuffled
}

const detectSelectionType = (ctx) => {
  if (ctx.hasSelectedSentence) {
    return SelectionType.SENTENCE
  }
  if (ctx.tokenCount === 1) {
    return SelectionType.WORD
  }
  if (ctx.tokenCount <= 8) {
    return SelectionType.PHRASE
  }
  return SelectionType.LONG_SPAN
}

const getLocalizedPrompt = (prompt, uiLanguage) => (uiLanguage === 'en' ? prompt.en : prompt.zh)

const getSuggestedQuestions = (ctx, uiLanguage) => {
  const type = detectSelectionType(ctx)
  const pool = promptPoolByType[type] || SENTENCE_PROMPTS
  const promptSeed = `${type}|${ctx.selectedText}|${ctx.fullSentence}|${ctx.tokenCount}|${ctx.hasSelectedSentence}`

  return diversify(pool, promptSeed).map((prompt) => getLocalizedPrompt(prompt, uiLanguage))
}

const SuggestedQuestions = ({ 
  quotedText, 
  onQuestionSelect, 
  isVisible = false,
  inputValue = '',
  onQuestionClick,
  tokenCount = 1,  // 新增：选中的token数量，默认为1
  hasSelectedSentence = false,  // 新增：是否选择了整句
  fullSentence = '',
  disabled = false  // 🔧 新增：是否禁用（main assistant 正在处理时）
}) => {
  const [selectedQuestion, setSelectedQuestion] = useState(null)
  const t = useTranslate()
  const { uiLanguage } = useUiLanguage()
  
  // ⚠️ Language detection: Presentation-only, does NOT affect data fetching or component lifecycle
  // Using useTranslate() hook which uses UI language context (same as header)

  const context = useMemo(() => ({
    selectedText: quotedText || '',
    fullSentence: fullSentence || (hasSelectedSentence ? quotedText || '' : ''),
    tokenCount,
    hasSelectedSentence,
  }), [quotedText, fullSentence, tokenCount, hasSelectedSentence])

  const suggestedQuestions = useMemo(
    () => getSuggestedQuestions(context, uiLanguage),
    [context, uiLanguage],
  )

  // 当组件显示时，重置选中状态
  useEffect(() => {
    if (isVisible) {
      setSelectedQuestion(null)
    }
  }, [isVisible])

  // 当输入框有内容时，取消高亮
  useEffect(() => {
    if (inputValue.trim() !== '') {
      setSelectedQuestion(null)
    }
  }, [inputValue])

  const handleQuestionClick = (question) => {
    // 不再设置 selectedQuestion，避免持续深色状态
    onQuestionSelect(question)
    // 通知父组件问题被点击
    if (onQuestionClick) {
      onQuestionClick(question)
    }
  }

  // 点击其他位置取消高亮
  const handleContainerClick = (e) => {
    // 如果点击的是容器而不是按钮，取消高亮
    if (e.target === e.currentTarget) {
      setSelectedQuestion(null)
    }
  }

  if (!isVisible || !quotedText) return null

  return (
    <div 
      data-keep-quote
      className="w-full bg-gray-50 border-t border-gray-200 px-4 py-3 flex-shrink-0"
      onClick={handleContainerClick}
    >
      <div className="text-sm text-gray-600 mb-2">
        {t("你可能想问...")}
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestedQuestions.map((question, index) => (
          <button
            key={index}
            onClick={() => handleQuestionClick(question)}
            disabled={disabled}
            className="px-3 py-1.5 text-sm rounded-lg border bg-white text-gray-700 border-gray-300 transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              '--hover-bg': colors.primary[50],
              '--hover-border': colors.primary[300],
              '--hover-text': colors.primary[700],
              '--active-bg': colors.primary[600],
              '--active-border': colors.primary[600],
              '--active-text': '#ffffff'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = colors.primary[50]
              e.currentTarget.style.borderColor = colors.primary[300]
              e.currentTarget.style.color = colors.primary[700]
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'white'
              e.currentTarget.style.borderColor = '#d1d5db'
              e.currentTarget.style.color = '#374151'
            }}
            onMouseDown={(e) => {
              e.currentTarget.style.backgroundColor = colors.primary[600]
              e.currentTarget.style.borderColor = colors.primary[600]
              e.currentTarget.style.color = '#ffffff'
            }}
            onMouseUp={(e) => {
              // 松开后立即恢复悬停状态（如果鼠标还在按钮上）或默认状态
              const rect = e.currentTarget.getBoundingClientRect()
              const x = e.clientX
              const y = e.clientY
              // 检查鼠标是否仍在按钮内
              if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
                e.currentTarget.style.backgroundColor = colors.primary[50]
                e.currentTarget.style.borderColor = colors.primary[300]
                e.currentTarget.style.color = colors.primary[700]
              } else {
                e.currentTarget.style.backgroundColor = 'white'
                e.currentTarget.style.borderColor = '#d1d5db'
                e.currentTarget.style.color = '#374151'
              }
            }}
          >
            "{question}"
          </button>
        ))}
      </div>
    </div>
  )
}

export default SuggestedQuestions
