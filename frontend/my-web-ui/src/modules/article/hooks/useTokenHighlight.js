import { useRef, useEffect, useState } from 'react'

/**
 * Custom hook to manage token highlighting during drag
 * 只负责 token 高亮，与 useTokenDrag 解耦
 * 使用 OnMousePressed, OnMousePressing, OnMouseEndPress 参数
 */
export function useTokenHighlight({ 
  addDebugLog,
  sentences
}) {
  // 记录鼠标按下时的 token 信息
  const pressTokenRef = useRef(null)
  // 记录鼠标是否按下
  const isMouseDownRef = useRef(false)
  // 记录鼠标移动时的位置和 token 信息（用于 OnMousePressing）
  const lastHoverTokenRef = useRef(null)
  // 定时器引用（用于每 0.5 秒打印一次）
  const pressingLogIntervalRef = useRef(null)
  // 记录鼠标按下时的位置
  const pressPositionRef = useRef(null)
  
  // 高亮状态：当前高亮的 token 范围
  const [highlightedRange, setHighlightedRange] = useState(null)
  
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
      const tokenInfo = detectTokenAtPosition(e.clientX, e.clientY)
      
      // 记录按下时的 token 信息和位置
      pressTokenRef.current = tokenInfo
      isMouseDownRef.current = true
      pressPositionRef.current = { x: e.clientX, y: e.clientY }
      
      // OnMousePressed: 只在 Token 索引不为空时打印
      if (addDebugLog && tokenInfo && tokenInfo.tokenIdx != null) {
        const logMessage = `OnMousePressed - X: ${e.clientX}, Y: ${e.clientY} | 句子索引: ${tokenInfo.sentenceIdx}, Token索引: ${tokenInfo.tokenIdx}`
        addDebugLog('info', logMessage, null)
      }
      
      // 🔧 如果按下时有 token，立即开启高亮（单个 token）
      if (tokenInfo && tokenInfo.tokenIdx != null) {
        setHighlightedRange({
          sentenceIdx: tokenInfo.sentenceIdx,
          startTokenIdx: tokenInfo.tokenIdx,
          endTokenIdx: tokenInfo.tokenIdx
        })
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
      const tokenInfo = detectTokenAtPosition(e.clientX, e.clientY)
      
      // OnMouseEndPress: 只在 Token 索引不为空且在同一 sentence 内时打印
      if (addDebugLog && tokenInfo && tokenInfo.tokenIdx != null && 
          pressTokenRef.current && pressTokenRef.current.tokenIdx != null &&
          tokenInfo.sentenceIdx === pressTokenRef.current.sentenceIdx) {
        const logMessage = `OnMouseEndPress - X: ${e.clientX}, Y: ${e.clientY} | 句子索引: ${tokenInfo.sentenceIdx}, Token索引: ${tokenInfo.tokenIdx}`
        addDebugLog('info', logMessage, null)
      }
      
      // 清除高亮
      setHighlightedRange(null)
      
      // 重置按下时的 token 信息
      pressTokenRef.current = null
      isMouseDownRef.current = false
      lastHoverTokenRef.current = null
      pressPositionRef.current = null
      
      // 清除定时器
      if (pressingLogIntervalRef.current) {
        clearInterval(pressingLogIntervalRef.current)
        pressingLogIntervalRef.current = null
      }
    }
    
    const handleGlobalMouseMove = (e) => {
      // 只有在鼠标按下时才更新高亮
      if (isMouseDownRef.current && pressTokenRef.current && pressTokenRef.current.tokenIdx != null) {
        const tokenInfo = detectTokenAtPosition(e.clientX, e.clientY)
        
        // 只有在同一 sentence 内时才更新高亮
        if (tokenInfo && tokenInfo.tokenIdx != null && 
            tokenInfo.sentenceIdx === pressTokenRef.current.sentenceIdx) {
          lastHoverTokenRef.current = {
            ...tokenInfo,
            mouseX: e.clientX,
            mouseY: e.clientY
          }
          
          // 更新高亮范围
          const startTokenIdx = pressTokenRef.current.tokenIdx
          const endTokenIdx = tokenInfo.tokenIdx
          const rangeStart = Math.min(startTokenIdx, endTokenIdx)
          const rangeEnd = Math.max(startTokenIdx, endTokenIdx)
          
          setHighlightedRange({
            sentenceIdx: tokenInfo.sentenceIdx,
            startTokenIdx: rangeStart,
            endTokenIdx: rangeEnd
          })
        } else {
          // 如果不在同一 sentence 内，清空高亮
          lastHoverTokenRef.current = null
          setHighlightedRange(null)
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
  }, [addDebugLog, sentences])

  return {
    highlightedRange // 返回高亮范围，供组件使用
  }
}

