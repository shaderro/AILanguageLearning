import { useMemo, useRef, useState } from 'react'
import { useArticle } from '../../../hooks/useApi'
import { apiService } from '../../../services/api'
import { useChatEvent } from '../contexts/ChatEventContext'

// InlineExplanation 组件 - 用于显示hover时的解释
function InlineExplanation({ explanation = "This is a quick explanation", token = null }) {
  const { sendMessageToChat } = useChatEvent()

  const handleDetailClick = (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    const tokenText = typeof token === 'string' ? token : (token?.token_body ?? token?.token ?? '')
    console.log('Token text:', tokenText) // 添加调试信息
    
    sendMessageToChat(
      "请为这个词和它在句中的用法提供详细解释",
      tokenText
    )
  }

  return (
    <div className="absolute top-full left-0 z-10 mt-1">
      <div className="px-2 py-1 text-xs bg-gray-100 text-gray-500 border border-gray-300 rounded shadow-lg">
        <div className="mb-1">{explanation}</div>
        <button
          onClick={handleDetailClick}
          className="text-xs text-blue-600 hover:text-blue-800 underline cursor-pointer"
        >
          detail explanation with AI
        </button>
      </div>
    </div>
  )
}

// VocabExplanationButton 简化版 - 绝对定位覆盖
function VocabExplanationButton({ token, onGetExplanation }) {
  const [isClicked, setIsClicked] = useState(false)

  const handleClick = (e) => {
    e.preventDefault() // 阻止默认行为
    e.stopPropagation() // 阻止事件冒泡
    setIsClicked(true)
    
    // 新增：调用回调函数来通知父组件
    if (onGetExplanation) {
      onGetExplanation(token, null) // 传递null作为explanation
    }
  }

  return (
    <div className="absolute top-full left-0 z-10 mt-1">
      {isClicked ? (
        <InlineExplanation explanation="This is a test explanation" />
      ) : (
        <button
          onClick={handleClick}
          className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 rounded border border-blue-300 transition-colors duration-150 shadow-lg"
        >
          quick translation
        </button>
      )}
    </div>
  )
}

const getTokenKey = (sentIdx, token, tokenIdx) => {
  const base = `${sentIdx}-${tokenIdx}`
  if (typeof token === 'string') return `${base}-${token}`
  if (token && typeof token === 'object') {
    const t = token?.token_body ?? ''
    const gid = token?.global_token_id ?? ''
    const sid = token?.sentence_token_id ?? ''
    return `${base}-${gid}-${sid}-${t}`
  }
  return base
}

const getTokenId = (token) => {
  if (!token || typeof token !== 'object') return undefined
  const gid = token?.global_token_id
  const sid = token?.sentence_token_id
  return (gid != null && sid != null) ? `${gid}-${sid}` : undefined
}

const rectsOverlap = (a, b) => {
  return !(b.left > a.right ||
           b.right < a.left ||
           b.top > a.bottom ||
           b.bottom < a.top)
}

