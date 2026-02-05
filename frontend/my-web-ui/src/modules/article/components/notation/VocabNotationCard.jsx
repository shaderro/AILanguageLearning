import { useState, useEffect, useRef, useCallback, useLayoutEffect } from 'react'
import { createPortal } from 'react-dom'
import { apiService } from '../../../../services/api'
import { logVocabNotationDebug } from '../../utils/vocabNotationDebug'

const DEFAULT_CARD_WIDTH = 320
// 🔧 放宽卡片高度限制，避免长解释被视觉截断（仍然允许内部滚动）
const DEFAULT_CARD_MAX_HEIGHT = 520
const CARD_MARGIN = 8

// 解析和格式化解释文本
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
      // console.log('⚠️ [parseExplanation] JSON.parse failed, trying regex:', e.message)
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
          console.log('✅ [parseExplanation] Extracted using fallback method, length:', cleanText.length)
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
  
  // 1. 处理字典格式的字符串（如 "{'explanation': '...'}" 或 '{"explanation": "..."}'）
  if (cleanText.includes("'explanation'") || cleanText.includes('"explanation"') || cleanText.includes("'definition'") || cleanText.includes('"definition"')) {
    try {
      // 尝试解析 JSON 格式
      const jsonMatch = cleanText.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        const jsonStr = jsonMatch[0]
        // 先尝试标准 JSON 解析
        try {
          const parsed = JSON.parse(jsonStr)
          cleanText = parsed.explanation || parsed.definition || parsed.context_explanation || cleanText
        } catch (e) {
          // 如果不是标准 JSON，尝试处理 Python 字典格式（单引号）
          // 🔧 使用正则表达式直接提取 explanation 字段的值（支持多行和转义字符）
          const explanationMatch = cleanText.match(/['"]explanation['"]\s*:\s*['"]([\s\S]*?)['"]\s*[,}]/s)
          if (explanationMatch) {
            cleanText = explanationMatch[1]
              .replace(/\\n/g, '\n')  // 处理转义的换行符
              .replace(/\\'/g, "'")   // 处理转义的单引号
              .replace(/\\"/g, '"')   // 处理转义的双引号
              .replace(/\\t/g, '\t')  // 处理转义的制表符
              .replace(/\\r/g, '\r')  // 处理转义的回车符
          } else {
            // 如果正则匹配失败，尝试将单引号替换为双引号（简单处理）
            const normalized = jsonStr.replace(/'/g, '"')
            try {
              const parsed = JSON.parse(normalized)
              cleanText = parsed.explanation || parsed.definition || parsed.context_explanation || cleanText
            } catch (e2) {
              // 如果还是失败，尝试使用 ast.literal_eval 的等价逻辑（手动解析）
              // 查找 explanation 键后面的值
              const keyPattern = /['"]explanation['"]\s*:\s*/
              const keyMatch = jsonStr.match(keyPattern)
              if (keyMatch) {
                const startPos = keyMatch.index + keyMatch[0].length
                const remaining = jsonStr.substring(startPos).trim()
                // 检查是否是字符串值
                if (remaining[0] === '"' || remaining[0] === "'") {
                  const quote = remaining[0]
                  let value = ''
                  let i = 1
                  let escaped = false
                  while (i < remaining.length) {
                    if (escaped) {
                      value += remaining[i]
                      escaped = false
                      i++
                    } else if (remaining[i] === '\\') {
                      escaped = true
                      i++
                    } else if (remaining[i] === quote) {
                      break
                    } else {
                      value += remaining[i]
                      i++
                    }
                  }
                  cleanText = value
                    .replace(/\\n/g, '\n')
                    .replace(/\\'/g, "'")
                    .replace(/\\"/g, '"')
                    .replace(/\\t/g, '\t')
                    .replace(/\\r/g, '\r')
                }
              }
            }
          }
        }
      }
    } catch (e) {
      // 解析失败，使用原始文本
      console.warn('⚠️ [VocabNotationCard] Failed to parse explanation JSON:', e, 'Original text:', cleanText)
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
      console.warn('⚠️ [VocabNotationCard] Failed to parse explanation from code block:', e)
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

/**
 * VocabNotationCard - 显示词汇注释卡片（由原 TokenNotation 重命名）
 * 
 * Props:
 * - isVisible: 是否显示
 * - note: 备用文本
 * - position: 定位信息（可选）
 * - textId, sentenceId, tokenIndex: 定位到具体词汇示例
 * - onMouseEnter, onMouseLeave: 悬停回调
 * - getVocabExampleForToken: 从缓存/后端获取示例
 */
export default function VocabNotationCard({ 
  isVisible = false, 
  note = "This is a test note", 
  position = null,
  textId = null,
  sentenceId = null,
  tokenIndex = null,
  onMouseEnter = null,
  onMouseLeave = null,
  getVocabExampleForToken = null,
  anchorRef = null
}) {
  const [vocabExample, setVocabExample] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [portalStyle, setPortalStyle] = useState({})
  const cardRef = useRef(null)
  const [cardHeight, setCardHeight] = useState(null)
  const portalContainerRef = useRef(null)
  // 🔧 使用 ref 存储上一次的位置，避免相同位置时触发更新
  const lastPositionRef = useRef({ left: null, top: null, opacity: null })

  // 🔧 当 isVisible 为 true 时，触发数据加载（不再维护额外的 show 状态，完全由 isVisible 控制显示）
  // 🔧 修复：使用 ref 跟踪是否已加载，避免重复加载
  const hasLoadedRef = useRef(false)
  const loadingKeyRef = useRef(null)
  
  useEffect(() => {
    if (!isVisible) {
      logVocabNotationDebug('⬜ [VocabNotationCard] visible=false', { textId, sentenceId, tokenIndex })
      return
    }

    logVocabNotationDebug('🟩 [VocabNotationCard] visible=true', { textId, sentenceId, tokenIndex })

    // 🔧 生成当前加载的 key，用于检测参数是否变化
    const currentKey = `${textId}:${sentenceId}:${tokenIndex}`
    
    // 🔧 如果 key 变化了，重置加载状态
    if (loadingKeyRef.current !== currentKey) {
      hasLoadedRef.current = false
      loadingKeyRef.current = currentKey
      // 🔧 key 变化时，清除旧数据（可选，也可以保留）
      // setVocabExample(null)
      // setError(null)
    }

    // 🔧 如果已经加载过相同 key 的数据，且数据存在，不再重新加载
    if (hasLoadedRef.current && loadingKeyRef.current === currentKey && vocabExample !== null) {
      logVocabNotationDebug('⏭️ [VocabNotationCard] skip reload (already loaded)', {
        textId,
        sentenceId,
        tokenIndex,
        hasExample: Boolean(vocabExample),
      })
      return
    }

    // 🔧 如果正在加载中，不重复加载
    if (isLoading) {
      logVocabNotationDebug('⏭️ [VocabNotationCard] skip reload (already loading)', {
        textId,
        sentenceId,
        tokenIndex,
      })
      return
    }

    // 🔧 如果已经加载过但数据为 null（表示没有数据），不再重新加载（避免无限循环）
    if (hasLoadedRef.current && loadingKeyRef.current === currentKey && vocabExample === null && !error) {
      logVocabNotationDebug('⏭️ [VocabNotationCard] skip reload (already loaded but no data)', {
        textId,
        sentenceId,
        tokenIndex,
      })
      return
    }

    // 🔧 只有在没有数据且没有错误时才加载
    if (!vocabExample && !error) {
      if (getVocabExampleForToken) {
        logVocabNotationDebug('⏳ [VocabNotationCard] fetch example (via getVocabExampleForToken)', {
          textId,
          sentenceId,
          tokenIndex,
        })
        setIsLoading(true)
        setError(null)
        getVocabExampleForToken(textId, sentenceId, tokenIndex)
          .then(example => {
            setVocabExample(example || null)
            setIsLoading(false)
            hasLoadedRef.current = true
            logVocabNotationDebug('✅ [VocabNotationCard] example resolved', {
              textId,
              sentenceId,
              tokenIndex,
              hasExplanation: Boolean(example?.context_explanation),
            })
          })
          .catch(error => {
            console.error('❌ [VocabNotationCard] Error fetching vocab example:', error)
            setError(error.message || 'Failed to load vocab example')
            setVocabExample(null)
            setIsLoading(false)
            hasLoadedRef.current = false
            logVocabNotationDebug('❌ [VocabNotationCard] example fetch error', {
              textId,
              sentenceId,
              tokenIndex,
              message: error?.message || String(error),
            })
          })
      } else if (textId && sentenceId && tokenIndex) {
        logVocabNotationDebug('⏳ [VocabNotationCard] fetch example (via getVocabExampleByLocation)', {
          textId,
          sentenceId,
          tokenIndex,
        })
        setIsLoading(true)
        setError(null)
        apiService.getVocabExampleByLocation(textId, sentenceId, tokenIndex)
          .then(response => {
            if (response && response.vocab_id) {
              setVocabExample(response)
            } else {
              setVocabExample(null)
            }
            setIsLoading(false)
            hasLoadedRef.current = true
            logVocabNotationDebug('✅ [VocabNotationCard] example resolved (by location)', {
              textId,
              sentenceId,
              tokenIndex,
              hasExplanation: Boolean(response?.context_explanation),
            })
          })
          .catch(error => {
            console.error('❌ [VocabNotationCard] Error fetching vocab example:', error)
            setError(error.message || 'Failed to load vocab example')
            setIsLoading(false)
            hasLoadedRef.current = false
            logVocabNotationDebug('❌ [VocabNotationCard] example fetch error (by location)', {
              textId,
              sentenceId,
              tokenIndex,
              message: error?.message || String(error),
            })
          })
      }
    } else if (vocabExample) {
      // 🔧 如果已有数据，标记为已加载
      hasLoadedRef.current = true
    }
  }, [isVisible, textId, sentenceId, tokenIndex, getVocabExampleForToken])

  useEffect(() => {
    if (typeof window === 'undefined') return
    if (!portalContainerRef.current) {
      let container = document.getElementById('notation-portal-root')
      if (!container) {
        container = document.createElement('div')
        container.id = 'notation-portal-root'
        container.style.position = 'relative'
        container.style.zIndex = '9999'
        document.body.appendChild(container)
      }
      portalContainerRef.current = container
    }
  }, [])

  const updatePosition = useCallback(() => {
    if (!anchorRef?.current || !portalContainerRef.current) {
      logVocabNotationDebug('⚠️ [VocabNotationCard] updatePosition skipped (no anchor or portal container)', {
        hasAnchor: Boolean(anchorRef?.current),
        hasPortal: Boolean(portalContainerRef.current),
        textId,
        sentenceId,
        tokenIndex,
      })
      return
    }
    const rect = anchorRef.current.getBoundingClientRect()
    const viewportWidth = window.innerWidth || document.documentElement.clientWidth
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight
    const measuredHeight =
      cardRef.current?.getBoundingClientRect().height ||
      cardHeight ||
      DEFAULT_CARD_MAX_HEIGHT
    
    // 左对齐到 token 的左边
    const desiredLeft = rect.left
    const maxLeft = viewportWidth - DEFAULT_CARD_WIDTH - CARD_MARGIN
    const left = Math.max(CARD_MARGIN, Math.min(desiredLeft, maxLeft))
    
    // 默认显示在 token 正下方
    let top = rect.bottom + CARD_MARGIN
    const spaceBelow = viewportHeight - rect.bottom - CARD_MARGIN
    const spaceAbove = rect.top
    
    // 如果下方空间不够（无法完整显示卡片），且上方有足够空间，则显示在上方
    if (spaceBelow < measuredHeight && spaceAbove >= measuredHeight) {
      // 显示在 token 正上方，卡片底部与 token 行上边对齐（无间隙）
      top = rect.top - measuredHeight
    }
    
    // 确保不会超出视口边界
    const finalTop = Math.max(0, Math.min(top, viewportHeight - measuredHeight))
    const finalOpacity = isVisible ? 1 : 0
    
    // 🔧 如果位置和透明度没有变化，跳过更新，避免不必要的重新渲染
    if (
      lastPositionRef.current.left === left &&
      lastPositionRef.current.top === finalTop &&
      lastPositionRef.current.opacity === finalOpacity
    ) {
      return
    }
    
    lastPositionRef.current = { left, top: finalTop, opacity: finalOpacity }
    
    setPortalStyle({
      position: 'fixed',
      top: `${finalTop}px`,
      left: `${left}px`,
      width: `${DEFAULT_CARD_WIDTH}px`,
      opacity: finalOpacity,
      pointerEvents: isVisible ? 'auto' : 'none',
      zIndex: 100000,
      ...(position || {})
    })

    logVocabNotationDebug('📐 [VocabNotationCard] updatePosition', {
      textId,
      sentenceId,
      tokenIndex,
      rect: {
        left: rect.left,
        top: rect.top,
        bottom: rect.bottom,
        width: rect.width,
        height: rect.height,
      },
      viewport: { width: viewportWidth, height: viewportHeight },
      measuredHeight,
      computed: { left, top: finalTop },
      isVisible,
    })
  }, [anchorRef, isVisible, position, cardHeight])

  useLayoutEffect(() => {
    if (isVisible && cardRef.current) {
      const h = cardRef.current.getBoundingClientRect().height
      if (h && h !== cardHeight) {
        setCardHeight(h)
      }
    }
  }, [isVisible, cardHeight])

  useEffect(() => {
    if (!isVisible) return
    updatePosition()
    const handleScroll = () => updatePosition()
    window.addEventListener('scroll', handleScroll, true)
    window.addEventListener('resize', handleScroll)
    return () => {
      window.removeEventListener('scroll', handleScroll, true)
      window.removeEventListener('resize', handleScroll)
    }
  }, [isVisible, updatePosition])

  // 🔧 修复首次 hover 时 portal 容器尚未创建的问题：
  // 如果还没有 portalContainerRef，尝试在这里同步创建，而不是等 useEffect 之后
  if (!portalContainerRef.current && typeof document !== 'undefined') {
    let container = document.getElementById('notation-portal-root')
    if (!container) {
      container = document.createElement('div')
      container.id = 'notation-portal-root'
      container.style.position = 'relative'
      container.style.zIndex = '9999'
      document.body.appendChild(container)
    }
    portalContainerRef.current = container
  }

  if (!portalContainerRef.current) {
    logVocabNotationDebug('⚠️ [VocabNotationCard] render skipped because no portalContainerRef (after sync ensure)', {
      textId,
      sentenceId,
      tokenIndex,
      isVisible,
    })
    return null
  }

  let displayContent = note

  if (isLoading) {
    // 🔧 显示"正在生成解释"的灰色文字
    displayContent = (
      <div className="flex items-center gap-2">
        <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-gray-500">正在生成解释...</span>
      </div>
    )
  } else if (error) {
    displayContent = (
      <div className="text-red-600">
        <div className="font-semibold">加载失败</div>
        <div className="text-xs mt-1">{error}</div>
      </div>
    )
  } else if (vocabExample && vocabExample.context_explanation) {
    displayContent = (
      <div>
        <div className="text-xs text-gray-500 mb-1">词汇解释</div>
        <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
          {parseExplanation(vocabExample.context_explanation)}
        </div>
      </div>
    )
  } else if (vocabExample === null && !isLoading) {
    // 🔧 如果example为null且不在加载中，显示"正在生成解释"
    displayContent = (
      <div className="text-gray-500 text-sm">正在生成解释...</div>
    )
  }

  return createPortal(
    <div 
      className="transition-opacity duration-200 notation-card"
      style={portalStyle}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={(e) => e.stopPropagation()}
    >
      <div 
        ref={cardRef}
        className="bg-white border border-gray-300 rounded-lg shadow-lg p-3"
        style={{
          maxHeight: `${DEFAULT_CARD_MAX_HEIGHT}px`,
          overflowY: 'auto'
        }}
      >
        {displayContent}
      </div>
    </div>,
    portalContainerRef.current
  )
}


