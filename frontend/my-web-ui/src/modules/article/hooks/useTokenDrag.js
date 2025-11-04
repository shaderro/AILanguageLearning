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
    console.log('🖱️ [useTokenDrag] mouseDown:', { sIdx, tIdx, token: token?.token_body, selectable: token?.selectable })
    if (!token?.selectable) return
    if (activeSentenceRef.current != null && activeSentenceRef.current !== sIdx) {
      e.preventDefault()
      console.log('🔄 [useTokenDrag] Switching to new sentence, clearing previous selection')
      clearSelection()
      // 设置新的活跃句子
      activeSentenceRef.current = sIdx
      // 重新开始选择，只选择当前token
      const startUid = getTokenId(token, sIdx)
      if (startUid) {
        const next = new Set([startUid])
        selectionBeforeDragRef.current = new Set(next)
        emitSelection(next, token?.token_body ?? '')
      }
    } else {
      e.preventDefault()
      console.log('🎯 [useTokenDrag] Starting drag in same sentence')
      isDraggingRef.current = true
      wasDraggingRef.current = true
      hasMovedRef.current = false
      dragSentenceIndexRef.current = sIdx
      dragStartIndexRef.current = tIdx
      selectionBeforeDragRef.current = new Set(selectedTokenIds)
      console.log('📦 [useTokenDrag] selectionBeforeDrag saved:', Array.from(selectionBeforeDragRef.current))
      if (activeSentenceRef.current == null) {
        activeSentenceRef.current = sIdx
      }
      dragStartPointRef.current = { x: e.clientX, y: e.clientY }
      const startUid = getTokenId(token, sIdx)
      if (startUid) {
        const next = new Set(selectionBeforeDragRef.current)
        next.add(startUid)
        selectionBeforeDragRef.current = new Set(next)
        console.log('➕ [useTokenDrag] Added start token, selection now:', Array.from(next))
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
    
    // 调试信息显示在标题栏
    document.title = `drag: start=${start} end=${end} range=[${from}-${to}] count=${rangeSet.size}`
    
    emitSelection(rangeSet, token?.token_body ?? '')
  }

  const handleMouseMove = (e) => {
    // 🔧 禁用：让 handleMouseEnterToken 完全负责拖拽选择逻辑
    // handleMouseMove 的矩形覆盖判断会导致跨行拖拽时的选择错误
    // 改为依赖 TokenSpan 的 onMouseEnter 事件来跟踪当前 token
    return
  }

  const handleMouseUp = () => {
    // 写入标题栏以便无控制台时看到
    document.title = `mouseUp: size=${selectedTokenIds.size}, hasMoved=${hasMovedRef.current}`
    
    console.log('🆙 [useTokenDrag] mouseUp:', {
      isDragging: isDraggingRef.current,
      wasDragging: wasDraggingRef.current,
      hasMoved: hasMovedRef.current,
      currentSelection: Array.from(selectedTokenIds)
    })
    
    if (isDraggingRef.current || wasDraggingRef.current) {
      suppressNextClickRef.current = true
      setTimeout(() => { 
        suppressNextClickRef.current = false
        console.log('🔓 [useTokenDrag] suppressNextClick released')
      }, 100)
    }
    isDraggingRef.current = false
    // 延迟重置 wasDraggingRef，确保后续事件能识别"刚结束拖拽"
    setTimeout(() => { 
      wasDraggingRef.current = false
      console.log('🔓 [useTokenDrag] wasDragging reset')
    }, 150)
    hasMovedRef.current = false
    dragSentenceIndexRef.current = null
    dragStartIndexRef.current = null
    // 不再清空 selectionBeforeDragRef，避免意外丢失选择
    console.log('✅ [useTokenDrag] mouseUp complete, selection preserved')
  }

  const handleBackgroundClick = (e) => {
    console.log('🖱️ [useTokenDrag] backgroundClick:', {
      wasDragging: wasDraggingRef.current,
      suppressNextClick: suppressNextClickRef.current,
      target: e.target?.tagName
    })
    
    // 如果刚结束拖拽（点击触发时机晚于 mouseup），不清空选择
    if (wasDraggingRef.current) {
      console.log('⏭️ [useTokenDrag] Skipping clear - just finished dragging')
      return
    }
    if (suppressNextClickRef.current) {
      console.log('⏭️ [useTokenDrag] Skipping clear - click suppressed')
      suppressNextClickRef.current = false
      return
    }
    const el = e.target?.closest ? e.target.closest('[data-token="1"]') : null
    if (!el) {
      console.log('🧹 [useTokenDrag] Clearing selection - clicked on background')
      clearSelection()
    } else {
      console.log('⏭️ [useTokenDrag] Not clearing - clicked on token')
    }
  }

  return {
    isDraggingRef,
    wasDraggingRef,
    tokenRefsRef,
    handleMouseDownToken,
    handleMouseEnterToken,
    handleMouseMove,
    handleMouseUp,
    handleBackgroundClick
  }
}

