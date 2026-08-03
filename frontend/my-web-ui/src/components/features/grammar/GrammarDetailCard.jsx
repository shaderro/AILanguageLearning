import { useState, useMemo, useEffect, useCallback } from 'react'
import { splitExplanationLines } from '../../../utils/explanationFormat'
import {
  parseStructuredGrammarExplanation,
  unwrapGrammarExplanation,
} from '../../../utils/grammarExplanationFormat'
import { BaseCard, BackButton } from '../../base'
import { colors, componentTokens } from '../../../design-tokens'
import { useUIText } from '../../../i18n/useUIText'
import { apiService } from '../../../services/api'
import { useLanguage, languageNameToCode, languageCodeToBCP47 } from '../../../contexts/LanguageContext'
import {
  fetchGrammarDetail,
  getCachedGrammarDetail,
  hasGrammarExamples,
  setCachedGrammarDetail,
} from '../../../utils/grammarDetailSessionCache'

const parseExplanation = unwrapGrammarExplanation

const renderInlineMarkdown = (text) => {
  const content = String(text || '')
  if (!content) return null

  const parts = content.split(/(\*\*[^*]+\*\*)/g)
  return parts.filter(Boolean).map((part, index) => {
    const boldMatch = part.match(/^\*\*([^*]+)\*\*$/)
    if (boldMatch) {
      return <strong key={index}>{boldMatch[1]}</strong>
    }
    return <span key={index}>{part}</span>
  })
}

