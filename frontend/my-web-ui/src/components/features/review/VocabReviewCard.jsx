import { useState, useMemo, useEffect, useCallback, useRef } from 'react'
import { BaseButton, BaseCard, BaseBadge } from '../../base'
import { colors, componentTokens } from '../../../design-tokens'
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
        } catch {
          // 如果不是标准 JSON，尝试处理 Python 字典格式（单引号）
          const explanationMatch = text.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)['"]\s*[,}]/s)
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
            } catch {
              cleanText = text
            }
          }
        }
      }
    } catch {
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
    } catch {
      // 解析失败，继续使用 cleanText
    }
  }
  
  // 3. 清理多余的转义字符和格式化
  cleanText = cleanText.replace(/\\n/g, '\n')
  cleanText = cleanText.replace(/\n{3,}/g, '\n\n')
  cleanText = cleanText.trim()
  
  return cleanText
}

const VocabReviewCard = ({
  // Vocab data
  vocab,
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
  const [vocabWithExamples, setVocabWithExamples] = useState(vocab)
  const latestVocabIdRef = useRef(vocab?.vocab_id)

  // 🔧 加载完整的 vocab 详情（包含 examples）- 优化：如果已有完整数据则跳过请求
  useEffect(() => {
    latestVocabIdRef.current = vocab?.vocab_id
    setShowDefinitions(false)
    setCurrentExampleIndex(0)
    
    // 🔧 如果传入的 vocab 已经包含 examples，直接使用，无需请求
    if (vocab && vocab.examples && Array.isArray(vocab.examples) && vocab.examples.length > 0) {
      setVocabWithExamples(vocab)
      return
    }
    
    // 🔧 如果没有 examples，才请求详情（但通常预加载已经完成）
    if (vocab && (!vocab.examples || !Array.isArray(vocab.examples) || vocab.examples.length === 0)) {
      const vocabId = vocab.vocab_id
      if (vocabId) {
        const requestedVocabId = vocabId
        apiService.getVocabById(vocabId)
          .then(response => {
            // 🔧 防止异步请求晚到覆盖了“下一个 vocab”的显示
            if (latestVocabIdRef.current !== requestedVocabId) {
              return
            }
            const detailData = response?.data?.data || response?.data || response
            if (detailData && detailData.examples && Array.isArray(detailData.examples) && detailData.examples.length > 0) {
              setVocabWithExamples({ ...vocab, ...detailData })
            } else {
              setVocabWithExamples(vocab)
            }
          })
          .catch(error => {
            // 🔧 同样丢弃过期失败回调
            if (latestVocabIdRef.current !== vocabId) {
              return
            }
            console.warn('⚠️ [VocabReviewCard] Failed to load vocab detail:', error)
            setVocabWithExamples(vocab)
          })
      } else {
        setVocabWithExamples(vocab)
      }
    } else {
      setVocabWithExamples(vocab)
    }
  }, [vocab])

  // 提取例句和例句解释
  const exampleData = useMemo(() => {
    const currentVocab = vocabWithExamples || vocab
    if (!currentVocab?.examples || !Array.isArray(currentVocab.examples)) {
      return []
    }
    return currentVocab.examples
      .map(ex => ({
        sentence: ex.original_sentence,
        explanation: ex.context_explanation || ex.explanation_context || ex.explanation || null
      }))
      .filter(ex => ex.sentence)
  }, [vocabWithExamples, vocab])
  
  const exampleSentences = exampleData.map(ex => ex.sentence)

  // 获取单词
  const word = vocabWithExamples?.vocab_body || vocab?.vocab_body || ''

  // 获取解释文本
  const explanation = useMemo(() => {
    const currentVocab = vocabWithExamples || vocab
    return parseExplanation(currentVocab?.explanation || '暂无定义')
  }, [vocabWithExamples, vocab])
  
  // 🔧 朗读功能
  const [isSpeakingVocab, setIsSpeakingVocab] = useState(false)
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
      console.warn('⚠️ [VocabReviewCard] 没有可用的语音')
      return null
    }
    
    const targetLang = languageCodeToBCP47(langCode)
    
    // 🔧 优先查找非多语言的、完全匹配的语音（避免多语言语音自动检测语言）
    let voice = availableVoices.find(v => 
      v.lang === targetLang && 
      !v.name.toLowerCase().includes('multilingual')
    )
    
    // 如果找不到非多语言的，再查找完全匹配的（包括多语言）
    if (!voice) {
      voice = availableVoices.find(v => v.lang === targetLang)
    }
    
    // 如果找不到，查找语言代码前缀匹配的（优先非多语言）
    if (!voice) {
      const langPrefix = targetLang.split('-')[0]
      voice = availableVoices.find(v => 
        v.lang && 
        v.lang.startsWith(langPrefix) && 
        !v.name.toLowerCase().includes('multilingual')
      )
    }
    
    // 如果还是找不到，查找任何匹配语言的语音
    if (!voice) {
      const langPrefix = targetLang.split('-')[0]
      voice = availableVoices.find(v => v.lang && v.lang.startsWith(langPrefix))
    }
    
    // 如果还是找不到，使用默认语音（通常是第一个）
    if (!voice && availableVoices.length > 0) {
      voice = availableVoices[0]
      console.warn(`⚠️ [VocabReviewCard] 未找到 ${targetLang} 语音，使用默认语音: ${voice.name}`)
    }
    
    console.log('🔊 [VocabReviewCard] 选择的语音:', {
      name: voice?.name,
      lang: voice?.lang,
      isMultilingual: voice?.name?.toLowerCase().includes('multilingual'),
      allMatchingVoices: availableVoices.filter(v => v.lang === targetLang).map(v => ({
        name: v.name,
        lang: v.lang,
        isMultilingual: v.name.toLowerCase().includes('multilingual')
      }))
    })
    
    return voice || null
  }, [])

  // 🔧 通用朗读函数（使用全局语言状态）
  const handleSpeak = useCallback(async (text, onStart, onEnd) => {
    if (!text) return
    
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      // 🔧 先取消任何正在进行的朗读
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel()
        // 等待一小段时间，确保 cancel 完成
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      
      // 🔧 使用全局语言状态
      const langCode = languageNameToCode(selectedLanguage)
      const targetLang = languageCodeToBCP47(langCode)
      
      // 🔧 确保语音列表已加载（某些浏览器需要触发 getVoices 才能加载）
      let availableVoices = window.speechSynthesis.getVoices()
      if (availableVoices.length === 0) {
        // 如果语音列表为空，等待一下再试
        await new Promise(resolve => setTimeout(resolve, 100))
        availableVoices = window.speechSynthesis.getVoices()
      }
      
      // 🔧 重新验证并获取语音对象（确保使用最新的语音列表）
      let validVoice = null
      const voice = getVoiceForLanguage(langCode)
      if (voice) {
        // 从当前可用的语音列表中查找匹配的语音（通过名称和语言）
        validVoice = availableVoices.find(v => 
          v.name === voice.name && v.lang === voice.lang
        ) || availableVoices.find(v => v.lang === voice.lang)
      }
      
      // 如果找不到匹配的语音，重新获取
      if (!validVoice) {
        validVoice = getVoiceForLanguage(langCode)
      }
      
      // 🔧 如果还是找不到，尝试查找任何德语语音（优先非多语言）
      if (!validVoice && langCode === 'de') {
        validVoice = availableVoices.find(v => 
          v.lang && 
          v.lang.startsWith('de') && 
          !v.name.toLowerCase().includes('multilingual')
        ) || availableVoices.find(v => v.lang && v.lang.startsWith('de'))
      }
      
      // 🔧 显示所有可用的德语语音（用于调试）
      const germanVoices = availableVoices.filter(v => v.lang && v.lang.startsWith('de'))
      console.log('🔊 [VocabReviewCard] 所有可用的德语语音:', germanVoices.map(v => ({
        name: v.name,
        lang: v.lang,
        isMultilingual: v.name.toLowerCase().includes('multilingual')
      })))
      
      console.log('🔊 [VocabReviewCard] 朗读设置:', {
        selectedLanguage,
        langCode,
        targetLang,
        voice: validVoice ? validVoice.name : 'null',
        voiceLang: validVoice ? validVoice.lang : 'null',
        textLength: text.length,
        text: text.substring(0, 50), // 显示文本内容（用于调试）
        availableVoicesCount: availableVoices.length
      })
      
      const utterance = new SpeechSynthesisUtterance(text)
      
      // 🔧 关键：先设置 lang，再设置 voice（某些浏览器需要这个顺序）
      utterance.lang = targetLang
      
      // 🔧 显式设置语音对象（这是关键！）
      if (validVoice) {
        utterance.voice = validVoice
        console.log('🔊 [VocabReviewCard] 使用语音:', validVoice.name, validVoice.lang)
        // 🔧 再次确认 voice 设置成功
        console.log('🔊 [VocabReviewCard] utterance.voice 确认:', utterance.voice?.name, utterance.voice?.lang)
        
        // 🔧 如果使用的是多语言语音，添加警告
        if (validVoice.name.toLowerCase().includes('multilingual')) {
          console.warn('⚠️ [VocabReviewCard] 警告：使用的是多语言语音，可能会根据文本内容自动检测语言')
        }
      } else {
        console.warn('⚠️ [VocabReviewCard] 未找到有效语音，使用浏览器默认语音')
      }
      
      utterance.rate = 0.9
      utterance.pitch = 1.0
      utterance.volume = 1.0
      
      utterance.onstart = () => {
        console.log('🔊 [VocabReviewCard] onStart - 实际使用的语音:', {
          voiceName: utterance.voice?.name,
          voiceLang: utterance.voice?.lang,
          utteranceLang: utterance.lang,
          text: text.substring(0, 50),
          isMultilingual: utterance.voice?.name?.toLowerCase().includes('multilingual')
        })
        if (onStart) onStart()
      }
      
      utterance.onend = () => {
        if (onEnd) onEnd()
      }
      
      utterance.onerror = (event) => {
        // 🔧 interrupted 错误通常是正常的（用户停止或新的朗读取消旧的），不需要记录为错误
        if (event.error === 'interrupted') {
          console.log('🔊 [VocabReviewCard] 朗读被中断（正常情况）')
          if (onEnd) onEnd()
          return
        }
        console.error('❌ [VocabReviewCard] 朗读错误:', event.error)
        if (onEnd) onEnd()
      }
      
      window.speechSynthesis.speak(utterance)
    }
  }, [selectedLanguage, getVoiceForLanguage]) // 🔧 确保当 selectedLanguage 改变时，函数会重新创建
  
  const handleSpeakVocab = () => {
    if (!word) return
    
    // 如果正在朗读，停止朗读
    if (isSpeakingVocab && typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel()
      setIsSpeakingVocab(false)
      return
    }
    
    // 🔧 开始朗读，使用全局语言状态
    handleSpeak(
      word,
      () => setIsSpeakingVocab(true),
      () => setIsSpeakingVocab(false)
    )
  }
  
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

          {/* Word */}
          <div className="flex items-center justify-center gap-3">
            <h1 
              className="text-center break-words"
              style={{
                fontSize: componentTokens.grammarVocabTitle.fontSize,
                fontWeight: componentTokens.grammarVocabTitle.fontWeight,
                color: componentTokens.grammarVocabTitle.color,
                lineHeight: componentTokens.grammarVocabTitle.lineHeight,
                maxWidth: '300px', // 复习卡片：固定最大宽度（卡片详情页面 max-w-4xl=896px 的 1/3 约为 300px）
                textAlign: componentTokens.grammarVocabTitle.textAlign,
                wordWrap: componentTokens.grammarVocabTitle.wordWrap,
                overflowWrap: componentTokens.grammarVocabTitle.overflowWrap,
              }}
            >
              {word}
            </h1>
            {/* 🔧 朗读图标按钮 */}
            <button
              onClick={handleSpeakVocab}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label={isSpeakingVocab ? '停止朗读' : '朗读'}
              title={isSpeakingVocab ? '停止朗读' : '朗读'}
            >
              {isSpeakingVocab ? (
                <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <rect x="9" y="9" width="6" height="6" rx="1" />
                  <circle cx="12" cy="12" r="10" />
                </svg>
              ) : (
                <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  {/* 扬声器锥形 */}
                  <path d="M11 5L6 9H2v6h4l5 4V5z" />
                  {/* 声波线条 */}
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07" />
                </svg>
              )}
            </button>
          </div>

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

export default VocabReviewCard

