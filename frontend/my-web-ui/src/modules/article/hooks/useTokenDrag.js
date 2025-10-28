import { useRef } from 'react'
import { getTokenId, rectsOverlap } from '../utils/tokenUtils'

/**
 * Custom hook to manage token drag selection
 */
export function useTokenDrag({ 
  sentences, 
  selectedTokenIds, 
  activeSentenceRef,
  emitSelection,
  clearSelection 
}) {
  const isDraggingRef = useRef(false)
  const wasDraggingRef = useRef(false)
  const hasMovedRef = useRef(false)
  const dragSentenceIndexRef = useRef(null)
  const dragStartIndexRef = useRef(null)
  const selectionBeforeDragRef = useRef(null)
  const suppressNextClickRef = useRef(false)
  const dragStartPointRef = useRef({ x: 0, y: 0 })
  const tokenRefsRef = useRef({})

  const handleMouseDownToken = (sIdx, tIdx, token, e) => {
    if (!token?.selectable) return
    if (activeSentenceRef.current != null && activeSentenceRef.current !== sIdx) {
      e.preventDefault()
      clearSelection()
      // 设置新的活跃句子
      activeSentenceRef.current = sIdx
      // 重新开始选择，只选择当前token
      const startUid = getTokenId(token, sIdx)
      // Debug logging removed for performance
      if (startUid) {
        const next = new Set([startUid])
        selectionBeforeDragRef.current = new Set(next)
        emitSelection(next, token?.token_body ?? '')
      }
    } else {
      e.preventDefault()
      isDraggingRef.current = true
      wasDraggingRef.current = true
      hasMovedRef.current = false
      dragSentenceIndexRef.current = sIdx
      dragStartIndexRef.current = tIdx
      selectionBeforeDragRef.current = new Set(selectedTokenIds)
      if (activeSentenceRef.current == null) {
        activeSentenceRef.current = sIdx
      }
      dragStartPointRef.current = { x: e.clientX, y: e.clientY }
      const startUid = getTokenId(token, sIdx)
      console.debug('[useTokenDrag.mouseDown] sIdx=', sIdx, 'startUid=', startUid, 'token=', token?.token_body)
      if (startUid) {
        const next = new Set(selectionBeforeDragRef.current)
        next.add(startUid)
        selectionBeforeDragRef.current = new Set(next)
        emitSelection(next, token?.token_body ?? '')
      }
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
        const id = getTokenId(tk, sIdx)
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
          const id = getTokenId(tk, sIdx)
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

  return {
    isDraggingRef,
    tokenRefsRef,
    handleMouseDownToken,
    handleMouseEnterToken,
    handleMouseMove,
    handleMouseUp,
    handleBackgroundClick
  }
}