const GrammarDetailCard = ({
  grammar,
  onPrevious,
  onNext,
  onBack,
  currentIndex,
  totalCount,
  loading = false,
}) => {
  const t = useUIText()
  const { selectedLanguage } = useLanguage() // 🔧 获取全局语言状态
  const [grammarWithDetails, setGrammarWithDetails] = useState(() => {
    if (!grammar?.rule_id) return grammar
    return getCachedGrammarDetail(grammar.rule_id) || grammar
  })
  const [articleTitles, setArticleTitles] = useState({})

  // 加载完整的 grammar 详情（包含 examples），优先使用 session 缓存
  useEffect(() => {
    let cancelled = false

    if (!grammar) {
      setGrammarWithDetails(null)
      return undefined
    }

    const grammarId = grammar.rule_id
    if (!grammarId) {
      setGrammarWithDetails(grammar)
      return undefined
    }

    const cached = getCachedGrammarDetail(grammarId)
    if (cached) {
      setGrammarWithDetails({ ...grammar, ...cached })
      if (hasGrammarExamples(cached)) {
        return undefined
      }
    } else if (hasGrammarExamples(grammar)) {
      setGrammarWithDetails(grammar)
      setCachedGrammarDetail(grammarId, grammar)
      return undefined
    } else {
      setGrammarWithDetails(cached ? { ...grammar, ...cached } : grammar)
    }

    fetchGrammarDetail(grammarId, { baseGrammar: grammar })
      .then((merged) => {
        if (cancelled) return
        setGrammarWithDetails(merged || grammar)
      })

    return () => {
      cancelled = true
    }
  }, [grammar?.rule_id, grammar])

  // 为每个例句加载文章标题
  useEffect(() => {
    const examples = grammarWithDetails?.examples || []
    if (examples.length === 0) return

    const textIdsToLoad = examples
      .map(ex => ex.text_id || ex.article_id)
      .filter(id => id && !articleTitles[id])

    if (textIdsToLoad.length === 0) return

    Promise.all(
      textIdsToLoad.map(textId =>
        apiService.getArticleById(textId)
          .then(response => {
            const articleData = response?.data?.data || response?.data || response
            return { textId, title: articleData?.text_title || articleData?.title || null }
          })
          .catch(error => {
            console.warn(`⚠️ [GrammarDetailCard] Failed to load article ${textId}:`, error)
            return { textId, title: null }
          })
      )
    ).then(results => {
      const newTitles = {}
      results.forEach(({ textId, title }) => {
        if (textId && title) {
          newTitles[textId] = title
        }
      })
      if (Object.keys(newTitles).length > 0) {
        setArticleTitles(prev => ({ ...prev, ...newTitles }))
      }
    })
  }, [grammarWithDetails?.examples, articleTitles])

  const ruleName = grammarWithDetails?.rule_name || ''
  const rawRuleSummary = grammarWithDetails?.rule_summary || grammarWithDetails?.explanation || ''

  const structuredExplanation = useMemo(
    () => parseStructuredGrammarExplanation(rawRuleSummary),
    [rawRuleSummary],
  )

  const ruleSummary = structuredExplanation.isStructured
    ? ''
    : parseExplanation(rawRuleSummary)

  const rulePoints = useMemo(() => splitExplanationLines(ruleSummary), [ruleSummary])

  const hasStructuredSections = structuredExplanation.isStructured && (
    structuredExplanation.coreMeaning.length > 0
    || structuredExplanation.structure.length > 0
    || Boolean(structuredExplanation.sentenceMapping)
    || structuredExplanation.recognitionTip.length > 0
  )

  const sectionLabels = structuredExplanation.sectionLabels
  const useDefinitionHighlight = hasStructuredSections
  const explanationDividerColor = colors.gray[200]
  const whiteSectionBg = { backgroundColor: colors.semantic.bg.primary }
  const definitionSectionBg = useDefinitionHighlight
    ? { backgroundColor: colors.primary[50] }
    : whiteSectionBg
  const explanationCardStyle = {
    backgroundColor: colors.semantic.bg.primary,
    borderColor: useDefinitionHighlight ? colors.primary[100] : colors.gray[200],
  }
  const grammarSectionSpacing = {
    padding: '14px',
    contentGap: '6px',
    definitionGap: '14px',
    inlineGap: '8px',
  }
  const scaleLineHeight = (value) => value * 0.8
  const grammarLineHeights = {
    definition: scaleLineHeight(1.7),
    body: scaleLineHeight(1.625),
    heading: scaleLineHeight(1.75),
  }
  const definitionHeroStyle = {
    fontSize: '17px',
    lineHeight: grammarLineHeights.definition,
  }
  const explanationSectionStyle = {
    padding: grammarSectionSpacing.padding,
    display: 'flex',
    flexDirection: 'column',
    gap: grammarSectionSpacing.contentGap,
  }
  const secondaryListStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: grammarSectionSpacing.contentGap,
    listStyle: 'none',
    margin: 0,
    padding: 0,
  }
  const mappingLines = useMemo(() => {
    if (!structuredExplanation.sentenceMapping) return []
    return structuredExplanation.sentenceMapping.split('\n').map((line) => line.trim()).filter(Boolean)
  }, [structuredExplanation.sentenceMapping])

  const structuredSectionFlags = [
    structuredExplanation.coreMeaning.length > 0,
    structuredExplanation.structure.length > 0,
    mappingLines.length > 0,
    structuredExplanation.recognitionTip.length > 0,
  ]
  const showExplanationDividerBefore = (sectionIndex) => (
    structuredSectionFlags.slice(0, sectionIndex).some(Boolean)
  )
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
      console.warn('⚠️ [GrammarDetailCard] 没有可用的语音')
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
      console.warn(`⚠️ [GrammarDetailCard] 未找到 ${targetLang} 语音，使用默认语音: ${voice.name}`)
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

  const examples = useMemo(() => {
    if (!grammarWithDetails?.examples || !Array.isArray(grammarWithDetails.examples)) {
      return []
    }
    return grammarWithDetails.examples
      .filter(ex => ex.original_sentence)
      .map(ex => {
        const textId = ex.text_id || ex.article_id || null
        const title = articleTitles[textId] || ex.text_title || ex.source || null
        return {
          sentence: ex.original_sentence,
          explanation: ex.context_explanation || ex.explanation_context || ex.explanation || null,
          source: title,
          text_id: textId,
          sentence_id: ex.sentence_id || null,
        }
      })
  }, [grammarWithDetails, articleTitles])

  const isPending = loading || (grammar?.rule_id && !grammarWithDetails)

  if (isPending) {
    return (
      <div className="w-full max-w-4xl mx-auto" style={{ backgroundColor: 'white' }}>
        <BaseCard padding="lg" className="w-full" style={{ backgroundColor: 'white' }}>
          <div className="text-center py-8" style={{ backgroundColor: 'white' }}>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4" style={{ borderColor: colors.primary[500] }}></div>
            <p className="text-gray-600">{t('加载中')}</p>
          </div>
        </BaseCard>
      </div>
    )
  }

  if (!grammarWithDetails) {
    return (
      <BaseCard padding="lg" className="w-full max-w-4xl mx-auto">
        <div className="text-center py-8">
          <p className="text-gray-600">{t('未找到语法数据')}</p>
        </div>
      </BaseCard>
    )
  }

  return (
    <div className="w-full max-w-4xl mx-auto" style={{ backgroundColor: 'white' }}>
      <BaseCard
        padding="lg"
        className="w-full relative"
        style={{
          '--card-bg': colors.semantic.bg.primary,
          '--card-border': colors.semantic.border.default,
          backgroundColor: 'white',
        }}
      >
        {/* 左上角返回按钮 */}
        {onBack && (
          <div className="absolute top-6 left-6 z-10">
            <BackButton onClick={onBack} />
          </div>
        )}
        
        {/* 右上角分页控件 */}
        {(onPrevious || onNext) && currentIndex !== undefined && totalCount !== undefined && (
          <div className="absolute top-6 right-6 z-10 flex items-center gap-2">
            <span className="text-sm" style={{ color: colors.semantic.text.secondary }}>
              {currentIndex + 1}/{totalCount}
            </span>
            {onPrevious && (
              <button
                onClick={onPrevious}
                className="p-1.5 rounded hover:bg-gray-100 transition-colors"
                aria-label="上一个"
                style={{
                  color: colors.semantic.text.secondary,
                }}
              >
                <svg
                  className="w-4 h-4"
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
                className="p-1.5 rounded hover:bg-gray-100 transition-colors"
                aria-label="下一个"
                style={{
                  color: colors.semantic.text.secondary,
                }}
              >
                <svg
                  className="w-4 h-4"
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
        )}
        
        <div className="space-y-6">
          {/* 语法规则标题区域 */}
          <div className="flex flex-col items-center gap-2">
            <h1 
              className="text-center break-words"
              style={{
                fontSize: componentTokens.grammarVocabTitle.fontSize,
                fontWeight: componentTokens.grammarVocabTitle.fontWeight,
                color: componentTokens.grammarVocabTitle.color,
                lineHeight: componentTokens.grammarVocabTitle.lineHeight,
                maxWidth: componentTokens.grammarVocabTitle.maxWidth,
                textAlign: componentTokens.grammarVocabTitle.textAlign,
                wordWrap: componentTokens.grammarVocabTitle.wordWrap,
                overflowWrap: componentTokens.grammarVocabTitle.overflowWrap,
              }}
            >
              {ruleName}
            </h1>
          </div>

          {/* 规则说明：结构化四区块（对齐 Vocab Detail）或 legacy 回退 */}
          {hasStructuredSections && (
            <section>
              <div
                className="rounded-lg border overflow-hidden"
                style={explanationCardStyle}
              >
                {structuredExplanation.coreMeaning.length > 0 && (
                  <div
                    style={{
                      ...definitionSectionBg,
                      ...explanationSectionStyle,
                      gap: grammarSectionSpacing.definitionGap,
                    }}
                  >
                    <h2
                      className="font-semibold text-lg"
                      style={{ color: colors.semantic.text.secondary, lineHeight: grammarLineHeights.heading }}
                    >
                      {sectionLabels.coreMeaning}
                    </h2>
                    <div
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: grammarSectionSpacing.definitionGap,
                      }}
                    >
                      {structuredExplanation.coreMeaning.map((point, index) => (
                        <div
                          key={index}
                          className="flex items-start"
                          style={{ gap: grammarSectionSpacing.inlineGap }}
                        >
                          <span
                            className="shrink-0"
                            style={{
                              color: colors.primary[500],
                              fontSize: definitionHeroStyle.fontSize,
                              lineHeight: definitionHeroStyle.lineHeight,
                            }}
                          >
                            •
                          </span>
                          <div
                            className="whitespace-pre-wrap flex-1"
                            style={{
                              color: colors.semantic.text.primary,
                              fontSize: definitionHeroStyle.fontSize,
                              lineHeight: definitionHeroStyle.lineHeight,
                            }}
                          >
                            {renderInlineMarkdown(point)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {structuredExplanation.structure.length > 0 && (
                  <>
                    {showExplanationDividerBefore(1) ? (
                      <div className="border-t" style={{ borderColor: explanationDividerColor }} aria-hidden="true" />
                    ) : null}
                    <div style={{ ...explanationSectionStyle, ...whiteSectionBg }}>
                      <h2 className="text-lg font-semibold" style={{ color: colors.semantic.text.secondary, lineHeight: grammarLineHeights.heading }}>
                        {sectionLabels.structure}
                      </h2>
                      <ul style={secondaryListStyle}>
                        {structuredExplanation.structure.map((point, index) => (
                          <li
                            key={index}
                            className="flex items-start"
                            style={{ gap: grammarSectionSpacing.inlineGap }}
                          >
                            <span
                              className="shrink-0"
                              style={{ color: colors.primary[500], lineHeight: grammarLineHeights.body }}
                            >
                              •
                            </span>
                            <span
                              className="whitespace-pre-wrap flex-1"
                              style={{ color: colors.semantic.text.primary, lineHeight: grammarLineHeights.body }}
                            >
                              {renderInlineMarkdown(point)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}

                {mappingLines.length > 0 && (
                  <>
                    {showExplanationDividerBefore(2) ? (
                      <div className="border-t" style={{ borderColor: explanationDividerColor }} aria-hidden="true" />
                    ) : null}
                    <div style={{ ...explanationSectionStyle, ...whiteSectionBg }}>
                      <h2 className="text-lg font-semibold" style={{ color: colors.semantic.text.secondary, lineHeight: grammarLineHeights.heading }}>
                        {sectionLabels.sentenceMapping}
                      </h2>
                      <ul style={secondaryListStyle}>
                        {mappingLines.map((line, index) => (
                          <li
                            key={index}
                            className="flex items-start"
                            style={{ gap: grammarSectionSpacing.inlineGap }}
                          >
                            <span
                              className="shrink-0"
                              style={{ color: colors.primary[500], lineHeight: grammarLineHeights.body }}
                            >
                              •
                            </span>
                            <span
                              className="whitespace-pre-wrap flex-1 font-mono text-sm"
                              style={{ color: colors.semantic.text.primary, lineHeight: grammarLineHeights.body }}
                            >
                              {renderInlineMarkdown(line)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}

                {structuredExplanation.recognitionTip.length > 0 && (
                  <>
                    {showExplanationDividerBefore(3) ? (
                      <div className="border-t" style={{ borderColor: explanationDividerColor }} aria-hidden="true" />
                    ) : null}
                    <div style={{ ...explanationSectionStyle, ...whiteSectionBg }}>
                      <h2 className="text-lg font-semibold" style={{ color: colors.semantic.text.secondary, lineHeight: grammarLineHeights.heading }}>
                        {sectionLabels.recognitionTip}
                      </h2>
                      <ul style={secondaryListStyle}>
                        {structuredExplanation.recognitionTip.map((point, index) => (
                          <li
                            key={index}
                            className="flex items-start"
                            style={{ gap: grammarSectionSpacing.inlineGap }}
                          >
                            <span
                              className="shrink-0"
                              style={{ color: colors.primary[500], lineHeight: grammarLineHeights.body }}
                            >
                              •
                            </span>
                            <span
                              className="whitespace-pre-wrap flex-1"
                              style={{ color: colors.semantic.text.primary, lineHeight: grammarLineHeights.body }}
                            >
                              {renderInlineMarkdown(point)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}
              </div>
            </section>
          )}

          {!hasStructuredSections && rulePoints.length > 0 && (
            <section>
              <div
                className="p-4 rounded-lg border space-y-4"
                style={{
                  backgroundColor: colors.primary[50],
                  borderColor: colors.primary[100],
                }}
              >
                <div className="space-y-2">
                  <h2 className="text-lg font-semibold" style={{ color: colors.semantic.text.secondary }}>
                    {sectionLabels.ruleDescription}
                  </h2>
                  <ul className="space-y-2">
                    {rulePoints.map((point, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="mt-1" style={{ color: colors.primary[500] }}>•</span>
                        <span
                          className="leading-relaxed whitespace-pre-wrap flex-1"
                          style={{ color: colors.semantic.text.primary }}
                        >
                          {renderInlineMarkdown(point)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>
          )}

          {/* 例句部分 */}
          {examples.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-3" style={{ color: colors.semantic.text.secondary }}>
                {sectionLabels.examples}
              </h2>
              <div className="space-y-4">
                {examples.map((example, index) => (
                  <div 
                    key={index}
                    className="p-4 rounded-lg border"
                    style={{ 
                      backgroundColor: colors.semantic.bg.primary,
                      borderColor: colors.gray[200]
                    }}
                  >
                    {/* 句子部分 */}
                    <div className="flex items-start gap-2 mb-2">
                      <div className="text-lg font-medium flex-1" style={{ color: colors.semantic.text.primary }}>
                        {example.sentence}
                      </div>
                      {/* 🔧 朗读图标按钮 */}
                      <button
                        onClick={() => handleSpeakSentence(example.sentence, index)}
                        className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors flex-shrink-0"
                        aria-label={speakingSentenceIndex === index ? '停止朗读' : '朗读句子'}
                        title={speakingSentenceIndex === index ? '停止朗读' : '朗读句子'}
                      >
                        {speakingSentenceIndex === index ? (
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
                    {/* 来源部分 */}
                    {(example.text_id || example.source) && (
                      <div className="flex items-center gap-1 mb-2">
                        <button
                          type="button"
                          onClick={() => {
                            if (example.text_id) {
                              const url = `${window.location.origin}${window.location.pathname}?page=article&articleId=${example.text_id}${example.sentence_id ? `&sentenceId=${example.sentence_id}` : ''}`
                              window.open(url, '_blank')
                            }
                          }}
                          className="flex items-center gap-1 text-xs font-medium hover:underline disabled:opacity-50"
                          style={{ 
                            color: colors.primary[600],
                            fontSize: '0.583rem'
                          }}
                          disabled={!example.text_id}
                        >
                          <span>{t('来源:')} {example.source || t('原文')}</span>
                          <svg
                            className="w-3 h-3"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                            />
                          </svg>
                        </button>
                      </div>
                    )}
                    {/* 解释部分 */}
                    {example.explanation && (
                      <div className="leading-relaxed whitespace-pre-wrap mt-2 pt-2 border-t" style={{ 
                        color: colors.semantic.text.secondary,
                        borderColor: colors.gray[200]
                      }}>
                        {renderInlineMarkdown(parseExplanation(example.explanation))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </BaseCard>
    </div>
  )
}

export default GrammarDetailCard

