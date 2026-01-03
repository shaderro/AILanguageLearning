import { useState, useMemo, useEffect, useCallback } from 'react'
import { BaseButton, BaseCard, BaseBadge } from '../../base'
import { colors } from '../../../design-tokens'
import { useUIText } from '../../../i18n/useUIText'
import { apiService } from '../../../services/api'
import { useLanguage, languageNameToCode, languageCodeToBCP47 } from '../../../contexts/LanguageContext'

// 解析和格式化解释文本（从 ReviewCard 复制）
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
          // 🔧 修复：处理被截断的 JSON（缺少结束引号或右大括号）
          // 先尝试完整匹配（有结束引号）
          let explanationMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)['"]\s*[,}]/s)
          if (!explanationMatch) {
            // 如果完整匹配失败，尝试匹配到字符串末尾（处理被截断的 JSON）
            explanationMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)(?:['"]\s*[,}]|$)/s)
          }
          if (explanationMatch) {
            cleanText = explanationMatch[1]
              .replace(/\\n/g, '\n')
              .replace(/\\'/g, "'")
              .replace(/\\"/g, '"')
          } else {
            const normalized = jsonStr.replace(/'/g, '"')
            try {
              const parsed = JSON.parse(normalized)
              cleanText = parsed.explanation || parsed.definition || text
            } catch (e2) {
              // 如果还是失败，尝试从截断的 JSON 中提取 explanation 值
              const truncatedMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*)/)
              if (truncatedMatch) {
                cleanText = truncatedMatch[1]
                  .replace(/\\n/g, '\n')
                  .replace(/\\'/g, "'")
                  .replace(/\\"/g, '"')
              } else {
                cleanText = text
              }
            }
          }
        }
      } else {
        // 🔧 修复：如果没有找到完整的 JSON 对象（可能被截断），尝试直接提取 explanation 字段
        const truncatedMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*)/)
        if (truncatedMatch) {
          cleanText = truncatedMatch[1]
            .replace(/\\n/g, '\n')
            .replace(/\\'/g, "'")
            .replace(/\\"/g, '"')
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
  cleanText = cleanText.replace(/\\n/g, '\n')
  cleanText = cleanText.replace(/\n{3,}/g, '\n\n')
  cleanText = cleanText.trim()
  
  return cleanText
}

const GrammarReviewCard = ({
  // Grammar data
  grammar,
  // Progress bar props
  currentProgress = 0,
  totalProgress = 0,
  onClose,
  onPrevious,
  onNext,
  // Answer callbacks
  onDontKnow,
  onKnow,
}) => {
  const t = useUIText()
  const { selectedLanguage } = useLanguage() // 🔧 获取全局语言状态
  const [showDefinitions, setShowDefinitions] = useState(false)
  const [currentExampleIndex, setCurrentExampleIndex] = useState(0)
  const [grammarWithExamples, setGrammarWithExamples] = useState(grammar)

  // 加载完整的 grammar 详情（包含 examples）
  useEffect(() => {
    setShowDefinitions(false)
    setCurrentExampleIndex(0)
    
    if (grammar && (!grammar.examples || !Array.isArray(grammar.examples) || grammar.examples.length === 0)) {
      const grammarId = grammar.rule_id
      if (grammarId) {
        apiService.getGrammarById(grammarId)
          .then(response => {
            const detailData = response?.data?.data || response?.data || response
            if (detailData && detailData.examples && Array.isArray(detailData.examples) && detailData.examples.length > 0) {
              setGrammarWithExamples({ ...grammar, ...detailData })
            } else {
              setGrammarWithExamples(grammar)
            }
          })
          .catch(error => {
            console.warn('⚠️ [GrammarReviewCard] Failed to load grammar detail:', error)
            setGrammarWithExamples(grammar)
          })
      } else {
        setGrammarWithExamples(grammar)
      }
    } else {
      setGrammarWithExamples(grammar)
    }
  }, [grammar])

  // 提取例句和例句解释
  const exampleData = useMemo(() => {
    const currentGrammar = grammarWithExamples || grammar
    if (!currentGrammar?.examples || !Array.isArray(currentGrammar.examples)) {
      return []
    }
    return currentGrammar.examples
      .map(ex => ({
        sentence: ex.original_sentence,
        explanation: ex.context_explanation || ex.explanation_context || ex.explanation || null
      }))
      .filter(ex => ex.sentence)
  }, [grammarWithExamples, grammar])
  
  const exampleSentences = exampleData.map(ex => ex.sentence)

  // 获取语法规则名称
  const ruleName = grammarWithExamples?.rule_name || grammar?.rule_name || ''

  // 获取解释文本
  const explanation = useMemo(() => {
    const currentGrammar = grammarWithExamples || grammar
    return parseExplanation(currentGrammar?.rule_summary || currentGrammar?.explanation || '暂无解释')
  }, [grammarWithExamples, grammar])
  
  // 🔧 朗读功能
  const [speakingSentenceIndex, setSpeakingSentenceIndex] = useState(null)
  
  // 组件卸载时清理朗读
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])
  
  // 🔧 根据语言代码获取对应的语音
  const getVoiceForLanguage = useCallback((langCode) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      return null
    }
    
    const availableVoices = window.speechSynthesis.getVoices()
    
    if (!availableVoices || availableVoices.length === 0) {
      console.warn('⚠️ [GrammarReviewCard] 没有可用的语音')
      return null
    }
    
    const targetLang = languageCodeToBCP47(langCode)
    
    // 优先查找完全匹配的语音
    let voice = availableVoices.find(v => v.lang === targetLang)
    
    // 如果找不到，查找语言代码前缀匹配的
    if (!voice) {
      const langPrefix = targetLang.split('-')[0]
      voice = availableVoices.find(v => v.lang && v.lang.startsWith(langPrefix))
    }
    
    // 如果还是找不到，使用默认语音（通常是第一个）
    if (!voice && availableVoices.length > 0) {
      voice = availableVoices[0]
      console.warn(`⚠️ [GrammarReviewCard] 未找到 ${targetLang} 语音，使用默认语音: ${voice.name}`)
    }
    
    return voice || null
  }, [])

  // 🔧 通用朗读函数（使用全局语言状态）
  const handleSpeak = useCallback((text, onStart, onEnd) => {
    if (!text) return
    
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      // 🔧 使用全局语言状态
      const langCode = languageNameToCode(selectedLanguage)
      const targetLang = languageCodeToBCP47(langCode)
      
      // 🔧 获取对应的语音对象
      const voice = getVoiceForLanguage(langCode)
      
      const utterance = new SpeechSynthesisUtterance(text)
      
      // 🔧 显式设置语音对象（这是关键！）
      if (voice) {
        utterance.voice = voice
      }
      utterance.lang = targetLang
      utterance.rate = 0.9
      utterance.pitch = 1.0
      utterance.volume = 1.0
      
      utterance.onstart = () => {
        if (onStart) onStart()
      }
      
      utterance.onend = () => {
        if (onEnd) onEnd()
      }
      
      utterance.onerror = () => {
        if (onEnd) onEnd()
      }
      
      window.speechSynthesis.speak(utterance)
    }
  }, [selectedLanguage, getVoiceForLanguage])
  
  const handleSpeakSentence = (sentence, index) => {
    if (!sentence) return
    
    // 如果正在朗读这个句子，停止朗读
    if (speakingSentenceIndex === index && typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel()
      setSpeakingSentenceIndex(null)
      return
    }
    
    // 🔧 开始朗读句子，使用全局语言状态
    handleSpeak(
      sentence,
      () => setSpeakingSentenceIndex(index),
      () => setSpeakingSentenceIndex(null)
    )
  }

  const handlePreviousExample = () => {
    if (currentExampleIndex > 0) {
      setCurrentExampleIndex(currentExampleIndex - 1)
    }
  }

  const handleNextExample = () => {
    if (currentExampleIndex < exampleSentences.length - 1) {
      setCurrentExampleIndex(currentExampleIndex + 1)
    }
  }

  const progressPercentage = totalProgress > 0 ? (currentProgress / totalProgress) * 100 : 0

  const handleAnswer = (choice) => {
    if (choice === 'unknown' && onDontKnow) {
      onDontKnow()
    } else if (choice === 'know' && onKnow) {
      onKnow()
    }
  }

  return (
    <BaseCard
      padding="lg"
      className="w-full max-w-2xl mx-auto"
      style={{
        '--card-bg': colors.semantic.bg.primary,
        '--card-border': colors.semantic.border.default,
      }}
    >
        <div className="space-y-6">
          {/* Progress Bar */}
          <div className="flex items-center gap-3">
            {/* Close Button */}
            {onClose && (
              <button
                onClick={onClose}
                className="p-1 rounded hover:bg-gray-100 transition-colors"
                aria-label="Close"
              >
                <svg
                  className="w-5 h-5 text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}

            {/* Progress Bar */}
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{
                  width: `${progressPercentage}%`,
                  backgroundColor: colors.primary[500],
                }}
              />
            </div>

            {/* Progress Text */}
            <span className="text-sm text-gray-600 whitespace-nowrap">
              {currentProgress}/{totalProgress}
            </span>

            {/* Navigation Controls */}
            <div className="flex items-center gap-1">
              {onPrevious && (
                <button
                  onClick={onPrevious}
                  className="p-1 rounded hover:bg-gray-100 transition-colors"
                  aria-label="Previous"
                >
                  <svg
                    className="w-5 h-5 text-gray-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 19l-7-7 7-7"
                    />
                  </svg>
                </button>
              )}
              {onNext && (
                <button
                  onClick={onNext}
                  className="p-1 rounded hover:bg-gray-100 transition-colors"
                  aria-label="Next"
                >
                  <svg
                    className="w-5 h-5 text-gray-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
              )}
            </div>
          </div>
          {/* Part of Speech Badge - 空白占位符 */}
          <div className="flex justify-center">
            <div className="h-6"></div>
          </div>

          {/* Rule Name */}
          <h1 className="text-4xl font-bold text-center text-gray-900">
            {ruleName}
          </h1>

          {/* Example Sentence Card */}
          {exampleSentences.length > 0 && (
            <div className="bg-gray-100 rounded-lg p-4">
              <div className="flex items-start gap-2 mb-4">
                <p className="text-lg text-gray-800 text-center flex-1 whitespace-normal break-words">
                  {exampleSentences[currentExampleIndex]}
                </p>
                {/* 🔧 朗读图标按钮 */}
                <button
                  onClick={() => handleSpeakSentence(exampleSentences[currentExampleIndex], currentExampleIndex)}
                  className="p-1.5 rounded-lg hover:bg-gray-200 transition-colors flex-shrink-0"
                  aria-label={speakingSentenceIndex === currentExampleIndex ? '停止朗读' : '朗读句子'}
                  title={speakingSentenceIndex === currentExampleIndex ? '停止朗读' : '朗读句子'}
                >
                  {speakingSentenceIndex === currentExampleIndex ? (
                    <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <rect x="9" y="9" width="6" height="6" rx="1" />
                      <circle cx="12" cy="12" r="10" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path d="M11 5L6 9H2v6h4l5 4V5z" />
                      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                    </svg>
                  )}
                </button>
              </div>

              {/* Sentence Explanation - 显示在灰色框内，当 showDefinitions 为 true 时 */}
              {showDefinitions && exampleData[currentExampleIndex]?.explanation && (
                <>
                  <div className="border-t border-gray-300 my-3"></div>
                  <p className="text-sm text-gray-600 whitespace-normal break-words">
                    {parseExplanation(exampleData[currentExampleIndex].explanation)}
                  </p>
                </>
              )}

              {/* Example Navigation */}
              {exampleSentences.length > 1 && (
                <div className="flex items-center justify-center gap-4 mt-4">
                  <button
                    onClick={handlePreviousExample}
                    disabled={currentExampleIndex === 0}
                    className="p-2 rounded-lg hover:bg-gray-200 disabled:opacity-30 transition-colors"
                    aria-label="Previous example"
                  >
                    <svg
                      className="w-5 h-5 text-gray-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                  </button>

                  <div className="flex items-center gap-1.5">
                    {exampleSentences.map((_, index) => (
                      <div
                        key={index}
                        className="w-2 h-2 rounded-full"
                        style={{
                          backgroundColor:
                            index === currentExampleIndex
                              ? colors.primary[600]
                              : colors.gray[300],
                        }}
                      />
                    ))}
                  </div>

                  <button
                    onClick={handleNextExample}
                    disabled={currentExampleIndex === exampleSentences.length - 1}
                    className="p-2 rounded-lg hover:bg-gray-200 disabled:opacity-30 transition-colors"
                    aria-label="Next example"
                  >
                    <svg
                      className="w-5 h-5 text-gray-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Toggle Definitions Button */}
          <div className="flex justify-center">
            <BaseButton
              variant="secondary"
              size="sm"
              onClick={() => setShowDefinitions(!showDefinitions)}
              leftIcon={
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  {showDefinitions ? (
                    <>
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                      />
                    </>
                  ) : (
                    <>
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
                      />
                      <circle cx="12" cy="12" r="3" />
                    </>
                  )}
                </svg>
              }
            >
              {showDefinitions ? t('隐藏释义') : t('显示释义')}
            </BaseButton>
          </div>

          {/* Definitions Section */}
          {showDefinitions && (
            <div className="pt-4 border-t border-gray-200">
              <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {explanation}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4 pt-4 justify-center">
            <BaseButton
              variant="danger"
              size="lg"
              onClick={() => handleAnswer('unknown')}
              className="flex-1 max-w-[40%]"
              style={{
                '--btn-bg': colors.danger[400],
                '--btn-bg-hover': colors.danger[500],
                '--btn-text': '#ffffff',
              }}
            >
              {t('不认识')}
            </BaseButton>
            <BaseButton
              variant="primary"
              size="lg"
              onClick={() => handleAnswer('know')}
              className="flex-1 max-w-[40%]"
              style={{
                '--btn-bg': '#10b981', // emerald-500 - 比主题色略饱和的柔和绿色
                '--btn-bg-hover': '#059669', // emerald-600
                '--btn-text': '#ffffff',
              }}
            >
              {t('认识')}
            </BaseButton>
          </div>
        </div>
    </BaseCard>
  )
}

export default GrammarReviewCard

