import { useState, useMemo, useEffect, useCallback } from 'react'
import { BaseCard, BackButton } from '../../base'
import { colors, componentTokens } from '../../../design-tokens'
import { useUIText } from '../../../i18n/useUIText'
import { apiService } from '../../../services/api'
import { useLanguage, languageNameToCode, languageCodeToBCP47 } from '../../../contexts/LanguageContext'

// 解析和格式化解释文本（与 VocabNotationCard 保持一致）
const parseExplanation = (text) => {
  if (!text) return ''
  
  let cleanText = String(text).trim()
  
  // 🔧 首先检查是否是 JSON 格式（包含大括号和 explanation 键）
  if (cleanText.startsWith('{') && cleanText.includes('explanation')) {
    // 方法1：尝试直接解析为 JSON（最标准的方式）
    try {
      const parsed = JSON.parse(cleanText)
      if (typeof parsed === 'object' && parsed !== null) {
        const extracted = parsed.explanation || parsed.definition || parsed.context_explanation
        if (extracted && extracted !== cleanText) {
          return String(extracted).trim()
        }
      }
    } catch (e) {
      // JSON.parse 失败，继续其他方法
    }
    
    // 方法2：使用正则表达式提取 explanation 字段的值（支持多行和实际换行符）
    // 🔧 改进：使用更智能的正则，能够处理被截断的 JSON 字符串
    // 首先尝试匹配完整的 JSON（有闭合引号和括号）
    let explanationMatch = cleanText.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)['"]\s*[,}]/s)
    
    // 如果失败，尝试匹配到字符串末尾（处理被截断的 JSON，比如没有闭合引号）
    if (!explanationMatch) {
      // 匹配 "explanation": "..." 到字符串末尾或遇到闭合引号
      explanationMatch = cleanText.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)(?:['"]\s*[,}]|$)/s)
    }
    
    // 如果还是失败，尝试更宽松的匹配：从 "explanation": " 开始到字符串末尾
    if (!explanationMatch) {
      const keyPattern = /['"]explanation['"]\s*:\s*['"]/
      const keyMatch = cleanText.match(keyPattern)
      if (keyMatch) {
        const startPos = keyMatch.index + keyMatch[0].length
        const value = cleanText.substring(startPos)
        // 如果找到了值，直接使用（可能是被截断的）
        if (value.length > 0) {
          cleanText = value
            .replace(/\\n/g, '\n')
            .replace(/\\'/g, "'")
            .replace(/\\"/g, '"')
            .replace(/\\t/g, '\t')
            .replace(/\\r/g, '\r')
          // 移除末尾可能存在的引号、逗号、大括号等
          cleanText = cleanText.replace(/['"]\s*[,}]\s*$/, '').trim()
          return cleanText.trim()
        }
      }
    }
    
    if (explanationMatch && explanationMatch[1]) {
      // 直接提取 explanation 的值
      cleanText = explanationMatch[1]
        .replace(/\\n/g, '\n')  // 先处理已转义的换行符
        .replace(/\\'/g, "'")   // 处理转义的单引号
        .replace(/\\"/g, '"')   // 处理转义的双引号
        .replace(/\\t/g, '\t')  // 处理转义的制表符
        .replace(/\\r/g, '\r')  // 处理转义的回车符
      return cleanText.trim()
    }
    
    // 方法3：手动解析（处理包含实际换行符或特殊字符的情况，包括被截断的 JSON）
    try {
      // 🔧 改进：不要求完整的 JSON 对象，直接在整个字符串中查找
      const keyPattern = /['"]explanation['"]\s*:\s*/
      const keyMatch = cleanText.match(keyPattern)
      if (keyMatch) {
        const startPos = keyMatch.index + keyMatch[0].length
        const remaining = cleanText.substring(startPos).trim()
        // 检查是否是字符串值（以引号开始）
        if (remaining[0] === '"' || remaining[0] === "'") {
          const quote = remaining[0]
          let value = ''
          let i = 1
          let escaped = false
          // 🔧 改进：如果字符串被截断了（没有闭合引号），也提取所有内容
          while (i < remaining.length) {
            if (escaped) {
              value += remaining[i]
              escaped = false
              i++
            } else if (remaining[i] === '\\') {
              escaped = true
              i++
            } else if (remaining[i] === quote) {
              // 找到匹配的结束引号
              break
            } else {
              value += remaining[i]
              i++
            }
          }
          // 🔧 如果找到了值（即使没有闭合引号），处理转义字符
          if (value.length > 0) {
            cleanText = value
              .replace(/\\n/g, '\n')
              .replace(/\\'/g, "'")
              .replace(/\\"/g, '"')
              .replace(/\\t/g, '\t')
              .replace(/\\r/g, '\r')
            // 移除末尾可能存在的引号、逗号、大括号等
            cleanText = cleanText.replace(/['"]\s*[,}]\s*$/, '').trim()
            return cleanText.trim()
          }
        }
      }
    } catch (e2) {
      // 手动解析也失败，继续其他方法
    }
  }
  
  // 2. 处理代码块格式（```json ... ```）
  if (cleanText.includes('```json') && cleanText.includes('```')) {
    try {
      const jsonMatch = cleanText.match(/```json\n?([\s\S]*?)\n?```/)
      if (jsonMatch) {
        const jsonStr = jsonMatch[1].trim()
        const parsed = JSON.parse(jsonStr)
        cleanText = parsed.explanation || parsed.definition || parsed.context_explanation || cleanText
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
  
  // 🔧 如果清理后的文本仍然包含明显的 JSON 结构，尝试最后一次解析
  if (cleanText.startsWith('{') && cleanText.includes('explanation')) {
    try {
      const parsed = JSON.parse(cleanText)
      if (typeof parsed === 'object' && parsed !== null) {
        cleanText = parsed.explanation || parsed.definition || parsed.context_explanation || cleanText
      }
    } catch (e) {
      // 最后尝试：将单引号替换为双引号
      try {
        const normalized = cleanText.replace(/'/g, '"')
        const parsed = JSON.parse(normalized)
        if (typeof parsed === 'object' && parsed !== null) {
          cleanText = parsed.explanation || parsed.definition || parsed.context_explanation || cleanText
        }
      } catch (e2) {
        // 解析失败，使用当前文本
      }
    }
  }
  
  return cleanText
}

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

const normalizeExplanationLayout = (rawText = '') => {
  if (!rawText) return ''

  const text = String(rawText)
    .replace(/\r\n/g, '\n')
    .replace(/\u00a0/g, ' ')

  const normalizedLines = text.split('\n').map((line) => {
    const trimmed = line.trim()
    if (!trimmed) return ''

    return line
      .replace(/^[ \t]{2,}/, '')
      .replace(/^\((?:if applicable)\)\s*collocations\s*:/i, 'Collocations:')
      .replace(/^\((?:if applicable)\)\s*grammar notes?\s*:/i, 'Grammar notes:')
      .replace(/^\((?:if applicable)\)\s*rare sense\s*:/i, 'Rare sense:')
      .replace(/^（如适用）\s*搭配\s*：?/, '搭配：')
      .replace(/^（如适用）\s*语法说明\s*：?/, '语法说明：')
      .replace(/^（如有）\s*少见义\s*：?/, '少见义：')
      .replace(/^grammar note\s*:/i, 'Grammar notes:')
      .replace(/^grammar notes\s*:/i, 'Grammar notes:')
      .replace(/^collocations?\s*:/i, 'Collocations:')
      .replace(/^rare sense\s*:/i, 'Rare sense:')
      .replace(/^[ \t]+(-\s+)/, '$1')
  })

  return normalizedLines
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

const isSectionHeading = (line, labels) => {
  const normalized = String(line || '')
    .trim()
    .replace(/^\*\*/, '')
    .replace(/\*\*$/, '')
    .replace(/[:：]\s*$/, '')
    .trim()
    .toLowerCase()

  return labels.some((label) => normalized === String(label).trim().toLowerCase())
}

// 从 explanation 中尝试分离“释义 / 少见义 / 搭配 / 语法说明”段落
const extractSections = (rawExplanation = '') => {
  const text = normalizeExplanationLayout(parseExplanation(rawExplanation))
  if (!text) {
    return { definitionText: '', rareSenseText: '', collocationsText: '', grammarText: '' }
  }

  const defLabels = ['释义', '定义', 'definition', 'definitions']
  const rareSenseLabels = ['rare sense', 'rare senses', '少见义']
  const collocationLabels = ['collocations', 'collocation', '搭配']
  const grammarLabels = ['grammar explanation', 'grammar notes', 'grammar note', '语法说明', 'definition note', 'grammar']

  const sections = {
    definition: [],
    rareSense: [],
    collocations: [],
    grammar: [],
  }

  let currentSection = 'definition'
  text.split('\n').forEach((line) => {
    const trimmed = line.trim()
    if (!trimmed) {
      if (sections[currentSection].length > 0) {
        sections[currentSection].push('')
      }
      return
    }

    if (isSectionHeading(trimmed, defLabels)) {
      currentSection = 'definition'
      return
    }
    if (isSectionHeading(trimmed, rareSenseLabels)) {
      currentSection = 'rareSense'
      return
    }
    if (isSectionHeading(trimmed, collocationLabels)) {
      currentSection = 'collocations'
      return
    }
    if (isSectionHeading(trimmed, grammarLabels)) {
      currentSection = 'grammar'
      return
    }

    sections[currentSection].push(trimmed)
  })

  const joinSection = (lines) => lines.join('\n').replace(/\n{3,}/g, '\n\n').trim()

  return {
    definitionText: joinSection(sections.definition),
    rareSenseText: joinSection(sections.rareSense),
    collocationsText: joinSection(sections.collocations),
    grammarText: joinSection(sections.grammar),
  }
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
  // 提取释义 / 搭配 / 语法说明文本（如果能拆分则拆分，否则释义包含全部）
  const { definitionText, rareSenseText, collocationsText, grammarText } = extractSections(vocabWithDetails?.explanation || '')
  const explanation = normalizeExplanationLayout(parseExplanation(vocabWithDetails?.explanation || ''))
  
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

  const collocationPoints = useMemo(() => {
    if (!collocationsText) return []
    return normalizeExplanationLayout(collocationsText)
      .split('\n')
      .filter(line => line.trim())
      .map(line => line.trim())
      .map(line => line.replace(/^[-*•]\s*/, ''))
      .filter(Boolean)
  }, [collocationsText])

  const rareSensePoints = useMemo(() => {
    if (!rareSenseText) return []
    return normalizeExplanationLayout(rareSenseText)
      .split('\n')
      .filter(line => line.trim())
      .map(line => line.trim())
      .filter(Boolean)
  }, [rareSenseText])

  // 解析语法说明，提取要点
  const grammarPoints = useMemo(() => {
    const rawGrammar = normalizeExplanationLayout(grammarText || vocabWithDetails?.grammar_notes || '')
    if (!rawGrammar) return []
    const parsed = parseExplanation(rawGrammar)
    const lines = parsed.split('\n').filter(line => line.trim())
    return lines
      .map(line => line.trim())
      .map(line => line.replace(/^[-*•]\s*/, ''))
      .filter(line => line && !/^note:\*{0,2}$/i.test(line))
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
      <div className="w-full max-w-4xl mx-auto" style={{ backgroundColor: 'white' }}>
        <BaseCard padding="lg" className="w-full" style={{ backgroundColor: 'white' }}>
          <div className="text-center py-8" style={{ backgroundColor: 'white' }}>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4" style={{ borderColor: colors.primary[500] }}></div>
            <p className="text-gray-600">{t('加载中...')}</p>
          </div>
        </BaseCard>
      </div>
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
        {/* 左上角返回按钮 - 绝对定位在卡片左上角 */}
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
          {/* 词汇标题区域 */}
          <div className="flex flex-col items-center gap-2">
            {/* 预留左右空间，避免与左上返回/右上翻页控件重叠 */}
            <div className="w-full px-20 flex justify-center">
              {/* 标题 + 朗读按钮作为一个居中内容块，朗读按钮紧贴标题右侧 */}
              <div className="inline-flex items-center gap-2 max-w-full">
              <h1 
                className="text-center truncate"
                style={{
                  fontSize: componentTokens.grammarVocabTitle.fontSize,
                  fontWeight: componentTokens.grammarVocabTitle.fontWeight,
                  color: componentTokens.grammarVocabTitle.color,
                  lineHeight: componentTokens.grammarVocabTitle.lineHeight,
                  textAlign: componentTokens.grammarVocabTitle.textAlign,
                  maxWidth: '100%',
                }}
              >
                {vocabBody}
              </h1>
              {/* 🔧 朗读图标按钮 */}
              <button
                onClick={handleSpeakVocab}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors shrink-0"
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
            </div>
            {partOfSpeech && (
              <span className="text-sm" style={{ color: colors.semantic.text.secondary }}>
                {partOfSpeech}
              </span>
            )}
          </div>

        {/* 释义 + 搭配 + 语法说明 合并为单卡片，使用 Primary-50 背景 */}
        {(definitions.length > 0 || rareSensePoints.length > 0 || collocationPoints.length > 0 || grammarPoints.length > 0) && (
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
                    {t('释义')}
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
                        {renderInlineMarkdown(def)}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {rareSensePoints.length > 0 && (
                <div className="space-y-2">
                  <h2 className="text-lg font-semibold" style={{ color: colors.semantic.text.secondary }}>
                    {t('少见义')}
                  </h2>
                  <div className="space-y-2">
                    {rareSensePoints.map((point, index) => (
                      <div
                        key={index}
                        className="leading-relaxed whitespace-pre-wrap"
                        style={{ color: colors.semantic.text.primary }}
                      >
                        {renderInlineMarkdown(point)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {collocationPoints.length > 0 && (
                <div className="space-y-2">
                  <h2 className="text-lg font-semibold" style={{ color: colors.semantic.text.secondary }}>
                    {t('搭配')}
                  </h2>
                  <ul className="space-y-2">
                    {collocationPoints.map((point, index) => (
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
              )}

              {grammarPoints.length > 0 && (
                <div className="space-y-2">
                  <h2 className="text-lg font-semibold" style={{ color: colors.semantic.text.secondary }}>
                    {t('语法说明')}
                  </h2>
                  <ul className="space-y-2">
                    {grammarPoints.map((point, index) => (
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
              )}
            </div>
          </section>
        )}

        {/* 例句部分 - 小标题分离，每个例句独立卡片 */}
        {examples.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3" style={{ color: colors.semantic.text.secondary }}>
              {t('例句')}
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

export default VocabDetailCard