export default function ArticleViewer({ articleId, onTokenSelect }) {
  const { data, isLoading, isError, error } = useArticle(articleId)
  const [selectedTokenIds, setSelectedTokenIds] = useState(() => new Set())
  const [activeSentenceIndex, setActiveSentenceIndex] = useState(null)
  
  // 存储词汇解释
  const [vocabExplanations, setVocabExplanations] = useState(() => new Map())
  
  // 新增：存储被点击了vocab explanation的token ID
  const [clickedVocabTokenIds, setClickedVocabTokenIds] = useState(() => new Set())
  
  // 新增：存储当前hover的token ID
  const [hoveredTokenId, setHoveredTokenId] = useState(null)
  
  // 新增：存储当前选中的token对象
  const [selectedToken, setSelectedToken] = useState(null)

  // selection / drag state
  const isDraggingRef = useRef(false)
  const wasDraggingRef = useRef(false)
  const hasMovedRef = useRef(false)
  const activeSentenceRef = useRef(null)
  const dragSentenceIndexRef = useRef(null)
  const dragStartIndexRef = useRef(null)
  const selectionBeforeDragRef = useRef(null)
  const suppressNextClickRef = useRef(false)
  const dragStartPointRef = useRef({ x: 0, y: 0 })

  // token DOM refs: { [sentenceIdx]: { [tokenIdx]: HTMLElement } }
  const tokenRefsRef = useRef({})

  const sentences = useMemo(() => {
    const raw = data?.data?.sentences
    return Array.isArray(raw) ? raw : []
  }, [data])

  const buildSelectedTexts = (sIdx, idSet) => {
    if (sIdx == null) return []
    const tokens = (sentences[sIdx]?.tokens || [])
    const texts = []
    for (let i = 0; i < tokens.length; i++) {
      const tk = tokens[i]
      if (tk && typeof tk === 'object') {
        const id = getTokenId(tk)
        if (id && idSet.has(id)) texts.push(tk.token_body ?? '')
      }
    }
    return texts
  }

  const emitSelection = (set, lastTokenText = '') => {
    setSelectedTokenIds(set)
    
    // 新增：更新选中的token对象
    if (set.size === 1) {
      const selectedTokenObj = getSelectedTokenObject(set)
      setSelectedToken(selectedTokenObj)
    } else {
      setSelectedToken(null)
    }
    
    if (onTokenSelect) {
      const selectedTexts = buildSelectedTexts(activeSentenceRef.current, set)
      onTokenSelect(lastTokenText, set, selectedTexts)
    }
  }

  // 修改：获取被选中的token对象
  const getSelectedTokenObject = (tokenIdSet) => {
    if (tokenIdSet.size !== 1) return null
    
    // 使用activeSentenceRef.current来限制搜索范围
    const sIdx = activeSentenceRef.current
    if (sIdx == null) return null
    
    const tokens = sentences[sIdx]?.tokens || []
    for (let tIdx = 0; tIdx < tokens.length; tIdx++) {
      const token = tokens[tIdx]
      const uid = getTokenId(token)
      if (uid && tokenIdSet.has(uid)) {
        return token
      }
    }
    return null
  }

  const clearSelection = () => {
    const empty = new Set()
    setSelectedTokenIds(empty)
    setSelectedToken(null) // 新增：清除选中的token对象
    activeSentenceRef.current = null
    setActiveSentenceIndex(null)
    if (onTokenSelect) {
      onTokenSelect('', empty, [])
    }
  }

  // 修改：处理词汇解释获取
  const handleGetExplanation = (token, explanation) => {
    const tokenId = getTokenId(token)
    if (tokenId) {
      setVocabExplanations(prev => new Map(prev).set(tokenId, explanation))
      // 新增：标记该token已被点击
      setClickedVocabTokenIds(prev => new Set(prev).add(tokenId))
    }
  }

  const addSingle = (sIdx, token) => {
    if (activeSentenceRef.current != null && activeSentenceRef.current !== sIdx) {
      clearSelection()
      return
    }
    const uid = getTokenId(token)
    if (!uid) return
    const next = new Set(selectedTokenIds)
    next.add(uid)
    if (activeSentenceRef.current == null) {
      activeSentenceRef.current = sIdx
      setActiveSentenceIndex(sIdx)
    }
    
    // 新增：直接设置选中的token对象
    setSelectedToken(token)
    
    emitSelection(next, token?.token_body ?? '')
  }

  const handleMouseDownToken = (sIdx, tIdx, token, e) => {
    if (!token?.selectable) return
    if (activeSentenceRef.current != null && activeSentenceRef.current !== sIdx) {
      e.preventDefault()
      clearSelection()
      return
    }
    e.preventDefault()
    isDraggingRef.current = true
    wasDraggingRef.current = true
    hasMovedRef.current = false
    dragSentenceIndexRef.current = sIdx
    dragStartIndexRef.current = tIdx
    selectionBeforeDragRef.current = new Set(selectedTokenIds)
    if (activeSentenceRef.current == null) {
      activeSentenceRef.current = sIdx
      setActiveSentenceIndex(sIdx)
    }
    dragStartPointRef.current = { x: e.clientX, y: e.clientY }
    const startUid = getTokenId(token)
    if (startUid) {
      const next = new Set(selectionBeforeDragRef.current)
      next.add(startUid)
      selectionBeforeDragRef.current = new Set(next)
      emitSelection(next, token?.token_body ?? '')
    }
    suppressNextClickRef.current = true
    setTimeout(() => { suppressNextClickRef.current = false }, 0)
  }

  const handleMouseEnterToken = (sIdx, tIdx, token) => {
    if (!isDraggingRef.current) return
    if (dragSentenceIndexRef.current !== sIdx) return
    if (!token?.selectable) return

    hasMovedRef.current = true

    const start = dragStartIndexRef.current ?? tIdx
    const end = tIdx
    const [from, to] = start <= end ? [start, end] : [end, start]

    const base = selectionBeforeDragRef.current ?? new Set()
    const rangeSet = new Set(base)

    const tokens = (sentences[sIdx]?.tokens || [])
    for (let i = from; i <= to; i++) {
      const tk = tokens[i]
      if (tk && typeof tk === 'object' && tk.selectable) {
        const id = getTokenId(tk)
        if (id) rangeSet.add(id)
      }
    }
    emitSelection(rangeSet, token?.token_body ?? '')
  }

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current) return
    const sIdx = activeSentenceRef.current
    if (sIdx == null) return

    const start = dragStartPointRef.current
    const current = { x: e.clientX, y: e.clientY }
    const rect = {
      left: Math.min(start.x, current.x),
      right: Math.max(start.x, current.x),
      top: Math.min(start.y, current.y),
      bottom: Math.max(start.y, current.y),
    }

    const base = selectionBeforeDragRef.current ?? new Set()
    const rangeSet = new Set(base)

    const tokens = (sentences[sIdx]?.tokens || [])
    const tokenRefsRow = tokenRefsRef.current[sIdx] || {}

    const coveredIdx = []
    for (let i = 0; i < tokens.length; i++) {
      const tk = tokens[i]
      if (!(tk && typeof tk === 'object' && tk.selectable)) continue
      const el = tokenRefsRow[i]
      if (!el) continue
      const elRect = el.getBoundingClientRect()
      if (rectsOverlap(rect, elRect)) {
        coveredIdx.push(i)
      }
    }

    let lastText = ''
    if (coveredIdx.length > 0) {
      const minIdx = Math.min(...coveredIdx)
      const maxIdx = Math.max(...coveredIdx)
      for (let i = minIdx; i <= maxIdx; i++) {
        const tk = tokens[i]
        if (tk && typeof tk === 'object' && tk.selectable) {
          const id = getTokenId(tk)
          if (id) rangeSet.add(id)
          lastText = tk?.token_body ?? lastText
        }
      }
    }

    hasMovedRef.current = true
    emitSelection(rangeSet, lastText)
  }

  const handleMouseUp = () => {
    if (isDraggingRef.current || wasDraggingRef.current) {
      suppressNextClickRef.current = true
      setTimeout(() => { suppressNextClickRef.current = false }, 0)
    }
    isDraggingRef.current = false
    wasDraggingRef.current = false
    hasMovedRef.current = false
    dragSentenceIndexRef.current = null
    dragStartIndexRef.current = null
    selectionBeforeDragRef.current = null
  }

  const handleBackgroundClick = (e) => {
    if (suppressNextClickRef.current) {
      suppressNextClickRef.current = false
      return
    }
    const el = e.target?.closest ? e.target.closest('[data-token="1"]') : null
    if (!el) clearSelection()
  }

  // 新增：处理token hover事件
  const handleTokenHover = (token) => {
    const tokenId = getTokenId(token)
    setHoveredTokenId(tokenId)
  }

  const handleTokenLeave = () => {
    setHoveredTokenId(null)
  }

  // 在ArticleViewer组件中添加一个函数来获取被选中的token
  const getSelectedToken = () => {
    if (selectedTokenIds.size !== 1) return null
    
    for (let sIdx = 0; sIdx < sentences.length; sIdx++) {
      const tokens = sentences[sIdx]?.tokens || []
      for (let tIdx = 0; tIdx < tokens.length; tIdx++) {
        const token = tokens[tIdx]
        const uid = getTokenId(token)
        if (uid && selectedTokenIds.has(uid)) {
          return token
        }
      }
    }
    return null
  }

  if (isLoading) {
    return (
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto h-full max-h-[calc(100vh-200px)]">
        <div className="text-gray-500">Loading article...</div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto h-full max-h-[calc(100vh-200px)]">
        <div className="text-red-500">Failed to load: {String(error?.message || error)}</div>
      </div>
    )
  }

  return (
    <div
      className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto h-full max-h-[calc(100vh-200px)] "
      onClick={handleBackgroundClick}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="space-y-[0.66rem] leading-[1.33] text-gray-900">
        {sentences.map((sentence, sIdx) => (
          <div key={`s-${sIdx}`} className={`select-none ${activeSentenceIndex === sIdx ? "border border-gray-300 rounded-md px-2 py-1" : ""}`} data-sentence="1">
            {(sentence?.tokens || []).map((t, tIdx) => {
              const displayText = typeof t === 'string' ? t : (t?.token_body ?? t?.token ?? '')
              const selectable = typeof t === 'object' ? !!t?.selectable : false
              const uid = getTokenId(t)
              const selected = uid ? selectedTokenIds.has(uid) : false
              const hasSelection = selectedTokenIds && selectedTokenIds.size > 0
              const hoverAllowed = selectable && (!hasSelection ? (activeSentenceIndex == null || activeSentenceIndex === sIdx) : activeSentenceIndex === sIdx)
              const cursorClass = hoverAllowed ? 'cursor-pointer' : 'cursor-default'
              
              // 新增：检查该token是否被点击了vocab explanation
              const isClickedVocab = uid ? clickedVocabTokenIds.has(uid) : false
              
              // 新增：检查是否正在hover这个token
              const isHovered = uid === hoveredTokenId
              
              const bgClass = selected
                ? 'bg-yellow-300'
                : (hoverAllowed ? 'bg-transparent hover:bg-yellow-200' : 'bg-transparent')
              
              // 新增：下划线样式
              const underlineClass = isClickedVocab ? 'underline decoration-2 decoration-blue-500' : ''
              
              // 判断是否为text类型token
              const isTextToken = typeof t === 'object' && t?.token_type === 'text'
              
              return (
                <span
                  key={getTokenKey(sIdx, t, tIdx)}
                  className="relative inline-block"
                >
                  <span
                    data-token="1"
                    ref={(el) => {
                      if (!tokenRefsRef.current[sIdx]) tokenRefsRef.current[sIdx] = {}
                      tokenRefsRef.current[sIdx][tIdx] = el
                    }}
                    onMouseDown={(e) => handleMouseDownToken(sIdx, tIdx, t, e)}
                    onMouseEnter={() => {
                      handleMouseEnterToken(sIdx, tIdx, t)
                      handleTokenHover(t)
                    }}
                    onMouseLeave={handleTokenLeave}
                    onClick={(e) => { if (!isDraggingRef.current && selectable) { e.preventDefault(); addSingle(sIdx, t) } }}
                    className={['px-0.5 rounded-sm transition-colors duration-150 select-none', cursorClass, bgClass, underlineClass].join(' ')}
                    style={{ color: '#111827' }}
                  >
                    {displayText}
                  </span>
                  
                  {/* 显示vocab explanation button - 当选中单个text类型token时 */}
                  {isTextToken && selected && selectedTokenIds.size === 1 && (
                    <VocabExplanationButton 
                      token={t} 
                      onGetExplanation={handleGetExplanation}
                    />
                  )}
                  
                  {/* 新增：显示hover解释 - 当token已被点击且正在hover时 */}
                  {isTextToken && isClickedVocab && isHovered && (
                    <InlineExplanation 
                      explanation="This is a test explanation" 
                      token={selectedToken}
                    />
                  )}
                </span>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
