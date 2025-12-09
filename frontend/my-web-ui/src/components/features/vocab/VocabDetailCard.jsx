import { useState, useMemo, useEffect } from 'react'
import { BaseCard } from '../../base'
import { colors } from '../../../design-tokens'
import { useUIText } from '../../../i18n/useUIText'
import { apiService } from '../../../services/api'

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
  loading = false,
}) => {
  const t = useUIText()
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
    <BaseCard
      padding="lg"
      className="w-full max-w-4xl mx-auto"
      style={{
        '--card-bg': colors.semantic.bg.primary,
        '--card-border': colors.semantic.border.default,
      }}
    >
      <div className="space-y-6">
        {/* 词汇标题区域 - 包含导航按钮（只有图标） */}
        <div className="flex items-center justify-center gap-6">
          {/* 上一个按钮 - 只有图标 */}
          {onPrevious && (
            <button
              onClick={onPrevious}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="上一个"
              style={{
                color: colors.primary[500],
              }}
            >
              <svg
                className="w-6 h-6"
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

          {/* 词汇和词性 */}
          <div className="flex flex-col items-center gap-2 flex-1">
            <h1 className="text-4xl font-bold text-center" style={{ color: colors.semantic.text.primary }}>
              {vocabBody}
            </h1>
            {partOfSpeech && (
              <span className="text-sm" style={{ color: colors.semantic.text.secondary }}>
                {partOfSpeech}
              </span>
            )}
          </div>

          {/* 下一个按钮 - 只有图标 */}
          {onNext && (
            <button
              onClick={onNext}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="下一个"
              style={{
                color: colors.primary[500],
              }}
            >
              <svg
                className="w-6 h-6"
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
                  <div className="text-lg mb-2 font-medium" style={{ color: colors.semantic.text.primary }}>
                    {example.sentence}
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

        {/* 底部导航栏 - 左边"< 上一个"，中间"来源: qa"，右边"下一个 >" */}
        <div className="flex items-center justify-between pt-4 border-t" style={{ borderColor: colors.gray[200] }}>
          {/* 左边：上一个 */}
          <div className="flex items-center gap-2">
            {onPrevious && (
              <button
                onClick={onPrevious}
                className="flex items-center gap-1 px-3 py-1 text-sm hover:bg-gray-100 rounded-lg transition-colors"
                style={{ color: colors.semantic.text.secondary }}
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
                上一个
              </button>
            )}
          </div>
          
          {/* 中间：来源 */}
          {vocabWithDetails?.source && (
            <div className="text-sm" style={{ color: colors.semantic.text.secondary }}>
              来源: <span className="font-medium">{vocabWithDetails.source}</span>
            </div>
          )}

          {/* 右边：下一个 */}
          <div className="flex items-center gap-2">
            {onNext && (
              <button
                onClick={onNext}
                className="flex items-center gap-1 px-3 py-1 text-sm hover:bg-gray-100 rounded-lg transition-colors"
                style={{ color: colors.semantic.text.secondary }}
              >
                下一个
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
        </div>
      </div>
    </BaseCard>
  )
}

export default VocabDetailCard
