import { useRef, useEffect } from 'react'

/**
 * Custom hook to manage token click selection
 * 支持：
 * 1. 点击多选（toggle 行为）
 * 2. 记录鼠标按下和松开时的位置和 token 信息（仅在同一 sentence 内时打印）
 * 3. 记录鼠标按下时在同一个 sentence 内 hover 的位置（每 0.5 秒打印一次）
 */
export function useTokenDrag({ 
  selectedTokenIdsRef,
  activeSentenceRef,
  clearSelection,
  clearSentenceSelection,
  addDebugLog,
  sentences,
  selectRange // 🔧 接收 selectRange 函数
}) {
  // 🔧 使用 ref 存储 selectRange，避免 useEffect 依赖项变化导致重新注册事件监听器
  const selectRangeRef = useRef(selectRange)
  useEffect(() => {
    selectRangeRef.current = selectRange
  }, [selectRange])
  // 记录鼠标按下时的 token 信息
  const pressTokenRef = useRef(null)
  // 记录鼠标是否按下
  const isMouseDownRef = useRef(false)
  // 记录鼠标移动时的位置和 token 信息（用于 OnMousePressing）
  const lastHoverTokenRef = useRef(null)
  // 定时器引用（用于每 0.5 秒打印一次）
  const pressingLogIntervalRef = useRef(null)
  // 🔧 记录鼠标按下时的位置，用于区分点击和拖拽
  const pressPositionRef = useRef(null)
  // 🔧 记录是否真的拖拽了（鼠标移动了）
  const hasDraggedRef = useRef(false)
  
  // 🔧 拖拽状态管理
  // 拖拽阈值（像素）
  const DRAG_THRESHOLD = 5
  // 是否正在拖拽
  const isDraggingRef = useRef(false)
  // 记录按下时的鼠标位置 {x, y}
  const dragStartPositionRef = useRef(null)
  // 记录最后一次调用的范围（用于节流）
  const lastSelectRangeRef = useRef(null)
  // 🔧 标记刚完成拖拽，用于防止拖拽后立即触发点击事件
  const justFinishedDragRef = useRef(false)
  
  /**
   * 检测鼠标位置下的 token
   * @param {number} x - 鼠标 X 坐标
   * @param {number} y - 鼠标 Y 坐标
   * @returns {Object|null} - { sentenceIdx, tokenIdx } 或 null
   */
  const detectTokenAtPosition = (x, y) => {
    const elementUnderMouse = document.elementFromPoint(x, y)
    const tokenElement = elementUnderMouse?.closest('[data-token-id]')
    
    if (!tokenElement) {
      return null
    }
    
    const tokenId = tokenElement.getAttribute('data-token-id')
    if (!tokenId) {
      return null
    }
    
    // 解析 tokenId: "sentenceIdx-sentence_token_id"
    const parts = tokenId.split('-')
    if (parts.length < 2) {
      return null
    }
    
    const sIdxStr = parts[0]
    const tokenIdStr = parts.slice(1).join('-')
    const sIdx = parseInt(sIdxStr, 10)
    const sentenceTokenId = parseInt(tokenIdStr, 10)
    
    if (isNaN(sIdx) || isNaN(sentenceTokenId)) {
      return null
    }
    
    // 查找 token 在数组中的索引
    if (!sentences || !sentences[sIdx]) {
      return null
    }
    
    const tokens = sentences[sIdx].tokens || []
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i]
      if (token && typeof token === 'object') {
        const tokenSentenceTokenId = token?.sentence_token_id ?? token?.sentenceTokenId
        if (tokenSentenceTokenId != null && Number(tokenSentenceTokenId) === Number(sentenceTokenId)) {
          return {
            sentenceIdx: sIdx,
            tokenIdx: i
          }
        }
      }
    }
    
    return null
  }

  // 监听全局鼠标按下和松开事件
  useEffect(() => {
    const handleGlobalMouseDown = (e) => {
      // 🔧 调试：确保事件被触发
      console.log('🔧 [useTokenDrag] handleGlobalMouseDown 被调用', { 
        clientX: e.clientX, 
        clientY: e.clientY,
        hasAddDebugLog: !!addDebugLog,
        hasSelectRange: !!selectRange
      })
      
      const tokenInfo = detectTokenAtPosition(e.clientX, e.clientY)
      
      // 🔧 记录按下时的鼠标位置到 dragStartPositionRef
      dragStartPositionRef.current = { x: e.clientX, y: e.clientY }
      // 🔧 初始化 isDraggingRef.current = false
      isDraggingRef.current = false
      // 🔧 清空 lastSelectRangeRef.current
      lastSelectRangeRef.current = null
      
      // 记录按下时的 token 信息和位置
      pressTokenRef.current = tokenInfo
      isMouseDownRef.current = true
      pressPositionRef.current = { x: e.clientX, y: e.clientY }
      hasDraggedRef.current = false // 🔧 重置拖拽标志
      
      // 🔧 调试：打印按下时的状态
      if (addDebugLog) {
        addDebugLog('info', `🔍 [useTokenDrag] MouseDown - tokenInfo: ${tokenInfo ? `句子${tokenInfo.sentenceIdx} Token${tokenInfo.tokenIdx}` : 'null'}, pressTokenRef已设置: ${!!pressTokenRef.current}`, null)
      }
      
      // 只在 Token 索引不为空时打印
      if (addDebugLog && tokenInfo && tokenInfo.tokenIdx != null) {
        const logMessage = `OnMousePressPos - X: ${e.clientX}, Y: ${e.clientY} | 句子索引: ${tokenInfo.sentenceIdx}, Token索引: ${tokenInfo.tokenIdx}`
        addDebugLog('info', logMessage, null)
      }
      
      // 启动定时器，每 0.5 秒打印一次 OnMousePressing
      if (pressingLogIntervalRef.current) {
        clearInterval(pressingLogIntervalRef.current)
      }
      pressingLogIntervalRef.current = setInterval(() => {
        if (isMouseDownRef.current && lastHoverTokenRef.current && 
            pressTokenRef.current && pressTokenRef.current.tokenIdx != null &&
            lastHoverTokenRef.current.sentenceIdx === pressTokenRef.current.sentenceIdx) {
          const hoverToken = lastHoverTokenRef.current
          const logMessage = `OnMousePressing - X: ${hoverToken.mouseX}, Y: ${hoverToken.mouseY} | 句子索引: ${hoverToken.sentenceIdx}, Token索引: ${hoverToken.tokenIdx}`
          if (addDebugLog) {
            addDebugLog('info', logMessage, null)
          }
        }
      }, 500)
    }
    
    const handleGlobalMouseUp = (e) => {
      // 🔧 调试：确保事件被触发
      console.log('🔧 [useTokenDrag] handleGlobalMouseUp 被调用', { 
        clientX: e.clientX, 
        clientY: e.clientY,
        hasAddDebugLog: !!addDebugLog,
        hasSelectRange: !!selectRange
      })
      
      const tokenInfo = detectTokenAtPosition(e.clientX, e.clientY)
      
      // 🔧 调试：打印检测到的 token 信息
      if (addDebugLog) {
        addDebugLog('info', `🔍 [useTokenDrag] MouseUp 检测到 token - tokenInfo: ${tokenInfo ? `句子${tokenInfo.sentenceIdx} Token${tokenInfo.tokenIdx}` : 'null'}, pressToken: ${pressTokenRef.current ? `句子${pressTokenRef.current.sentenceIdx} Token${pressTokenRef.current.tokenIdx}` : 'null'}`, null)
      }
      
      // 只在 Token 索引不为空且在同一 sentence 内时打印
      if (addDebugLog && tokenInfo && tokenInfo.tokenIdx != null && 
          pressTokenRef.current && pressTokenRef.current.tokenIdx != null &&
          tokenInfo.sentenceIdx === pressTokenRef.current.sentenceIdx) {
        const logMessage = `OnMouseEndPressPos - X: ${e.clientX}, Y: ${e.clientY} | 句子索引: ${tokenInfo.sentenceIdx}, Token索引: ${tokenInfo.tokenIdx}`
        addDebugLog('info', logMessage, null)
      }
      
      // 🔧 只有在真正拖拽时才调用 selectRange（区分点击和拖拽）
      // 条件：1. 鼠标移动了（hasDraggedRef.current === true）
      //       2. 按下和松开的 token 不同
      //       3. 在同一 sentence 内
      
      // 🔧 只有在 pressToken 存在时才检查 selectRange（避免点击空白处时的多余日志）
      if (selectRangeRef.current && pressTokenRef.current && pressTokenRef.current.tokenIdx != null) {
        // 🔧 调试：打印检查条件（只在有 pressToken 时打印）
        if (addDebugLog) {
          addDebugLog('info', `🔍 [useTokenDrag] MouseUp 检查 - selectRange存在: ${!!selectRangeRef.current}, pressToken存在: ${!!pressTokenRef.current}, tokenIdx: ${pressTokenRef.current?.tokenIdx}`, null)
        }
        const startTokenIdx = pressTokenRef.current.tokenIdx
        const endTokenIdx = tokenInfo && tokenInfo.tokenIdx != null && 
                           tokenInfo.sentenceIdx === pressTokenRef.current.sentenceIdx
                           ? tokenInfo.tokenIdx
                           : pressTokenRef.current.tokenIdx
        
        // 判断是否真的拖拽了：
        // 1. 鼠标移动了（hasDraggedRef.current === true）
        // 2. 或者按下和松开的 token 不同
        const isRealDrag = hasDraggedRef.current || (startTokenIdx !== endTokenIdx)
        
        // 🔧 调试：打印拖拽判断
        if (addDebugLog) {
          addDebugLog('info', `🔍 [useTokenDrag] 拖拽判断 - hasDragged: ${hasDraggedRef.current}, startTokenIdx: ${startTokenIdx}, endTokenIdx: ${endTokenIdx}, isRealDrag: ${isRealDrag}, tokenInfo存在: ${!!tokenInfo}, 同一句子: ${tokenInfo?.sentenceIdx === pressTokenRef.current.sentenceIdx}`, null)
        }
        
        // 只在真正拖拽且在同一 sentence 内时调用 selectRange
        if (isRealDrag && tokenInfo && tokenInfo.sentenceIdx === pressTokenRef.current.sentenceIdx) {
          // 🔧 检查是否有已选择的 token，如果有且在同一句子内，则合并选择
          const hasExistingSelection = selectedTokenIdsRef.current && 
                                      selectedTokenIdsRef.current.size > 0
          const isSameSentence = activeSentenceRef.current === pressTokenRef.current.sentenceIdx
          const shouldMerge = hasExistingSelection && isSameSentence
          
          // 🔧 调试：打印调用 selectRange 的信息
          if (addDebugLog) {
            addDebugLog('info', `✅ [useTokenDrag] 调用 selectRange - 句子: ${pressTokenRef.current.sentenceIdx}, 起始: ${startTokenIdx}, 结束: ${endTokenIdx}, 合并: ${shouldMerge}`, null)
          }
          
          selectRangeRef.current(pressTokenRef.current.sentenceIdx, startTokenIdx, endTokenIdx, shouldMerge)
    } else {
          // 🔧 调试：打印为什么没有调用 selectRange
          if (addDebugLog) {
            addDebugLog('info', `❌ [useTokenDrag] 未调用 selectRange - isRealDrag: ${isRealDrag}, tokenInfo存在: ${!!tokenInfo}, 同一句子: ${tokenInfo?.sentenceIdx === pressTokenRef.current.sentenceIdx}`, null)
          }
        }
      }
      // 🔧 注意：如果 pressToken 不存在（如点击空白处），不打印日志，这是正常情况
      
      // 重置按下时的 token 信息和拖拽标志
      pressTokenRef.current = null
      isMouseDownRef.current = false
      lastHoverTokenRef.current = null
      pressPositionRef.current = null
      hasDraggedRef.current = false
      
      // 清除定时器
      if (pressingLogIntervalRef.current) {
        clearInterval(pressingLogIntervalRef.current)
        pressingLogIntervalRef.current = null
      }
    }
    
    const handleGlobalMouseMove = (e) => {
      // 只有在鼠标按下时才记录 hover 的 token 信息
      if (isMouseDownRef.current && pressTokenRef.current && pressTokenRef.current.tokenIdx != null) {
        // 🔧 检查是否真的拖拽了（鼠标移动超过 5 像素）
        if (pressPositionRef.current) {
          const deltaX = Math.abs(e.clientX - pressPositionRef.current.x)
          const deltaY = Math.abs(e.clientY - pressPositionRef.current.y)
          if (deltaX > 5 || deltaY > 5) {
            hasDraggedRef.current = true
          }
        }
        
        const tokenInfo = detectTokenAtPosition(e.clientX, e.clientY)
        
        // 只有在同一 sentence 内时才记录
        if (tokenInfo && tokenInfo.tokenIdx != null && 
            tokenInfo.sentenceIdx === pressTokenRef.current.sentenceIdx) {
          lastHoverTokenRef.current = {
            ...tokenInfo,
            mouseX: e.clientX,
            mouseY: e.clientY
          }
    } else {
          // 如果不在同一 sentence 内，清空记录
          lastHoverTokenRef.current = null
        }
      }
    }
    
    document.addEventListener('mousedown', handleGlobalMouseDown)
    document.addEventListener('mouseup', handleGlobalMouseUp)
    document.addEventListener('mousemove', handleGlobalMouseMove)
    
    return () => {
      document.removeEventListener('mousedown', handleGlobalMouseDown)
      document.removeEventListener('mouseup', handleGlobalMouseUp)
      document.removeEventListener('mousemove', handleGlobalMouseMove)
      
      // 清理定时器
      if (pressingLogIntervalRef.current) {
        clearInterval(pressingLogIntervalRef.current)
        pressingLogIntervalRef.current = null
      }
    }
  }, [addDebugLog, sentences]) // 🔧 移除 selectRange 依赖，使用 ref 访问

  const handleBackgroundClick = (e) => {
    // 点击背景时清空选择
    const isBackgroundClick = e.target === e.currentTarget || !e.target.closest('[data-token-id]')
    
    if (isBackgroundClick) {
      clearSelection()
    }
  }

  return {
    handleBackgroundClick
  }
}
