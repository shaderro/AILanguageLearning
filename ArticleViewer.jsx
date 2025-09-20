import { useMemo, useRef, useState } from 'react'
import { useArticle } from '../../../hooks/useApi'
import { apiService } from '../../../services/api'

const getTokenKey = (sentIdx, token, tokenIdx) => {
  const base = ${sentIdx}-
  if (typeof token === 'string') return ${base}-
  if (token && typeof token === 'object') {
    const t = token?.token_body ?? ''
    const gid = token?.global_token_id ?? ''
    const sid = token?.sentence_token_id ?? ''
    return ${base}---
  }
  return base
}

const getTokenId = (token) => {
  if (!token || typeof token !== 'object') return undefined
  const gid = token?.global_token_id
  const sid = token?.sentence_token_id
  return (gid != null && sid != null) ? ${gid}- : undefined
}

const rectsOverlap = (a, b) => {
  return !(b.left > a.right ||
           b.right < a.left ||
           b.top > a.bottom ||
           b.bottom < a.top)
}

// VocabExplanationButton ���
function VocabExplanationButton({ token, onGetExplanation }) {
  const [isLoading, setIsLoading] = useState(false)
  const [explanation, setExplanation] = useState(null)
  const [error, setError] = useState(null)

  const handleClick = async () => {
    if (explanation) return // ������н��ͣ����ظ�����
    
    setIsLoading(true)
    setError(null)
    try {
      // ����API��ȡ�ʻ����
      const result = await apiService.getVocabExplanation(token.token_body)
      
      setExplanation(result)
      if (onGetExplanation) {
        onGetExplanation(token, result)
      }
    } catch (error) {
      console.error('Failed to get vocab explanation:', error)
      setError('Failed to load explanation')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="mt-1">
      <button
        onClick={handleClick}
        disabled={isLoading}
        className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 rounded border border-blue-300 transition-colors duration-150 disabled:opacity-50"
      >
        {isLoading ? 'Loading...' : 'vocab explanation'}
      </button>
      {error && (
        <div className="mt-1 text-xs text-red-600">{error}</div>
      )}
      {explanation && (
        <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-sm max-w-md">
          <div className="font-semibold text-gray-800 text-base">{explanation.word}</div>
          {explanation.pronunciation && (
            <div className="text-gray-500 text-xs mt-1">{explanation.pronunciation}</div>
          )}
          {explanation.partOfSpeech && (
            <div className="text-blue-600 text-xs mt-1 font-medium">{explanation.partOfSpeech}</div>
          )}
          <div className="text-gray-700 mt-2">{explanation.definition}</div>
          
          {explanation.examples && explanation.examples.length > 0 && (
            <div className="mt-3">
              <div className="font-medium text-gray-700 text-sm">Examples:</div>
              {explanation.examples.map((example, idx) => (
                <div key={idx} className="text-gray-600 text-xs mt-1 italic pl-2 border-l-2 border-gray-300">
                  {example}
                </div>
              ))}
            </div>
          )}
          
          {explanation.synonyms && explanation.synonyms.length > 0 && (
            <div className="mt-3">
              <div className="font-medium text-gray-700 text-sm">Synonyms:</div>
              <div className="text-gray-600 text-xs mt-1">
                {explanation.synonyms.join(', ')}
              </div>
            </div>
          )}
          
          {explanation.difficulty && (
            <div className="mt-2">
              <span className={inline-block px-2 py-1 text-xs rounded }>
                {explanation.difficulty} difficulty
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// VocabTooltip ��� - ������ʾ���н��͵�hoverЧ��
function VocabTooltip({ token, explanation, isVisible }) {
  if (!isVisible || !explanation) return null

  return (
    <div className="absolute z-50 mt-1 p-3 bg-gray-900 text-white text-xs rounded shadow-lg max-w-xs">
      <div className="font-semibold text-sm">{explanation.word}</div>
      {explanation.pronunciation && (
        <div className="text-gray-300 text-xs mt-1">{explanation.pronunciation}</div>
      )}
      <div className="mt-2 text-gray-200">{explanation.definition}</div>
      {explanation.examples && explanation.examples.length > 0 && (
        <div className="mt-2">
          <div className="font-medium text-gray-300">Examples:</div>
          {explanation.examples.slice(0, 1).map((example, idx) => (
            <div key={idx} className="mt-1 italic text-gray-400 text-xs">
              {example}
            </div>
          ))}
        </div>
      )}
      {explanation.difficulty && (
        <div className="mt-2">
          <span className={inline-block px-1 py-0.5 text-xs rounded }>
            {explanation.difficulty}
          </span>
        </div>
      )}
    </div>
  )
}

export default function ArticleViewer({ articleId, onTokenSelect }) {
  const { data, isLoading, isError, error } = useArticle(articleId)
  const [selectedTokenIds, setSelectedTokenIds] = useState(() => new Set())
  const [activeSentenceIndex, setActiveSentenceIndex] = useState(null)
  
  // ����״̬���洢�ʻ����
  const [vocabExplanations, setVocabExplanations] = useState(() => new Map())
  const [hoveredTokenId, setHoveredTokenId] = useState(null)

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
    if (onTokenSelect) {
      const selectedTexts = buildSelectedTexts(activeSentenceRef.current, set)
      onTokenSelect(lastTokenText, set, selectedTexts)
    }
  }

  const clearSelection = () => {
    const empty = new Set()
    emitSelection(empty, '')
    activeSentenceRef.current = null
    setActiveSentenceIndex(null)
  }

  const addSingle = (sIdx, token) => {
    // ������������ӵ� token ʱ��ֻ��յ�ǰѡ�񣬲�ѡ��� token
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
    emitSelection(next, token?.token_body ?? '')
  }

  // ����������ʻ���ͻ�ȡ
  const handleGetExplanation = (token, explanation) => {
    const tokenId = getTokenId(token)
    if (tokenId) {
      setVocabExplanations(prev => new Map(prev).set(tokenId, explanation))
    }
  }

  // ���������token�Ƿ��н���
  const hasExplanation = (token) => {
    const tokenId = getTokenId(token)
    return tokenId ? vocabExplanations.has(tokenId) : false
  }

  // ��������ȡtoken�Ľ���
  const getExplanation = (token) => {
    const tokenId = getTokenId(token)
    return tokenId ? vocabExplanations.get(tokenId) : null
  }

  const handleMouseDownToken = (sIdx, tIdx, token, e) => {
    if (!token?.selectable) return
    // ������������ӵ� token ʱ��ֻ��յ�ǰѡ�񣬲���ֹ�� token ��ѡ��
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
    // record drag start point
    dragStartPointRef.current = { x: e.clientX, y: e.clientY }
    // add start token immediately
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

  // Rectangle selection within the active sentence when dragging over whitespace or anywhere
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

    // ���ռ������θ��ǵ� token ����
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
          <div key={s-} className={select-none } data-sentence="1">
            {(sentence?.tokens || []).map((t, tIdx) => {
              const displayText = typeof t === 'string' ? t : (t?.token_body ?? t?.token ?? '')
              const selectable = typeof t === 'object' ? !!t?.selectable : false
              const uid = getTokenId(t)
              const selected = uid ? selectedTokenIds.has(uid) : false
              const hasSelection = selectedTokenIds && selectedTokenIds.size > 0
              const hoverAllowed = selectable && (!hasSelection ? (activeSentenceIndex == null || activeSentenceIndex === sIdx) : activeSentenceIndex === sIdx)
              const cursorClass = hoverAllowed ? 'cursor-pointer' : 'cursor-default'
              // ����Ƿ�Ϊtext����token
              const isTextToken = typeof t === "object" && t?.token_type === "text"
              const bgClass = selected
                ? 'bg-yellow-300'
                : (hoverAllowed ? 'bg-transparent hover:bg-yellow-200' : 'bg-transparent')
              
              // ����������Ƿ�Ϊtext����token
              const isTextToken = typeof t === 'object' && t?.token_type === 'text'
              const tokenHasExplanation = isTextToken && hasExplanation(t)
              const tokenExplanation = isTextToken ? getExplanation(t) : null
              const isHovered = hoveredTokenId === uid
              
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
                      if (isTextToken && tokenHasExplanation) {
                        setHoveredTokenId(uid)
                      }
                      handleMouseEnterToken(sIdx, tIdx, t)
                    }}
                    onMouseLeave={() => {
                      if (isTextToken && tokenHasExplanation) {
                        setHoveredTokenId(null)
                      }
                    }}
                    onClick={(e) => { if (!isDraggingRef.current && selectable) { e.preventDefault(); addSingle(sIdx, t) } }}
                    className={['px-0.5 rounded-sm transition-colors duration-150 select-none', cursorClass, bgClass].join(' ')}
                    style={{ color: '#111827' }}
                  >
                    {displayText}
                  </span>
                  
                  {/* ��ʾ�ʻ���͵�tooltip */}
                  {isTextToken && tokenHasExplanation && (
                    <VocabTooltip 
                      token={t} 
                      explanation={tokenExplanation} 
                      isVisible={isHovered} 
                    />
                  )}
                  
                  {/* ��ʾvocab explanation button - ����ѡ�е���text����tokenʱ */}
                  {isTextToken && selected && selectedTokenIds.size === 1 && (
                    <VocabExplanationButton 
                      token={t} 
                      onGetExplanation={handleGetExplanation}
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


      {/* ���԰�ť - ������ʾ */}
      <div className="mt-4 p-4 bg-yellow-100 border border-yellow-300 rounded">
        <button
          onClick={() => alert("This is a test explanation")}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          vocab explanation (���԰�ť)
        </button>
      </div>
    </div>
  )
}
