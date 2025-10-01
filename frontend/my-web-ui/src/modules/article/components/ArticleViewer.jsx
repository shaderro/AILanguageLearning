import { useMemo, useRef, useState, useEffect } from 'react'
import { useArticle } from '../../../hooks/useApi'
import { apiService } from '../../../services/api'
import { useChatEvent } from '../contexts/ChatEventContext'

// InlineExplanation 组件 - 用于显示hover时的解释
function InlineExplanation({ explanation = "This is a quick explanation", token = null, sentenceBody = "", textId = 1, sentenceId = 1 }) {
  const { sendMessageToChat, triggerKnowledgeToast } = useChatEvent()
  const [isConverting, setIsConverting] = useState(false)

  // 测试token转vocab功能
  const testTokenToVocab = async (tokenData) => {
    if (!tokenData || typeof tokenData !== 'object') {
      console.warn('⚠️ [Frontend] Invalid token data for conversion')
      return
    }

    setIsConverting(true)
    console.log('🚀 [Frontend] 开始测试token转vocab功能...')
    console.log('📥 [Frontend] 原始Token数据:', tokenData)
    console.log('📋 [Frontend] 上下文信息:')
    console.log('  - Sentence Body:', sentenceBody)
    console.log('  - Text ID:', textId)
    console.log('  - Sentence ID:', sentenceId)

    try {
      const requestData = {
        token: {
          token_body: tokenData.token_body || tokenData.token || '',
          token_type: tokenData.token_type || 'text',
          difficulty_level: tokenData.difficulty_level || 'hard',
          global_token_id: tokenData.global_token_id || 1,
          sentence_token_id: tokenData.sentence_token_id || 1
        }
        // 注意：sentence 相关信息由后端从 session_state 读取，无需前端传入
      }

      console.log('📤 [Frontend] 发送请求数据 (sentence 从后端 session_state 读取):', JSON.stringify(requestData, null, 2))

      const response = await fetch('http://localhost:8000/api/test-token-to-vocab', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      })

      console.log('📡 [Frontend] 收到响应状态:', response.status, response.statusText)
      
      const result = await response.json()
      console.log('📥 [Frontend] 收到响应数据:', result)

      if (result.success && result.data) {
        console.log('✅ [Frontend] Token转Vocab成功!')
        console.log('📊 [Frontend] Vocab数据详情:')
        console.log('  - Vocab ID:', result.data.vocab_id)
        console.log('  - Vocab Body:', result.data.vocab_body)
        console.log('  - Explanation:', result.data.explanation)
        console.log('  - Source:', result.data.source)
        console.log('  - Examples count:', result.data.examples?.length || 0)
        console.log('  - Saved to file:', result.saved_to_file)
        
        console.log('🎯 [Frontend] 完整Vocab对象:')
        console.log(JSON.stringify(result.data, null, 2))
        
        // 提示用户刷新数据
        if (result.saved_to_file) {
          console.log('💡 [Frontend] 建议: 点击Word页面的刷新按钮查看新词汇!')
        }
        
        // 将 AI 解释发送到聊天框
        const explanation = result.data.explanation || ''
        const contextExplanation = result.data.examples?.[0]?.context_explanation || ''
        const aiResponse = explanation + (contextExplanation ? '\n\n' + contextExplanation : '')
        
        if (aiResponse && sendMessageToChat) {
          console.log('💬 [Frontend] Sending AI explanation to chat:', aiResponse.substring(0, 100) + '...')
          // 不传 quotedText，让它作为 AI 响应直接显示
          sendMessageToChat(aiResponse, null)
          // 触发 Toast：提示该词汇已总结
          if (triggerKnowledgeToast) {
            const vocabBody = result?.data?.vocab_body || tokenText || ''
            triggerKnowledgeToast(`词汇: ${vocabBody}`)
          }
        }
      } else {
        console.error('❌ [Frontend] 转换失败:', result.error)
        if (result.traceback) {
          console.error('🔍 [Frontend] 后端错误详情:', result.traceback)
        }
      }
    } catch (error) {
      console.error('💥 [Frontend] 请求失败:', error)
      console.error('🔍 [Frontend] 错误详情:', error.message)
    } finally {
      setIsConverting(false)
      console.log('🏁 [Frontend] Token转Vocab流程结束')
    }
  }

  const handleDetailClick = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    console.log('🎯 [Frontend] Detail按钮被点击!')
    
    // Debug: trace token resolution path
    console.log('🔍 [Frontend] Token解析路径追踪:')
    console.log('  - 原始token:', token)
    console.log('  - token类型:', typeof token)
    
    if (token && typeof token === 'object') {
      console.log('  - token.token_body:', token?.token_body)
      console.log('  - token.token:', token?.token)
      console.log('  - 可用键:', Object.keys(token))
    }

    const tokenText = typeof token === 'string' ? token : (token?.token_body ?? token?.token ?? '')
    console.log('📝 [Frontend] 计算得出的tokenText:', tokenText)
    
    if (!tokenText) {
      console.warn('⚠️ [Frontend] tokenText为空，进行备用检查...', {
        tokenStringFallback: String(token ?? ''),
      })
      return
    }

    // 1) 先把用户意图显示到聊天（带引用 token）
    const question = "请为这个词和它在句中的用法提供详细解释"
    console.log('💬 [Frontend] 发送用户提问到聊天:', tokenText)
    sendMessageToChat(question, tokenText)

    // 2) 走 token→vocab 专用链路（不调用 /api/chat）
    try {
      console.log('🧪 [Frontend] 使用 token→vocab 专用接口，获取解释并回显到聊天')
      await testTokenToVocab(token)
    } catch (error) {
      console.error('💥 [Frontend] Detail explanation error:', error)
    }
  }

  return (
    <div className="absolute top-full left-0 z-10 mt-1">
      <div className="px-2 py-1 text-xs bg-gray-100 text-gray-500 border border-gray-300 rounded shadow-lg">
        <div className="mb-1">{explanation}</div>
        <button
          onClick={handleDetailClick}
          disabled={isConverting}
          className={`text-xs underline cursor-pointer ${
            isConverting 
              ? 'text-gray-400 cursor-not-allowed' 
              : 'text-blue-600 hover:text-blue-800'
          }`}
        >
          {isConverting ? '🧪 转换中...' : 'detail explanation with AI'}
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
        <InlineExplanation 
          explanation="This is a test explanation" 
          token={token}
          sentenceBody=""
          textId={1}
          sentenceId={1}
        />
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

  // 当文章 ID 改变时，设置第一个句子为当前句子上下文
  // 注意：只监听 articleId，不监听 data/sentences，避免数据刷新时重复设置
  useEffect(() => {
    if (data?.data && sentences.length > 0) {
      const firstSentence = sentences[0]
      if (firstSentence) {
        const sentenceData = {
          text_id: data.data.text_id || 1,
          sentence_id: firstSentence.sentence_id || 1,
          sentence_body: firstSentence.sentence_body || ''
        }
        console.log('📄 [Frontend] Article changed, setting first sentence as context:', sentenceData)
        apiService.session.setSentence(sentenceData)
          .then(response => {
            console.log('✅ [Frontend] Session sentence set response:', response)
          })
          .catch(error => {
            console.error('❌ [Frontend] Failed to set session sentence:', error)
          })
      }
    }
  }, [articleId])

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

  const emitSelection = (set, lastTokenText = '', lastTokenObj = null) => {
    setSelectedTokenIds(set)
    
    // 打印调用栈，查看是谁在调用
    const stack = new Error().stack
    const caller = stack.split('\n')[2]?.trim() || 'unknown'
    
    console.log('📌 [Frontend] emitSelection called', {
      setSize: set.size,
      lastTokenText,
      hasLastTokenObj: !!lastTokenObj,
      activeSentenceIndex: activeSentenceRef.current,
      calledFrom: caller
    })
    
    // 更新选中的token对象并同步到 session state（使用优化的批量接口）
    if (set.size === 1) {
      console.log('➡️ [Frontend] Single token selection branch')
      const selectedTokenObj = getSelectedTokenObject(set)
      console.log('📍 [Frontend] selectedTokenObj:', selectedTokenObj)
      setSelectedToken(selectedTokenObj)
      
      // 同步设置 session state 的 selected_token（单选）
      if (selectedTokenObj) {
        const sIdx = activeSentenceRef.current
        const sentence = sentences[sIdx]
        
        if (sentence) {
          const sentenceData = {
            text_id: data?.data?.text_id || 1,
            sentence_id: sentence.sentence_id || sIdx + 1,
            sentence_body: sentence.sentence_body || ''
          }
          
          const tokenData = {
            token_body: selectedTokenObj.token_body || '',
            global_token_id: selectedTokenObj.global_token_id,
            sentence_token_id: selectedTokenObj.sentence_token_id,
            token_type: selectedTokenObj.token_type || 'text',
            difficulty_level: selectedTokenObj.difficulty_level
          }
          
          console.log('🎯 [Frontend] Single token selected, updating context (batch):', {
            sentence: sentenceData.sentence_id,
            token: tokenData.token_body
          })
          
          apiService.session.updateContext({
            sentence: sentenceData,
            token: tokenData
          })
            .then(response => {
              console.log('✅ [Frontend] Session context updated:', response)
            })
            .catch(error => {
              console.error('❌ [Frontend] Failed to update session context:', error)
            })
        }
      }
    } else if (set.size > 1) {
      console.log('➡️ [Frontend] Multiple tokens selection branch')
      // 多选：使用最后添加的 token 更新到 session state
      setSelectedToken(null)
      // 如果传入了 lastTokenObj，使用它；否则尝试获取
      const tokenToUpdate = lastTokenObj || getSelectedTokenObject(set)
      console.log('📍 [Frontend] tokenToUpdate:', tokenToUpdate)
      
      if (tokenToUpdate) {
        const sIdx = activeSentenceRef.current
        const sentence = sentences[sIdx]
        
        if (sentence) {
          const sentenceData = {
            text_id: data?.data?.text_id || 1,
            sentence_id: sentence.sentence_id || sIdx + 1,
            sentence_body: sentence.sentence_body || ''
          }
          
          const tokenData = {
            token_body: tokenToUpdate.token_body || '',
            global_token_id: tokenToUpdate.global_token_id,
            sentence_token_id: tokenToUpdate.sentence_token_id,
            token_type: tokenToUpdate.token_type || 'text',
            difficulty_level: tokenToUpdate.difficulty_level
          }
          
          console.log('🎯 [Frontend] Multiple tokens selected, updating context (batch):', {
            sentence: sentenceData.sentence_id,
            token: tokenData.token_body
          })
          
          apiService.session.updateContext({
            sentence: sentenceData,
            token: tokenData
          })
            .then(response => {
              console.log('✅ [Frontend] Session context updated:', response)
            })
            .catch(error => {
              console.error('❌ [Frontend] Failed to update session context:', error)
            })
        }
      }
    } else {
      console.log('➡️ [Frontend] No selection (cleared) branch')
      // 取消选择：清空 session state 的 selected_token
      setSelectedToken(null)
      console.log('🔄 [Frontend] Selection cleared')
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
    
    // 移除这里的 setSelectedToken，因为 emitSelection 内部会设置
    // 避免触发重复的副作用
    
    // 传入 token 作为最后选中的对象，确保多选时也能更新 session state
    emitSelection(next, token?.token_body ?? '', token)
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
    
    // 移除这里的 emitSelection 调用
    // mouseDown 只初始化拖拽状态，不触发选择
    // 真正的选择由 onClick（无拖拽）或 onMouseUp（拖拽结束）触发
    const startUid = getTokenId(token)
    if (startUid) {
      const next = new Set(selectionBeforeDragRef.current)
      next.add(startUid)
      selectionBeforeDragRef.current = new Set(next)
    }
    suppressNextClickRef.current = true
    setTimeout(() => { suppressNextClickRef.current = false }, 0)
  }

  const handleMouseEnterToken = (sIdx, tIdx, token) => {
    if (!isDraggingRef.current) return
    if (dragSentenceIndexRef.current !== sIdx) return
    if (!token?.selectable) return

    hasMovedRef.current = true

    // 拖拽时更新视觉反馈（高亮），但不触发 session state 设置
    // 只更新本地 selectedTokenIds，不调用 emitSelection
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
    
    // 只更新视觉状态，不触发 emitSelection（避免重复调用 session state）
    setSelectedTokenIds(rangeSet)
  }

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current) return
    const sIdx = activeSentenceRef.current
    if (sIdx == null) return

    const start = dragStartPointRef.current
    const current = { x: e.clientX, y: e.clientY }
    
    // 检查是否真正移动了（阈值 5 像素）
    const dx = Math.abs(current.x - start.x)
    const dy = Math.abs(current.y - start.y)
    if (dx < 5 && dy < 5) {
      return
    }
    
    hasMovedRef.current = true
    // mouseMove 只用于更新视觉反馈，不调用 emitSelection
    // 真正的选择确认在 mouseUp 时进行
  }

  const handleMouseUp = (e) => {
    const wasDragging = isDraggingRef.current || wasDraggingRef.current
    
    // 如果是拖拽操作且有移动，在这里统一处理选择
    if (wasDragging && hasMovedRef.current) {
      const sIdx = activeSentenceRef.current
      if (sIdx != null) {
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
        let lastToken = null
        if (coveredIdx.length > 0) {
          const minIdx = Math.min(...coveredIdx)
          const maxIdx = Math.max(...coveredIdx)
          for (let i = minIdx; i <= maxIdx; i++) {
            const tk = tokens[i]
            if (tk && typeof tk === 'object' && tk.selectable) {
              const id = getTokenId(tk)
              if (id) rangeSet.add(id)
              lastText = tk?.token_body ?? lastText
              lastToken = tk
            }
          }
        }

        console.log('🖱️ [Frontend] MouseUp after drag, finalizing selection')
        emitSelection(rangeSet, lastText, lastToken)
      }
    }
    
    if (wasDragging) {
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
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto">
        <div className="text-gray-500">Loading article...</div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto">
        <div className="text-red-500">Failed to load: {String(error?.message || error)}</div>
      </div>
    )
  }

  return (
    <div
      className="flex-1 bg-white rounded-lg border border-gray-200 p-4 overflow-auto"
      onClick={handleBackgroundClick}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      <div className="space-y-[0.66rem] leading-[1.33] text-gray-900">
        {sentences.map((sentence, sIdx) => (
          <div
            key={`s-${sIdx}`}
            className={`select-none ${activeSentenceIndex === sIdx ? "outline outline-1 outline-gray-300 rounded-md outline-offset-1" : ""}`}
            data-sentence="1"
          >
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
                      token={t}
                      sentenceBody={sentence?.sentence_body || ""}
                      textId={data?.data?.text_id ?? 1}
                      sentenceId={sentence?.sentence_id || sIdx + 1}
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
