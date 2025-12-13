import { useState, useMemo, useEffect, useCallback } from 'react'
import { BaseCard } from '../../base'
import { colors } from '../../../design-tokens'
import { useUIText } from '../../../i18n/useUIText'
import { apiService } from '../../../services/api'
import { useLanguage, languageNameToCode, languageCodeToBCP47 } from '../../../contexts/LanguageContext'

// 解析和格式化解释文本
const parseExplanation = (text) => {
  if (!text) return ''
  
  let cleanText = text
  
  // 1. 处理字典格式的字符串（如 "{'explanation': '...'}" 或 '{"explanation": "..."}'）
  if (text.includes("'explanation'") || text.includes('"explanation"')) {
    try {
      const jsonMatch = text.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        const jsonStr = jsonMatch[0]
        try {
          const parsed = JSON.parse(jsonStr)
          cleanText = parsed.explanation || parsed.definition || text
        } catch (e) {
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
            } catch (e2) {
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
  cleanText = cleanText.replace(/\\n/g, '\n')
  cleanText = cleanText.replace(/\n{3,}/g, '\n\n')
  cleanText = cleanText.trim()
  
  return cleanText
}

// 从 explanation 中尝试分离“释义”和“语法说明”段落
const extractSections = (rawExplanation = '') => {
  const text = parseExplanation(rawExplanation)
  if (!text) return { definitionText: '', grammarText: '' }

  // 尝试匹配中英文小标题
  const defLabels = ['释义', '定义', 'definition', 'definitions']
  const grammarLabels = ['语法说明', '语法', 'grammar', 'grammar notes', 'grammar explanation']

  const toRegex = (labels) => labels.map((l) => l.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')
  const defRegex = new RegExp(`(?:${toRegex(defLabels)})[:：]?`, 'i')
  const grammarRegex = new RegExp(`(?:${toRegex(grammarLabels)})[:：]?`, 'i')

  // 如果同时存在两个小标题，按顺序截取
  const combinedRegex = new RegExp(
    `(?:${toRegex(defLabels)})[:：]?\\s*([\\s\\S]*?)(?=${toRegex(grammarLabels)}[:：]?|$)`,
    'i'
  )
  const defMatch = text.match(combinedRegex)
  const grammarMatch = text.match(new RegExp(`(?:${toRegex(grammarLabels)})[:：]?\\s*([\\s\\S]*)`, 'i'))

  const definitionText = defMatch?.[1]?.trim() || text // 若未提取到释义，则全部作为释义
  const grammarText = grammarMatch?.[1]?.trim() || ''

  return { definitionText, grammarText }
}

const VocabDetailCard = ({
  vocab,
  onPrevious,
  onNext,
  onBack,
  currentIndex,
  totalCount,
  loading = false,
}) => {
  const t = useUIText()
  const { selectedLanguage } = useLanguage() // 🔧 获取全局语言状态
  const [vocabWithDetails, setVocabWithDetails] = useState(vocab)
  const [articleTitles, setArticleTitles] = useState({}) // text_id -> title 映射

  // 加载完整的 vocab 详情（包含 examples）
  useEffect(() => {
    if (vocab && (!vocab.examples || !Array.isArray(vocab.examples) || vocab.examples.length === 0)) {
      const vocabId = vocab.vocab_id
      if (vocabId) {
        apiService.getVocabById(vocabId)
          .then(response => {
            const detailData = response?.data?.data || response?.data || response
            if (detailData) {
              setVocabWithDetails({ ...vocab, ...detailData })
            } else {
              setVocabWithDetails(vocab)
            }
          })
          .catch(error => {
            console.warn('⚠️ [VocabDetailCard] Failed to load vocab detail:', error)
            setVocabWithDetails(vocab)
          })
      } else {
        setVocabWithDetails(vocab)
      }
    } else {
      setVocabWithDetails(vocab)
    }
  }, [vocab])

  // 为每个例句加载文章标题
  useEffect(() => {
    const examples = vocabWithDetails?.examples || []
    if (examples.length === 0) return

    const textIdsToLoad = examples
      .map(ex => ex.text_id || ex.article_id)
      .filter(id => id && !articleTitles[id]) // 只加载还没有缓存的

    if (textIdsToLoad.length === 0) return

    // 批量加载文章标题
    Promise.all(
      textIdsToLoad.map(textId =>
        apiService.getArticleById(textId)
          .then(response => {
            const articleData = response?.data?.data || response?.data || response
            return { textId, title: articleData?.text_title || articleData?.title || null }
          })
          .catch(error => {
            console.warn(`⚠️ [VocabDetailCard] Failed to load article ${textId}:`, error)
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
  }, [vocabWithDetails?.examples, articleTitles])

  const vocabBody = vocabWithDetails?.vocab_body || ''
  // 提取释义与语法说明文本（如果能拆分则拆分，否则释义包含全部）
  const { definitionText, grammarText } = extractSections(vocabWithDetails?.explanation || '')
  const explanation = parseExplanation(vocabWithDetails?.explanation || '')
  
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
      console.warn('⚠️ [VocabDetailCard] 没有可用的语音')
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
      console.warn(`⚠️ [VocabDetailCard] 未找到 ${targetLang} 语音，使用默认语音: ${voice.name}`)
    }
    
    console.log('🔊 [VocabDetailCard] 选择的语音:', {
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
      console.log('🔊 [VocabDetailCard] 所有可用的德语语音:', germanVoices.map(v => ({
        name: v.name,
        lang: v.lang,
        isMultilingual: v.name.toLowerCase().includes('multilingual')
      })))
      
      console.log('🔊 [VocabDetailCard] 朗读设置:', {
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
        console.log('🔊 [VocabDetailCard] 使用语音:', validVoice.name, validVoice.lang)
        // 🔧 再次确认 voice 设置成功
        console.log('🔊 [VocabDetailCard] utterance.voice 确认:', utterance.voice?.name, utterance.voice?.lang)
        
        // 🔧 如果使用的是多语言语音，添加警告
        if (validVoice.name.toLowerCase().includes('multilingual')) {
          console.warn('⚠️ [VocabDetailCard] 警告：使用的是多语言语音，可能会根据文本内容自动检测语言')
        }
      } else {
        console.warn('⚠️ [VocabDetailCard] 未找到有效语音，使用浏览器默认语音')
      }
      
      utterance.rate = 0.9
      utterance.pitch = 1.0
      utterance.volume = 1.0
      
      utterance.onstart = () => {
        console.log('🔊 [VocabDetailCard] onStart - 实际使用的语音:', {
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
          console.log('🔊 [VocabDetailCard] 朗读被中断（正常情况）')
          if (onEnd) onEnd()
          return
        }
        console.error('❌ [VocabDetailCard] 朗读错误:', event.error)
        if (onEnd) onEnd()
      }
      
      window.speechSynthesis.speak(utterance)
    }
  }, [selectedLanguage, getVoiceForLanguage]) // 🔧 确保当 selectedLanguage 改变时，函数会重新创建
  
  const handleSpeakVocab = () => {
    if (!vocabBody) return
    
    // 如果正在朗读，停止朗读
    if (isSpeakingVocab && typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel()
      setIsSpeakingVocab(false)
      return
    }
    
    // 🔧 开始朗读，使用全局语言状态
    handleSpeak(
      vocabBody,
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
  
  // 解析释义，尝试提取多个定义
  const definitions = useMemo(() => {
    const base = definitionText || explanation
    if (!base) return []
    
    // 尝试按数字编号分割（如 "1. xxx 2. yyy"）
    const numberedMatch = base.match(/(\d+)[\.、]\s*([^\d]+?)(?=\s*\d+[\.、]|$)/g)
    if (numberedMatch && numberedMatch.length > 1) {
      return numberedMatch.map(item => {
        const cleaned = item.replace(/^\d+[\.、]\s*/, '').trim()
        return cleaned
      })
    }
    
    // 如果没有编号，尝试按换行分割
    const lines = base.split('\n').filter(line => line.trim())
    if (lines.length > 1) {
      return lines.map(line => line.trim())
    }
    
    // 如果只有一行，返回整个解释
    return [base]
  }, [definitionText, explanation])

  // 解析语法说明，提取要点
  const grammarPoints = useMemo(() => {
    const rawGrammar = grammarText || vocabWithDetails?.grammar_notes || ''
    if (!rawGrammar) return []
    const parsed = parseExplanation(rawGrammar)
    const lines = parsed.split('\n').filter(line => line.trim())
    return lines.map(line => line.trim())
  }, [grammarText, vocabWithDetails])

  // 提取例句
  const examples = useMemo(() => {
    if (!vocabWithDetails?.examples || !Array.isArray(vocabWithDetails.examples)) {
      return []
    }
    return vocabWithDetails.examples
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
  }, [vocabWithDetails, articleTitles])

  // 提取词性
  const partOfSpeech = vocabWithDetails?.part_of_speech || vocabWithDetails?.pos || ''

  if (loading) {
    return (
      <BaseCard padding="lg" className="w-full max-w-4xl mx-auto">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4" style={{ borderColor: colors.primary[500] }}></div>
          <p className="text-gray-600">{t('加载中...')}</p>
        </div>
      </BaseCard>
    )
  }

  if (!vocabWithDetails) {
    return (
      <BaseCard padding="lg" className="w-full max-w-4xl mx-auto">
        <div className="text-center py-8">
          <p className="text-gray-600">{t('未找到词汇数据')}</p>
        </div>
      </BaseCard>
    )
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <BaseCard
        padding="lg"
        className="w-full relative"
        style={{
          '--card-bg': colors.semantic.bg.primary,
          '--card-border': colors.semantic.border.default,
        }}
      >
        {/* 左上角返回按钮 - 绝对定位在卡片左上角 */}
        {onBack && (
          <button
            onClick={onBack}
            className="absolute top-6 left-6 z-10 px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            aria-label="返回"
          >
            {t('返回')}
          </button>
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
          {/* 词汇标题区域 */}
          <div className="flex flex-col items-center gap-2">
            <div className="flex items-center gap-3">
              <h1 className="text-4xl font-bold text-center" style={{ color: colors.semantic.text.primary }}>
                {vocabBody}
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
            {partOfSpeech && (
              <span className="text-sm" style={{ color: colors.semantic.text.secondary }}>
                {partOfSpeech}
              </span>
            )}
          </div>

        {/* 释义 + 语法说明 合并为单卡片，使用 Primary-50 背景 */}
        {(definitions.length > 0 || grammarPoints.length > 0) && (
          <section>
            <div
              className="p-4 rounded-lg border space-y-4"
              style={{
                backgroundColor: colors.primary[50],
                borderColor: colors.primary[100],
              }}
            >
              {definitions.length > 0 && (
                <div className="space-y-3">
                  <h2 className="text-lg font-semibold" style={{ color: colors.semantic.text.secondary }}>
                    释义
                  </h2>
                  {definitions.map((def, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <span className="font-medium min-w-[24px]" style={{ color: colors.semantic.text.secondary }}>
                        {index + 1}.
                      </span>
                      <div
                        className="leading-relaxed whitespace-pre-wrap flex-1"
                        style={{ color: colors.semantic.text.primary }}
                      >
                        {def}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {grammarPoints.length > 0 && (
                <div className="space-y-2">
                  <h2 className="text-lg font-semibold" style={{ color: colors.semantic.text.secondary }}>
                    语法说明
                  </h2>
                  <ul className="space-y-2">
                    {grammarPoints.map((point, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="mt-1" style={{ color: colors.primary[500] }}>•</span>
                        <span
                          className="leading-relaxed whitespace-pre-wrap flex-1"
                          style={{ color: colors.semantic.text.primary }}
                        >
                          {point}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </section>
        )}

        {/* 例句部分 - 小标题分离，每个例句独立卡片 */}
        {examples.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3" style={{ color: colors.semantic.text.secondary }}>
              例句
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
                  {/* 来源部分 - 绿色文字和链接图标 */}
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
                          fontSize: '0.583rem' // text-sm的2/3: 0.875rem * 2/3 ≈ 0.583rem (约9.3px)
                        }}
                        disabled={!example.text_id}
                      >
                        <span>来源: {example.source || t('原文')}</span>
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
                      {parseExplanation(example.explanation)}
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

export default VocabDetailCard
