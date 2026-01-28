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

import { useState, useEffect } from 'react'
import { colors } from '../../../design-tokens'
import { useTranslate } from '../../../i18n/useTranslate'

const SuggestedQuestions = ({ 
  quotedText, 
  onQuestionSelect, 
  isVisible = false,
  inputValue = '',
  onQuestionClick,
  tokenCount = 1,  // 新增：选中的token数量，默认为1
  hasSelectedSentence = false,  // 新增：是否选择了整句
  disabled = false  // 🔧 新增：是否禁用（main assistant 正在处理时）
}) => {
  const [selectedQuestion, setSelectedQuestion] = useState(null)
  const t = useTranslate()
  
  // ⚠️ Language detection: Presentation-only, does NOT affect data fetching or component lifecycle
  // Using useTranslate() hook which uses UI language context (same as header)

  // 单个token的建议问题
  const singleTokenQuestions = [
    t("这个词是什么意思？"),
    t("这个词有什么词根词缀吗？")
  ]

  // 多个token（短语）的建议问题
  const multipleTokensQuestions = [
    t("这些词是什么意思？"),
    t("这部分的语法结构是什么？")
  ]

  // 整句话的建议问题
  const sentenceQuestions = [
    t("这句话是什么意思？"),
    t("这句话的语法结构是什么？")
  ]

  // 根据选择类型和token数量选择对应的问题列表
  const getSuggestedQuestions = () => {
    // 如果选择了整句，优先使用句子问题
    if (hasSelectedSentence) {
      return sentenceQuestions
    }
    
    // 否则根据token数量选择
    if (tokenCount === 1) {
      return singleTokenQuestions
    } else if (tokenCount > 1 && tokenCount < 10) {
      // 假设小于10个token为短语
      return multipleTokensQuestions
    } else {
      // 10个及以上token
      return sentenceQuestions
    }
  }

  const suggestedQuestions = getSuggestedQuestions()

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
