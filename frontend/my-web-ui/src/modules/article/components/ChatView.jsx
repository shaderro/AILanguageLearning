import { useState, useRef, useEffect, useMemo, useLayoutEffect } from 'react'
import ToastNotice from './ToastNotice'
import SuggestedQuestions from './SuggestedQuestions'
import { useChatEvent } from '../contexts/ChatEventContext'
import { useTranslationDebug } from '../../../contexts/TranslationDebugContext'
import { useRefreshData } from '../../../hooks/useApi'
import { colors } from '../../../design-tokens'

// 🔧 本地持久化 - 最多存 200 条跨文章消息
const LS_KEY_CHAT_MESSAGES_ALL = 'chat_messages_all'

const reviveMessages = (raw) => {
  if (!Array.isArray(raw)) return []
  return raw.map(m => ({
    ...m,
    timestamp: m?.timestamp ? new Date(m.timestamp) : new Date()
  }))
}

const loadAllMessagesFromLS = () => {
  try {
    const raw = JSON.parse(localStorage.getItem(LS_KEY_CHAT_MESSAGES_ALL) || '[]')
    return reviveMessages(raw)
  } catch (e) {
    console.warn('⚠️ [ChatView] 读取本地消息失败，将忽略本地缓存', e)
    return []
  }
}

const saveAllMessagesToLS = (messagesAll) => {
  try {
    localStorage.setItem(LS_KEY_CHAT_MESSAGES_ALL, JSON.stringify(messagesAll))
  } catch (e) {
    console.warn('⚠️ [ChatView] 写入本地消息失败，已忽略', e)
  }
}

export default function ChatView({ 
  quotedText, 
  onClearQuote, 
  disabled = false, 
  hasSelectedToken = false, 
  selectedTokenCount = 1, 
  selectionContext = null, 
  markAsAsked = null,  // 旧API（备用，向后兼容）
  createVocabNotation = null,  // 新API（优先使用）
  refreshAskedTokens = null, 
  refreshGrammarNotations = null, 
  articleId = null, 
  hasSelectedSentence = false, 
  selectedSentence = null,
  // 新增：实时缓存更新函数
  addGrammarNotationToCache = null,
  addVocabNotationToCache = null,
  addGrammarRuleToCache = null,
  addVocabExampleToCache = null,
  // 🔧 新增：isProcessing 状态管理（从父组件传入，用于同步状态）
  isProcessing: externalIsProcessing = null,
  onProcessingChange = null
}) {
  const { pendingMessage, clearPendingMessage, pendingContext, clearPendingContext, pendingToast, clearPendingToast } = useChatEvent()
  const { refreshGrammar, refreshVocab } = useRefreshData()  // 🔧 添加自动刷新功能
  const { addLog } = useTranslationDebug()  // 🔧 添加调试日志
  
  // 🔧 使用 useRef 跟踪组件挂载，用于调试
  const mountRef = useRef(false)
  const componentInstanceIdRef = useRef(Math.random().toString(36).substring(7))
  
  // 🔧 消息 ID 生成器，确保唯一性
  const messageIdCounterRef = useRef(0)
  const generateMessageId = () => {
    messageIdCounterRef.current += 1
    return Date.now() + Math.random() + messageIdCounterRef.current
  }
  
  // 🔧 使用 ref 保存 messages，避免组件重新挂载时丢失
  // 🔧 使用全局变量存储，确保跨组件实例共享
  if (!window.chatViewMessagesRef) {
    window.chatViewMessagesRef = [
    { id: 1, text: "你好！我是聊天助手，有什么可以帮助你的吗？", isUser: false, timestamp: new Date() }
    ]
  }
  const messagesRef = useRef(window.chatViewMessagesRef)
  
  useEffect(() => {
    const wasMounted = mountRef.current
    const instanceId = componentInstanceIdRef.current
    
    if (!wasMounted) {
      mountRef.current = true
      addLog('info', '🔄 [ChatView] 组件已挂载/重新挂载', { instanceId })
      // 🔧 如果组件重新挂载，从全局ref恢复messages
      if (window.chatViewMessagesRef && window.chatViewMessagesRef.length > 0) {
        addLog('info', '🔄 [ChatView] 检测到组件重新挂载，从全局ref恢复 messages', {
          instanceId,
          count: window.chatViewMessagesRef.length,
          messages: window.chatViewMessagesRef.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser }))
        })
        // 🔧 恢复messages状态（使用函数式更新，确保基于最新状态）
        setMessages(prev => {
          // 🔧 使用深拷贝确保引用不会丢失，但保留 Date 对象
          const globalRef = window.chatViewMessagesRef ? window.chatViewMessagesRef.map(msg => ({
            ...msg,
            timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
          })) : null
          
          // 🔧 关键修复：如果全局ref中的消息数量更多或相等，使用全局ref（因为全局ref是最新的）
          // 这样可以确保即使组件重新挂载，也能恢复最新的消息
          if (globalRef && globalRef.length >= prev.length) {
            // 🔧 不在渲染期间调用 addLog，使用 setTimeout 延迟执行
            setTimeout(() => {
              addLog('info', '🔄 [ChatView] 从全局ref恢复 messages（全局ref有更多或相等数量的消息）', {
                instanceId,
                prevLength: prev.length,
                globalRefLength: globalRef.length,
                globalRefMessages: globalRef.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser }))
              })
            }, 0)
            messagesRef.current = globalRef
            return globalRef
          } else {
            setTimeout(() => {
              addLog('info', '🔄 [ChatView] 保持当前 messages（当前状态已是最新）', {
                instanceId,
                prevLength: prev.length,
                globalRefLength: globalRef?.length || 0,
                globalRefMessages: globalRef?.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser })) || []
              })
            }, 0)
            return prev
          }
        })
      }
    } else {
      // 🔧 组件已挂载，但可能因为某些原因重新渲染，确保状态同步
      // 🔧 减少日志输出，避免频繁打印
      if (window.chatViewMessagesRef && window.chatViewMessagesRef.length > 0) {
        setMessages(prev => {
          // 🔧 使用深拷贝确保引用不会丢失，但保留 Date 对象
          const globalRef = window.chatViewMessagesRef.map(msg => ({
            ...msg,
            timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
          }))
          
          // 🔧 关键修复：如果全局ref中的消息数量更多或相等，同步到状态（因为全局ref是最新的）
          if (globalRef.length >= prev.length) {
            // 🔧 不在渲染期间调用 addLog，使用 setTimeout 延迟执行
            setTimeout(() => {
              addLog('info', '🔄 [ChatView] 同步全局ref到状态（检测到更多或相等数量的消息）', {
                instanceId,
                prevLength: prev.length,
                globalRefLength: globalRef.length,
                globalRefMessages: globalRef.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser }))
              })
            }, 0)
            messagesRef.current = globalRef
            return globalRef
          }
          return prev
        })
      }
    }
  }, [addLog])
  
  const [messages, setMessages] = useState(() => {
    const globalRef = window.chatViewMessagesRef || []
    // 从本地存储加载全量，按文章筛选
    const allFromLS = loadAllMessagesFromLS()
    console.log('🔄 [ChatView] 从 localStorage 加载消息', {
      totalInLS: allFromLS.length,
      currentArticleId: articleId,
      allArticleIds: [...new Set(allFromLS.map(m => m.articleId).filter(Boolean))]
    })
    
    // 🔧 如果有 articleId，优先加载该文章的消息；否则加载所有消息（包括没有 articleId 的）
    // 🔧 修复：处理 articleId 类型不匹配问题（字符串 vs 数字）
    const normalizedArticleId = articleId ? String(articleId) : null
    
    // 🔧 详细分析所有消息的 articleId 情况
    const articleIdAnalysis = {
      total: allFromLS.length,
      withArticleId: allFromLS.filter(m => m.articleId).length,
      withoutArticleId: allFromLS.filter(m => !m.articleId).length,
      articleIdTypes: [...new Set(allFromLS.filter(m => m.articleId).map(m => typeof m.articleId))],
      uniqueArticleIds: [...new Set(allFromLS.filter(m => m.articleId).map(m => String(m.articleId)))],
      matchingCount: normalizedArticleId ? allFromLS.filter(m => m.articleId && String(m.articleId) === normalizedArticleId).length : 0
    }
    
    const fromLSForArticle = normalizedArticleId
      ? allFromLS
          .filter(m => {
            // 🔧 匹配逻辑：没有 articleId 的消息 OR articleId 匹配（支持字符串和数字比较）
            if (!m.articleId) return false // 🔧 修复：如果没有 articleId，不应该加载（因为我们要加载特定文章的消息）
            const mArticleId = String(m.articleId)
            return mArticleId === normalizedArticleId
          })
          .map(({ articleId: _aid, ...rest }) => rest)
          .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)) // 渲染按时间正序
      : allFromLS
          .filter(m => !m.articleId) // 如果没有 articleId，只加载没有 articleId 的消息
          .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    
    console.log('🔍 [ChatView] 消息筛选结果', {
      totalInLS: allFromLS.length,
      normalizedArticleId: normalizedArticleId,
      filteredCount: fromLSForArticle.length,
      articleIdAnalysis: articleIdAnalysis,
      sampleArticleIds: allFromLS.slice(0, 5).map(m => ({ 
        id: m.id, 
        articleId: m.articleId, 
        articleIdType: typeof m.articleId,
        articleIdString: m.articleId ? String(m.articleId) : null,
        matches: normalizedArticleId ? (m.articleId && String(m.articleId) === normalizedArticleId) : false
      }))
    })
    
    const initialMessages = (fromLSForArticle.length > 0 ? fromLSForArticle : globalRef) || [
      { id: 1, text: "你好！我是聊天助手，有什么可以帮助你的吗？", isUser: false, timestamp: new Date() }
    ]
    console.log('🔄 [ChatView] messages 状态初始化', { 
      count: initialMessages.length,
      hasGlobalRef: !!globalRef?.length,
      globalRefLength: globalRef?.length || 0,
      globalRefIds: globalRef?.map(m => m.id) || [],
      initialMessageIds: initialMessages.map(m => m.id),
      fromLS: fromLSForArticle.length,
      articleId: articleId,
      normalizedArticleId: normalizedArticleId
    })
    messagesRef.current = initialMessages
    window.chatViewMessagesRef = initialMessages
    return initialMessages
  })
  
  // 🔧 重构：使用 useEffect 监听全局 ref 的变化，确保状态同步
  useEffect(() => {
    const checkAndSyncMessages = () => {
      const globalRef = window.chatViewMessagesRef
      const currentStateLength = messages.length
      const globalRefLength = globalRef?.length || 0
      
      // 🔧 如果全局 ref 中的消息数量更多，同步到状态
      if (globalRefLength > currentStateLength) {
        console.log('🔄 [ChatView] 检测到全局 ref 有更多消息，同步到状态', {
          currentStateLength,
          globalRefLength,
          currentStateIds: messages.map(m => m.id),
          globalRefIds: globalRef.map(m => m.id)
        })
        
        const globalRefCopy = globalRef.map(msg => ({
          ...msg,
          timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
        }))
        
        setMessages(globalRefCopy)
        messagesRef.current = globalRefCopy
      } else if (currentStateLength > globalRefLength) {
        // 🔧 如果状态中的消息数量更多，同步到全局 ref
        const messagesCopy = messages.map(msg => ({
          ...msg,
          timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
        }))
        messagesRef.current = messagesCopy
        window.chatViewMessagesRef = messagesCopy
        addLog('info', '🔄 [ChatView] 同步 messages 到全局 ref（状态有更多消息）', {
          messagesCount: messagesCopy.length,
          globalRefLength: globalRefLength,
          messages: messagesCopy.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser }))
        })
      } else {
        // 🔧 消息数量相等，只更新 ref
        const messagesCopy = messages.map(msg => ({
          ...msg,
          timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
        }))
        messagesRef.current = messagesCopy
      }
    }
    
    // 🔧 使用 setTimeout 延迟执行，避免在 useEffect 中直接调用 setMessages 导致无限循环
    const timeoutId = setTimeout(checkAndSyncMessages, 0)
    return () => clearTimeout(timeoutId)
  }, [messages, addLog])

  // 🔧 将消息持久化到 localStorage（全局最多 200 条，带 articleId）
  useEffect(() => {
    // 🔧 即使 articleId 为空，也保存消息（使用当前 articleId 或保留原有的 articleId）
    const all = loadAllMessagesFromLS()
    // 去重：移除与当前 messages 相同 id 的旧记录
    const withoutDup = all.filter(m => !messages.some(n => n.id === m.id))
    // 🔧 统一 articleId 格式为字符串，确保类型一致
    const normalizedArticleId = articleId ? String(articleId) : null
    const merged = [
      ...withoutDup,
      ...messages.map(m => ({
        ...m,
        // 🔧 如果当前消息没有 articleId，使用传入的 articleId；如果都没有，保留 undefined
        // 🔧 统一转换为字符串格式
        articleId: m.articleId ? String(m.articleId) : (normalizedArticleId || undefined),
        timestamp: m.timestamp instanceof Date ? m.timestamp.toISOString() : m.timestamp
      }))
    ]
    merged.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    const trimmed = merged.slice(0, 200)
    saveAllMessagesToLS(trimmed)
    console.log('💾 [ChatView] 已保存消息到 localStorage', {
      totalMessages: trimmed.length,
      currentArticleId: articleId,
      normalizedArticleId: normalizedArticleId,
      messagesWithArticleId: trimmed.filter(m => m.articleId).length,
      sampleArticleIds: trimmed.slice(0, 3).map(m => ({ id: m.id, articleId: m.articleId }))
    })
  }, [messages, articleId])
  
  // 🔧 新增：定期检查全局 ref 的变化（用于处理组件重新挂载的情况）
  useEffect(() => {
    const intervalId = setInterval(() => {
      const globalRef = window.chatViewMessagesRef
      const currentStateLength = messages.length
      const globalRefLength = globalRef?.length || 0
      
      if (globalRefLength > currentStateLength) {
        console.log('🔄 [ChatView] 定期检查：检测到全局 ref 有更多消息，同步到状态', {
          currentStateLength,
          globalRefLength,
          currentStateIds: messages.map(m => m.id),
          globalRefIds: globalRef.map(m => m.id)
        })
        
        const globalRefCopy = globalRef.map(msg => ({
          ...msg,
          timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
        }))
        
        setMessages(globalRefCopy)
        messagesRef.current = globalRefCopy
      }
    }, 100) // 每100ms检查一次
    
    return () => clearInterval(intervalId)
  }, [messages])
  // 🔧 重构：使用全局 ref 持久化 toasts，避免组件重新挂载导致状态丢失
  if (!window.chatViewToastsRef) {
    window.chatViewToastsRef = []
  }
  const toastsRef = useRef(window.chatViewToastsRef)
  
  // 🔧 重构：多实例 toast 栈，从全局 ref 初始化
  const [toasts, setToasts] = useState(() => {
    const initialToasts = window.chatViewToastsRef || []
    console.log('🔄 [ChatView] toasts 状态初始化', { count: initialToasts.length })
    // 🔧 注意：这里不能使用 toastsRef.current，因为 toastsRef 还没有初始化
    // 直接使用 window.chatViewToastsRef，toastsRef 会在 useEffect 中同步
    return initialToasts
  })
  
  // 🔧 初始化 toastsRef（在 toasts 状态初始化后）
  useEffect(() => {
    if (toastsRef.current.length !== toasts.length) {
      toastsRef.current = toasts
      window.chatViewToastsRef = toasts
    }
  }, []) // 只在组件挂载时执行一次
  
  const [inputText, setInputText] = useState('')
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const messagesEndRef = useRef(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(false)
  const scrollContainerRef = useRef(null)
  const scrollPositionRef = useRef(0)
  // 🔧 新增：跟踪 main assistant 是否正在处理
  // 🔧 如果父组件传入了外部状态，使用外部状态；否则使用内部状态
  const [internalIsProcessing, setInternalIsProcessing] = useState(false)
  const isProcessing = externalIsProcessing !== null ? externalIsProcessing : internalIsProcessing
  const setIsProcessing = onProcessingChange || setInternalIsProcessing
  // 移除展开状态相关代码

  // 🔧 保持 Chat 滚动位置，避免点击/重渲染时跳到顶部
  useEffect(() => {
    const sc = scrollContainerRef.current
    if (!sc) return
    const onScroll = () => {
      scrollPositionRef.current = sc.scrollTop
    }
    sc.addEventListener('scroll', onScroll, { passive: true })
    return () => sc.removeEventListener('scroll', onScroll)
  }, [])

  useLayoutEffect(() => {
    const sc = scrollContainerRef.current
    if (sc && typeof scrollPositionRef.current === 'number') {
      sc.scrollTop = scrollPositionRef.current
    }
  })

  // 新增：自动滚动到底部的函数（仅在需要自动滚动时）
  const scrollToBottom = () => {
    if (shouldAutoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  // 状态冲突检测（移除详细日志，只保留警告）
  useEffect(() => {
    // 状态冲突检测
    if (hasSelectedToken && hasSelectedSentence) {
      console.warn('⚠️ [ChatView] State conflict detected: both token and sentence selected!')
    }
  }, [hasSelectedToken, hasSelectedSentence])

  // 抽取：显示"知识点已加入"提示卡片
  const showKnowledgeToast = (currentKnowledge) => {
    console.log('🍞 [Toast Debug] showKnowledgeToast 被调用，参数:', currentKnowledge)
    const text = String(currentKnowledge ?? '').trim()
    const msg = `${text} 知识点已总结并加入列表`
    console.log('🍞 [Toast Debug] 生成的 toast 消息:', msg)
    
    // 🔧 重构：先更新全局 ref，再更新状态，确保即使组件重新挂载也能恢复
    const id = Date.now() + Math.random()
    const currentToasts = toastsRef.current || window.chatViewToastsRef || []
    const slot = currentToasts.length
    const newToast = { id, message: msg, slot }
    const newToasts = [...currentToasts, newToast]
    
    // 先更新全局 ref
    toastsRef.current = newToasts
    window.chatViewToastsRef = newToasts
    
    console.log('🍞 [Toast Debug] 添加 toast 到栈', {
      当前栈长度: currentToasts.length,
      新栈长度: newToasts.length,
      新toast: newToast,
      所有toasts: newToasts,
      全局ref已更新: true
    })
    
    // 然后更新状态（使用函数式更新确保基于最新状态）
    setToasts(prev => {
      console.log('🍞 [Toast Debug] setToasts 回调执行', {
        回调接收到的prev: prev,
        要设置的新值: newToasts
      })
      // 如果 prev 和 newToasts 不同，返回 newToasts
      if (JSON.stringify(prev) !== JSON.stringify(newToasts)) {
        return newToasts
      }
      return prev
    })
    
    console.log('🍞 [Toast Debug] 已调用 setToasts（函数式更新）')
    
    // 兼容旧的单实例
    setToastMessage(msg)
    setShowToast(true)
  }

  // 🔧 同步 toasts 到全局 ref
  useEffect(() => {
    toastsRef.current = toasts
    window.chatViewToastsRef = toasts
    console.log('🔄 [ChatView] toasts 状态已同步到全局 ref', { 
      count: toasts.length,
      toastIds: toasts.map(t => t.id.toString().slice(-4)),
      toasts: toasts
    })
  }, [toasts])
  
  // 🔧 定期检查全局 ref，确保状态同步（处理组件重新挂载的情况）
  useEffect(() => {
    const intervalId = setInterval(() => {
      const globalToasts = window.chatViewToastsRef || []
      if (globalToasts.length !== toasts.length || JSON.stringify(globalToasts) !== JSON.stringify(toasts)) {
        console.log('🔄 [ChatView] 定期检查：检测到全局 ref 有更新，恢复 toasts', {
          当前toasts数量: toasts.length,
          全局toasts数量: globalToasts.length,
          当前toasts: toasts,
          全局toasts: globalToasts
        })
        setToasts(globalToasts)
        toastsRef.current = globalToasts
      }
    }, 100) // 每100ms检查一次
    
    return () => clearInterval(intervalId)
  }, [toasts])
  
  // 🔧 组件重新挂载时，从全局 ref 恢复 toasts
  useEffect(() => {
    const globalToasts = window.chatViewToastsRef || []
    console.log('🔄 [ChatView] 检查是否需要从全局 ref 恢复 toasts', {
      当前toasts数量: toasts.length,
      全局toasts数量: globalToasts.length,
      当前toasts: toasts,
      全局toasts: globalToasts
    })
    if (globalToasts.length > toasts.length || JSON.stringify(globalToasts) !== JSON.stringify(toasts)) {
      console.log('🔄 [ChatView] 检测到全局 ref 有更新，恢复 toasts', {
        当前toasts数量: toasts.length,
        全局toasts数量: globalToasts.length
      })
      setToasts(globalToasts)
      toastsRef.current = globalToasts
    }
  }, []) // 只在组件挂载时执行一次
  
  // 新增：监听messages变化，自动滚动到底部（只在消息数量增加时）
  const prevMessagesLengthRef = useRef(messages.length)
  useEffect(() => {
    // 🔧 调试：记录消息变化
    addLog('info', '🔄 [ChatView] messages 状态变化', { 
      messagesCount: messages.length,
      messages: messages.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser })),
      messageIds: messages.map(m => m.id)
    })
    const prevLen = prevMessagesLengthRef.current
    // 只有在消息数量增加时才自动滚动，避免无关重渲染导致滚动重置
    if (messages.length > prevLen) {
      setShouldAutoScroll(true)
      scrollToBottom()
    }
    prevMessagesLengthRef.current = messages.length
  }, [messages]) // 🔧 仅在 messages 数组变化时处理

  // 🔧 使用 ref 来跟踪是否正在处理 pendingMessage，避免重复执行
  const processingPendingMessageRef = useRef(false)
  // 🔧 使用 ref 保存 selectionContext，避免作为依赖项导致不必要的重新执行
  const selectionContextRef = useRef(selectionContext)
  
  // 🔧 更新 ref 当 selectionContext 变化时
  useEffect(() => {
    selectionContextRef.current = selectionContext
  }, [selectionContext])

  // 新增：监听待发送消息
  useEffect(() => {
    // 🔧 添加详细日志，帮助调试
    addLog('info', '🔍 [ChatView] useEffect 执行（pendingMessage）', {
      hasPendingMessage: !!pendingMessage,
      pendingMessageText: pendingMessage?.text,
      pendingMessageQuotedText: pendingMessage?.quotedText,
      processingRef: processingPendingMessageRef.current
    })
    
    // 🔧 如果正在处理或没有 pendingMessage，直接返回
    if (processingPendingMessageRef.current) {
      addLog('info', '⏭️ [ChatView] 跳过处理（正在处理中）', {
        processingRef: processingPendingMessageRef.current
      })
      return
    }
    
    if (!pendingMessage) {
      addLog('info', '⏭️ [ChatView] 跳过处理（没有 pendingMessage）')
      return
    }
    
    // 🔧 标记为正在处理
    processingPendingMessageRef.current = true
    
      addLog('info', '📥 [ChatView] 收到 pendingMessage', pendingMessage)
    
    // 🔧 使用立即执行函数来处理，确保逻辑清晰
    ;(async () => {
      try {
      // 判断消息类型：如果没有 quotedText，说明是 AI 直接响应
      if (!pendingMessage.quotedText) {
        // AI 响应消息
        // 🔧 解析 AI 响应，去除 JSON 符号
        const parsedResponse = parseAIResponse(pendingMessage.text)
        const aiMessage = {
            id: generateMessageId(),
          text: parsedResponse,
          isUser: false,
          timestamp: new Date()
        }
        addLog('info', '📝 [ChatView] 添加 AI 消息到 UI', aiMessage)
        setMessages(prev => {
          const newMessages = [...prev, aiMessage]
            // 🔧 不在渲染期间调用 addLog，使用 setTimeout 延迟执行
            setTimeout(() => {
          addLog('success', '✅ [ChatView] 消息列表已更新（AI消息）', { 
            totalMessages: newMessages.length,
            allMessages: newMessages.map(m => ({ id: m.id, text: m.text?.substring(0, 50), isUser: m.isUser }))
          })
            }, 0)
          return newMessages
        })
        // 🔧 延迟清除，确保状态更新完成
        setTimeout(() => {
          clearPendingMessage()
            processingPendingMessageRef.current = false
        }, 0)
      } else {
        // 用户提问消息 - 需要触发 API 调用
        const questionText = pendingMessage.text
        const currentQuotedText = pendingMessage.quotedText
          // 🔧 优先使用 pendingContext（从 sendMessageToChat 传递），否则使用 ref 中的 selectionContext
          const currentSelectionContext = pendingContext || selectionContextRef.current
        
        addLog('info', '📝 [ChatView] 处理用户消息', {
          questionText,
          currentQuotedText,
          hasSelectionContext: !!currentSelectionContext,
          hasPendingContext: !!pendingContext,
          hasSelectionContextProp: !!selectionContext,
          isProcessing,
          pendingContext: pendingContext ? {
            hasSentence: !!pendingContext.sentence,
            hasTokens: !!pendingContext.tokens,
            tokensCount: pendingContext.tokens?.length || 0,
            tokenInfo: pendingContext.tokens?.[0] ? {
              token_body: pendingContext.tokens[0].token_body,
              sentence_token_id: pendingContext.tokens[0].sentence_token_id,
              global_token_id: pendingContext.tokens[0].global_token_id
            } : null
          } : null,
            selectionContextProp: selectionContextRef.current ? {
              hasSentence: !!selectionContextRef.current.sentence,
              hasTokens: !!selectionContextRef.current.tokens,
              tokensCount: selectionContextRef.current.tokens?.length || 0
          } : null
        })
        
        // 🔧 先添加消息到 UI，然后再清除 pendingMessage（避免状态冲突）
          const messageId = generateMessageId()
        const userMessageWithId = {
          id: messageId,
          text: questionText,
          isUser: true,
          timestamp: pendingMessage.timestamp || new Date(),
          quote: currentQuotedText
        }
          addLog('info', '📝 [ChatView] 添加用户消息到 UI', userMessageWithId)
          
          // 🔧 关键修复：在调用 setMessages 之前就更新全局 ref
          // 这样可以确保即使组件在 setMessages 执行前重新挂载，也能从全局 ref 恢复正确的状态
          const currentMessages = messagesRef.current || window.chatViewMessagesRef || []
          const exists = currentMessages.some(m => m.id === messageId)
          
          if (!exists) {
            const newMessages = [...currentMessages, userMessageWithId]
            // 🔧 立即更新全局 ref 和本地 ref（在 setMessages 之前）
            messagesRef.current = newMessages
            window.chatViewMessagesRef = newMessages
            
            addLog('info', '🔧 [ChatView] 已更新全局 ref（在 setMessages 之前，用户消息）', {
              newLength: newMessages.length,
              newMessages: newMessages.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser }))
            })
        
        // 🔧 使用函数式更新，确保基于最新状态
        setMessages(prev => {
              // 🔧 不在渲染期间调用 addLog，使用 setTimeout 延迟执行
              setTimeout(() => {
                addLog('info', '🔍 [ChatView] setMessages 回调执行 - 用户消息', {
                  prevLength: prev.length,
                  prevMessages: prev.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser })),
                  messageId: messageId,
                  globalRefLength: window.chatViewMessagesRef?.length || 0
                })
              }, 0)
              
          // 🔧 检查是否已经存在相同的消息（避免重复添加）
              const existsInPrev = prev.some(m => m.id === messageId)
              if (existsInPrev) {
                setTimeout(() => {
            addLog('warning', '⚠️ [ChatView] 消息已存在，跳过添加', { messageId, currentMessages: prev.length })
                }, 0)
            return prev
          }
          
              // 🔧 使用全局 ref 中的最新状态，而不是 prev（因为可能已经被重新挂载重置）
              const latestMessages = window.chatViewMessagesRef || newMessages
              setTimeout(() => {
          addLog('success', '✅ [ChatView] 消息列表已更新（用户消息）', { 
                  totalMessages: latestMessages.length,
            prevLength: prev.length,
                  lastMessage: latestMessages[latestMessages.length - 1],
                  allMessages: latestMessages.map(m => ({ id: m.id, text: m.text?.substring(0, 50), isUser: m.isUser }))
                })
                console.log('🔍 [ChatView] setMessages 返回新数组（用户消息）:', {
                  newLength: latestMessages.length,
                  newMessages: latestMessages.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser }))
                })
              }, 0)
              return latestMessages
            })
          } else {
            addLog('warning', '⚠️ [ChatView] 用户消息已存在，跳过添加', { messageId })
          }
          
          // 🔧 立即检查状态（使用 setTimeout 确保状态更新完成）
        setTimeout(() => {
          setMessages(current => {
              // 🔧 不在渲染期间调用 addLog，使用 setTimeout 延迟执行
              setTimeout(() => {
            addLog('info', '🔍 [ChatView] 状态检查（用户消息后）', {
              currentLength: current.length,
                  currentMessages: current.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser })),
                  expectedMessageId: messageId,
                  refLength: messagesRef.current.length
            })
              }, 0)
            return current // 不修改状态，只用于调试
          })
          }, 50)
        
        // 🔧 保存 currentSelectionContext 到局部变量，避免在异步函数中丢失
        const savedSelectionContext = currentSelectionContext
        
        // 🔧 延迟清除 pendingMessage，确保状态更新完成
        setTimeout(() => {
      clearPendingMessage()
          clearPendingContext()
        }, 0)
        
        // 🔧 触发 API 调用（类似于 handleSendMessage 的逻辑）
        if (!isProcessing && questionText.trim() !== '') {
            addLog('info', '🚀 [ChatView] 开始处理 API 调用', { 
              questionText,
              isProcessing,
              hasOnProcessingChange: !!onProcessingChange,
              hasExternalIsProcessing: externalIsProcessing !== null
            })
            
            // 🔧 立即设置处理状态
          setIsProcessing(true)
            addLog('info', '🔧 [ChatView] isProcessing 已设置为 true', {
              hasOnProcessingChange: !!onProcessingChange,
              hasExternalIsProcessing: externalIsProcessing !== null
            })
          
            try {
              const { apiService } = await import('../../../services/api')
              
              // 🔧 关键：如果有新的选择上下文，先更新 session state，确保后端使用最新的句子和token
              // 🔧 使用保存的 savedSelectionContext，而不是 currentSelectionContext（可能已被清除）
              if (savedSelectionContext && savedSelectionContext.sentence) {
                addLog('info', '🔧 [ChatView] 检测到新的选择上下文（自动发送），先更新 session state', savedSelectionContext)
                try {
                  const preUpdatePayload = {
                    sentence: savedSelectionContext.sentence
                  }
                  
                  // 添加token信息（如果有）
                  if (savedSelectionContext.tokens && savedSelectionContext.tokens.length > 0) {
                    if (savedSelectionContext.tokens.length > 1) {
                      preUpdatePayload.token = {
                        multiple_tokens: savedSelectionContext.tokens,
                        token_indices: savedSelectionContext.tokenIndices,
                        token_text: savedSelectionContext.selectedTexts.join(' ')
                      }
                      addLog('info', '🔧 [ChatView] 更新多个 token 信息', preUpdatePayload.token)
                    } else {
                      const token = savedSelectionContext.tokens[0]
                      // 🔧 确保 token 对象有必要的字段
                      const tokenPayload = {
                        token_body: token.token_body || token.token || '',
                        sentence_token_id: token.sentence_token_id || null
                      }
                      // 🔧 只有在存在时才添加 global_token_id
                      if (token.global_token_id) {
                        tokenPayload.global_token_id = token.global_token_id
                      }
                      preUpdatePayload.token = tokenPayload
                      addLog('info', '🔧 [ChatView] 更新单个 token 信息', {
                        tokenPayload,
                        originalToken: token,
                        hasTokenBody: !!token.token_body,
                        hasSentenceTokenId: !!token.sentence_token_id,
                        sentenceId: savedSelectionContext.sentence?.sentence_id,
                        textId: savedSelectionContext.sentence?.text_id
                      })
                    }
                  } else {
                    // 如果只选择了句子而没有token，清除旧的token
                    preUpdatePayload.token = null
                    addLog('warning', '⚠️ [ChatView] 没有 token 信息，清除 token', {
                      hasTokens: !!savedSelectionContext.tokens,
                      tokensLength: savedSelectionContext.tokens?.length || 0
                    })
                  }
                  
                  await apiService.session.updateContext(preUpdatePayload)
                  addLog('success', '✅ [ChatView] Session state 已更新为最新选择（自动发送）', preUpdatePayload)
                  
                  // 等待一下确保后端已处理
                  await new Promise(resolve => setTimeout(resolve, 100))
                } catch (error) {
                  addLog('error', '❌ [ChatView] 更新 session state 失败（自动发送）', { error: error.message })
                  // 继续执行，不阻止发送消息
                }
              } else {
                addLog('warning', '⚠️ [ChatView] 没有选择上下文，直接发送消息')
              }
              
              // 更新 current_input
              const updatePayload = {
                current_input: questionText
              }
              
              await apiService.session.updateContext(updatePayload)
              addLog('success', '✅ [ChatView] 已更新 current_input', updatePayload)
              
              // 调用 chat 接口
              addLog('info', '📤 [ChatView] 调用 chat API...', { questionText })
              let response = null
              try {
                response = await apiService.sendChat({
                user_question: questionText
              })
              addLog('info', '📥 [ChatView] 收到 API 响应', { 
                hasResponse: !!response,
                hasAiResponse: !!response?.ai_response,
                  responseKeys: response ? Object.keys(response) : [],
                  responseType: typeof response,
                  responseString: JSON.stringify(response).substring(0, 200)
                })
              } catch (apiError) {
                addLog('error', '❌ [ChatView] API 调用失败', {
                  error: apiError.message,
                  stack: apiError.stack,
                  response: apiError.response
                })
                // 🔧 即使API调用失败，也要重置处理状态
                setIsProcessing(false)
                processingPendingMessageRef.current = false
                return // 提前返回，不再继续处理
              }
              
              // 显示 AI 回答
              if (response && response.ai_response) {
                try {
                const parsedResponse = parseAIResponse(response.ai_response)
                  // 🔧 使用更唯一的 ID，避免与用户消息 ID 冲突
                  const aiMessageId = generateMessageId()
                const aiMessage = {
                    id: aiMessageId,
                  text: parsedResponse,
                  isUser: false,
                  timestamp: new Date()
                }
                addLog('info', '📝 [ChatView] 添加 AI 回答到 UI', aiMessage)
                  
                  // 🔧 关键修复：在调用 setMessages 之前就更新全局 ref
                  // 这样可以确保即使组件在 setMessages 执行前重新挂载，也能从全局 ref 恢复正确的状态
                  const currentMessages = messagesRef.current || window.chatViewMessagesRef || []
                  const exists = currentMessages.some(m => m.id === aiMessageId)
                  
                  if (!exists) {
                    // 🔧 创建新消息列表，并按时间升序排序（确保显示顺序正确）
                    const newMessages = [...currentMessages, aiMessage].sort(
                      (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
                    )
                    
                    // 🔧 先更新全局 ref
                    messagesRef.current = newMessages
                    window.chatViewMessagesRef = newMessages
                    
                    // 🔧 同步到 localStorage（保存时按降序，保留最新的200条）
                    const allFromLS = loadAllMessagesFromLS()
                    const withoutCurrent = allFromLS.filter(m => !newMessages.some(n => n.id === m.id))
                    const merged = [...withoutCurrent, ...newMessages.map(m => ({ ...m, articleId }))]
                    merged.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                    const trimmed = merged.slice(0, 200)
                    saveAllMessagesToLS(trimmed)
                    
                    addLog('info', '🔧 [ChatView] 已更新全局 ref（pendingMessage，AI回答）', {
                      newLength: newMessages.length,
                      newMessages: newMessages.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser })),
                      globalRefLength: window.chatViewMessagesRef?.length || 0
                    })
                    
                    // 🔧 使用函数式更新，但基于最新的全局 ref
                    setMessages(() => {
                      setTimeout(() => {
                        addLog('success', '✅ [ChatView] 消息列表已更新（pendingMessage，AI回答）', { 
                          totalMessages: newMessages.length,
                          aiResponse: parsedResponse.substring(0, 100) + '...',
                          allMessages: newMessages.map(m => ({ id: m.id, text: m.text?.substring(0, 50), isUser: m.isUser }))
                        })
                      }, 0)
                      return newMessages
                    })
                    
                    // 🔧 关键修复：在显示 AI 回答后立即重置处理状态，不等待后续的 toast 轮询
                    setIsProcessing(false)
                    addLog('success', '✅ [ChatView] isProcessing 已重置为 false（pendingMessage，AI 回答显示后）')
                  } else {
                    addLog('warning', '⚠️ [ChatView] AI 消息已存在，跳过添加', { messageId: aiMessageId })
                    // 🔧 即使消息已存在，也确保状态同步并重置处理状态
                    if (currentMessages.length > messages.length) {
                      setMessages([...currentMessages])
                    }
                    setIsProcessing(false)
                  }
                  
                  // 🔧 立即检查状态（使用 setTimeout 确保状态更新完成）
                setTimeout(() => {
                  setMessages(current => {
                      // 🔧 不在渲染期间调用 addLog，使用 setTimeout 延迟执行
                      setTimeout(() => {
                        addLog('info', '🔍 [ChatView] 状态检查（setMessages后）', {
                      currentLength: current.length,
                          currentMessages: current.map(m => ({ id: m.id, text: m.text?.substring(0, 30), isUser: m.isUser })),
                          expectedAiMessageId: aiMessageId,
                          refLength: messagesRef.current.length
                    })
                      }, 0)
                    return current // 不修改状态，只用于调试
                  })
                  }, 50)
                } catch (error) {
                  addLog('error', '❌ [ChatView] 处理 AI 回答时出错', {
                    error: error.message,
                    stack: error.stack,
                    aiResponse: response.ai_response
                  })
                }
              } else {
                addLog('warning', '⚠️ [ChatView] API 响应中没有 ai_response（pendingMessage）', { 
                  response,
                  hasResponse: !!response,
                  responseType: typeof response,
                  responseKeys: response ? Object.keys(response) : []
                })
                // 🔧 如果没有 ai_response，也重置处理状态
                setIsProcessing(false)
              }
              
              // 处理 notations（如果有）
              addLog('info', '🔍 [ChatView] 检查响应中的 notations', {
                hasCreatedGrammarNotations: !!response?.created_grammar_notations,
                grammarNotationsLength: response?.created_grammar_notations?.length || 0,
                hasCreatedVocabNotations: !!response?.created_vocab_notations,
                vocabNotationsLength: response?.created_vocab_notations?.length || 0,
                hasVocabToAdd: !!response?.vocab_to_add,
                vocabToAddLength: response?.vocab_to_add?.length || 0,
                hasAddVocabNotationToCache: !!addVocabNotationToCache,
                hasAddGrammarNotationToCache: !!addGrammarNotationToCache,
                hasCreateVocabNotation: !!createVocabNotation,
                hasSavedSelectionContext: !!savedSelectionContext
              })
              
              if (response?.created_grammar_notations && response.created_grammar_notations.length > 0) {
                addLog('info', '➕ [ChatView] 处理 grammar notations', {
                  count: response.created_grammar_notations.length,
                  notations: response.created_grammar_notations
                })
                response.created_grammar_notations.forEach((n, index) => {
                  addLog('info', `➕ [ChatView] 添加 grammar notation ${index + 1}`, n)
                  if (addGrammarNotationToCache) {
                    addGrammarNotationToCache(n)
                    addLog('success', `✅ [ChatView] grammar notation ${index + 1} 已添加到缓存`)
                  } else {
                    addLog('warning', `⚠️ [ChatView] addGrammarNotationToCache 函数不存在`)
                  }
                })
              } else {
                addLog('info', 'ℹ️ [ChatView] 没有 grammar notations 需要处理')
              }
              
              if (response?.created_vocab_notations && response.created_vocab_notations.length > 0) {
                addLog('info', '➕ [ChatView] 处理 vocab notations', {
                  count: response.created_vocab_notations.length,
                  notations: response.created_vocab_notations
                })
                response.created_vocab_notations.forEach((n, index) => {
                  addLog('info', `➕ [ChatView] 添加 vocab notation ${index + 1}`, n)
                  if (addVocabNotationToCache) {
                    addVocabNotationToCache(n)
                    addLog('success', `✅ [ChatView] vocab notation ${index + 1} 已添加到缓存`)
                  } else {
                    addLog('warning', `⚠️ [ChatView] addVocabNotationToCache 函数不存在`)
                  }
                })
              } else {
                addLog('info', 'ℹ️ [ChatView] 没有 created_vocab_notations 需要处理', {
                  responseKeys: response ? Object.keys(response) : [],
                  createdVocabNotations: response?.created_vocab_notations
                })
              }
              
              // 🔧 如果有 vocab_to_add 且有选择上下文，创建 vocab notation
              if (response?.vocab_to_add && Array.isArray(response.vocab_to_add) && response.vocab_to_add.length > 0 && savedSelectionContext) {
                addLog('info', '➕ [ChatView] 检测到 vocab_to_add，准备创建 vocab notations', {
                  vocabCount: response.vocab_to_add.length,
                  vocabList: response.vocab_to_add.map(v => v.vocab),
                  hasTokens: !!savedSelectionContext.tokens,
                  tokensCount: savedSelectionContext.tokens?.length || 0,
                  hasCreateVocabNotation: !!createVocabNotation
                })
                
                // 为每个新词汇创建 notation
                for (const vocab of response.vocab_to_add) {
                  if (!vocab.vocab || !vocab.vocab_id) {
                    addLog('warning', '⚠️ [ChatView] vocab 缺少必要字段，跳过', vocab)
                    continue
                  }
                  
                  // 找到匹配的 token
                  const matchingToken = savedSelectionContext.tokens?.find(t => {
                    const tokenBody = (t.token_body || t.token || '').toLowerCase()
                    return tokenBody === vocab.vocab.toLowerCase()
                  })
                  
                  if (matchingToken && savedSelectionContext.sentence) {
                    const textId = savedSelectionContext.sentence.text_id
                    const sentenceId = savedSelectionContext.sentence.sentence_id
                    const sentenceTokenId = matchingToken.sentence_token_id
                    
                    addLog('info', '➕ [ChatView] 创建 vocab notation', {
                      vocab: vocab.vocab,
                      vocabId: vocab.vocab_id,
                      textId,
                      sentenceId,
                      sentenceTokenId
                    })
                    
                    if (createVocabNotation) {
                      try {
                        const result = await createVocabNotation(textId, sentenceId, sentenceTokenId, vocab.vocab_id)
                        if (result.success) {
                          addLog('success', `✅ [ChatView] vocab notation 创建成功: ${vocab.vocab}`, result.notation)
                        } else {
                          addLog('warning', `⚠️ [ChatView] vocab notation 创建失败: ${vocab.vocab}`, result)
                        }
                      } catch (error) {
                        addLog('error', `❌ [ChatView] 创建 vocab notation 时出错: ${vocab.vocab}`, {
                          error: error.message,
                          stack: error.stack
                        })
                      }
                    } else {
                      addLog('warning', '⚠️ [ChatView] createVocabNotation 函数不存在，无法创建 vocab notation')
                    }
                  } else {
                    addLog('warning', '⚠️ [ChatView] 找不到匹配的 token 或句子信息，无法创建 vocab notation', {
                      vocab: vocab.vocab,
                      hasMatchingToken: !!matchingToken,
                      hasSentence: !!savedSelectionContext.sentence
                    })
                  }
                }
              } else {
                addLog('info', 'ℹ️ [ChatView] 没有 vocab_to_add 或缺少选择上下文，跳过创建 vocab notation', {
                  hasVocabToAdd: !!response?.vocab_to_add,
                  vocabToAddLength: response?.vocab_to_add?.length || 0,
                  hasSavedSelectionContext: !!savedSelectionContext
                })
              }
              
              // 🔧 注意：isProcessing 已在显示 AI 回答后立即重置，这里不需要重复重置
              // 但需要重置 processingPendingMessageRef
              processingPendingMessageRef.current = false
              addLog('success', '✅ [ChatView] API 调用完成（pendingMessage）', {
                hasOnProcessingChange: !!onProcessingChange,
                hasExternalIsProcessing: externalIsProcessing !== null
              })
            } catch (error) {
              addLog('error', '❌ [ChatView] 自动发送消息失败', { 
                error: error.message, 
                stack: error.stack,
                errorName: error.name,
                errorResponse: error.response
              })
              // 🔧 确保即使出错也重置处理状态
              addLog('info', '🔧 [ChatView] 错误处理：准备重置 isProcessing 状态', {
                hasOnProcessingChange: !!onProcessingChange,
                hasExternalIsProcessing: externalIsProcessing !== null
              })
              
              // 🔧 使用 setTimeout 确保状态更新在下一个事件循环中执行
              setTimeout(() => {
              setIsProcessing(false)
                addLog('success', '✅ [ChatView] 错误处理完成，isProcessing 已重置')
              }, 0)
            } finally {
              // 🔧 确保在处理完成后重置 ref
              processingPendingMessageRef.current = false
              addLog('info', '🔧 [ChatView] processingPendingMessageRef 已重置')
            }
        } else {
          addLog('warning', '⚠️ [ChatView] 跳过 API 调用', { 
            isProcessing, 
            questionText: questionText.trim() 
          })
            // 🔧 如果跳过了 API 调用，也要重置 ref
            processingPendingMessageRef.current = false
          }
          
          // 🔧 不再自动清空引用 - 保持引用以便用户继续追问
          // 引用会在用户选择新的 token 或点击文章空白处时自动更新/清空
          // 这样可以避免在消息添加后立即清除引用，导致 selectionContext 变化，进而可能触发组件重新渲染
        }
      } catch (error) {
        addLog('error', '❌ [ChatView] 处理 pendingMessage 失败', { 
          error: error.message, 
          stack: error.stack 
        })
        processingPendingMessageRef.current = false
      }
    })()
    // 🔧 移除 selectionContext 作为依赖项，使用 ref 代替，避免因 selectionContext 变化导致不必要的重新执行
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingMessage, pendingContext, isProcessing, addLog, addGrammarNotationToCache, addVocabNotationToCache, setIsProcessing, clearPendingMessage, clearPendingContext])

  // 新增：监听跨组件触发的 toast
  useEffect(() => {
    if (pendingToast) {
      showKnowledgeToast(pendingToast)
      clearPendingToast()
    }
  }, [pendingToast, clearPendingToast])

  // 新增：测试连续 Toast 的方法（按下 S 键触发，每 0.5s 一次，共 3 次）
  const triggerSequentialToasts = () => {
    const items = ['测试Toast 1', '测试Toast 2', '测试Toast 3']
    items.forEach((msg, idx) => {
      setTimeout(() => {
        showKnowledgeToast(msg)
      }, idx * 500)
    })
  }

  // 注释掉按s键触发Toast的测试功能（保留代码以备将来使用）
  // useEffect(() => {
  //   const onKeyDown = (e) => {
  //     if ((e.key || '').toLowerCase() === 's') {
  //       triggerSequentialToasts()
  //     }
  //   }
  //   window.addEventListener('keydown', onKeyDown)
  //   return () => window.removeEventListener('keydown', onKeyDown)
  // }, [])

  const handleSendMessage = async () => {
    console.log('🔘 [ChatView] handleSendMessage 被调用', {
      inputText: inputText.trim(),
      isProcessing,
      hasSelectedToken,
      hasSelectedSentence
    })
    
    if (inputText.trim() === '' || isProcessing) {
      console.log('⚠️ [ChatView] handleSendMessage 提前返回', {
        isEmpty: inputText.trim() === '',
        isProcessing
      })
      return
    }
    
    // 🔧 设置处理状态为 true
    setIsProcessing(true)
    console.log('✅ [ChatView] isProcessing 已设置为 true')
    
    // 添加到父组件的调试日志
    if (typeof addDebugLog === 'undefined') {
      // 如果没有传递 addDebugLog，创建一个本地版本
      window.chatDebugLogs = window.chatDebugLogs || []
      window.chatDebugLogs.push(`[${new Date().toLocaleTimeString()}] handleSendMessage 开始`)
      window.chatDebugLogs = window.chatDebugLogs.slice(-10)
    }

    const questionText = inputText
    console.log('📝 [ChatView] 准备发送消息', { questionText })
    // 🔧 保存当前的引用文本和上下文（用于 UI 显示）
    const currentQuotedText = quotedText
    const currentSelectionContext = selectionContext
    
    // 🔧 关键：如果有新的选择上下文，先更新 session state，确保后端使用最新的句子
    // 这样可以避免使用旧的 session state 中的句子
    if (currentSelectionContext && currentSelectionContext.sentence) {
      console.log('🔧 [ChatView] 检测到新的选择上下文，先更新 session state 以确保使用最新句子...')
      try {
        const { apiService } = await import('../../../services/api')
        const preUpdatePayload = {
          sentence: currentSelectionContext.sentence
        }
        
        // 添加token信息（如果有）
        if (currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
          if (currentSelectionContext.tokens.length > 1) {
            preUpdatePayload.token = {
              multiple_tokens: currentSelectionContext.tokens,
              token_indices: currentSelectionContext.tokenIndices,
              token_text: currentSelectionContext.selectedTexts.join(' ')
            }
          } else {
            const token = currentSelectionContext.tokens[0]
            preUpdatePayload.token = {
              token_body: token.token_body,
              sentence_token_id: token.sentence_token_id
            }
          }
        } else {
          // 如果只选择了句子而没有token，清除旧的token
          preUpdatePayload.token = null
        }
        
        await apiService.session.updateContext(preUpdatePayload)
        console.log('✅ [ChatView] Session state 已更新为最新选择')
      } catch (error) {
        console.error('❌ [ChatView] 更新 session state 失败:', error)
        // 继续执行，不阻止发送消息
      }
    }
    
    // Add user message with quote if exists
    const userMessage = {
      id: generateMessageId(),
      text: questionText,
      isUser: true,
      timestamp: new Date(),
      quote: currentQuotedText || null
    }
    
    // 🔧 重构：简化消息添加逻辑，直接使用当前状态
    console.log('🔧 [ChatView] 准备添加用户消息', {
      messageId: userMessage.id,
      currentMessagesLength: messages.length,
      currentMessageIds: messages.map(m => m.id),
      messagesRefLength: messagesRef.current?.length || 0,
      globalRefLength: window.chatViewMessagesRef?.length || 0
    })
    
    // 🔧 直接使用当前 messages 状态，创建新数组确保 React 检测到变化
    const newMessages = [...messages, userMessage]
    
    // 🔧 更新全局 ref
    messagesRef.current = newMessages
    window.chatViewMessagesRef = newMessages
    
    console.log('🔧 [ChatView] 已更新全局 ref（用户消息）', {
      newLength: newMessages.length,
      messageId: userMessage.id,
      newMessageIds: newMessages.map(m => m.id),
      globalRefLength: window.chatViewMessagesRef?.length || 0
    })
    
    // 🔧 直接设置状态，使用新数组引用
    setMessages(newMessages)
    console.log('✅ [ChatView] 已调用 setMessages（用户消息）', {
      newLength: newMessages.length,
      messageId: userMessage.id
    })
    setInputText('')
    document.title = '正在发送请求...'

    // 调用后端 chat API
    try {
      document.title = '等待后端响应...'
      console.log('\n' + '='.repeat(80))
      if (currentSelectionContext) {
        console.log('  - 句子 ID:', currentSelectionContext.sentence?.sentence_id)
        console.log('  - 文章 ID:', currentSelectionContext.sentence?.text_id)
        console.log('  - 句子原文:', currentSelectionContext.sentence?.sentence_body)
        console.log('  - 选中的 tokens:', currentSelectionContext.selectedTexts)
        console.log('  - Token 数量:', currentSelectionContext.tokens?.length)
      } else {
        console.log('  - 无上下文（未选择任何token）')
      }
      console.log('='.repeat(80) + '\n')
      
      const { apiService } = await import('../../../services/api')
      
      // 🔧 关键修复：只更新 current_input，不更新句子和token
      // 因为句子和token已经在选择时更新了（或者在发送前刚刚更新）
      // 这样可以确保使用后端当前已设置的 session state，而不是前端可能已过时的上下文
      const updatePayload = {
        current_input: questionText
      }
      
      console.log('💬 [ChatView] 只更新 current_input，使用后端当前已设置的 session state')
      console.log('💬 [ChatView] 当前选择上下文（仅用于日志）:', {
        hasContext: !!currentSelectionContext,
        sentenceId: currentSelectionContext?.sentence?.sentence_id,
        sentenceBody: currentSelectionContext?.sentence?.sentence_body?.substring(0, 50),
        tokenCount: currentSelectionContext?.tokens?.length || 0
      })
      
      const updateResponse = await apiService.session.updateContext(updatePayload)
      console.log('✅ [ChatView] Session context 更新完成（仅更新 current_input）:', updateResponse)
      
      // 调用 chat 接口
      console.log('💬 [Frontend] 步骤4: 调用 /api/chat 接口...')
      const response = await apiService.sendChat({
        user_question: questionText
      })
      
      document.title = '收到响应，处理中...'
      console.log('✅ [Frontend] 步骤5: 收到响应')
      console.log('🔍 [Frontend] 完整响应数据:', response)
      console.log('🔍 [Frontend] response.created_grammar_notations:', response?.created_grammar_notations)
      console.log('🔍 [Frontend] response.created_vocab_notations:', response?.created_vocab_notations)
      
      // 🔧 检查响应是否成功
      if (response && response.success === false) {
        // 🔧 处理错误响应
        const errorMessage = response.error || '处理请求时发生错误'
        console.error('❌ [Frontend] API 返回错误:', errorMessage)
        
        const latestMessages = window.chatViewMessagesRef || messagesRef.current || messages
        const errorMsg = {
          id: generateMessageId(),
          text: `抱歉，处理您的问题时出现错误: ${errorMessage}`,
          isUser: false,
          timestamp: new Date()
        }
        
        const newMessages = [...latestMessages, errorMsg]
        messagesRef.current = newMessages
        window.chatViewMessagesRef = newMessages
        setMessages(newMessages)
        
        console.log('✅ [ChatView] 已显示错误消息', {
          errorMessage,
          newLength: newMessages.length
        })
        
        // 🔧 处理完成，重置处理状态
        setIsProcessing(false)
        return
      }
      
      // 🔧 立即显示 AI 回答（不等待后续流程）
      if (response && response.ai_response) {
        document.title = '显示 AI 回答...'
        console.log('🔍 [ChatView] 原始 AI 响应:', {
          type: typeof response.ai_response,
          value: response.ai_response,
          isString: typeof response.ai_response === 'string',
          isObject: typeof response.ai_response === 'object',
          stringLength: typeof response.ai_response === 'string' ? response.ai_response.length : 0
        })
        // 🔧 解析 AI 响应，去除 JSON 符号
        const parsedResponse = parseAIResponse(response.ai_response)
        console.log('🔍 [ChatView] 解析后的 AI 响应:', {
          parsed: parsedResponse,
          length: parsedResponse?.length || 0,
          isEmpty: !parsedResponse || parsedResponse.trim() === ''
        })
        
        // 🔧 如果解析失败或为空，使用原始响应或尝试其他方式
        let finalResponse = parsedResponse
        if (!finalResponse || finalResponse.trim() === '') {
          if (typeof response.ai_response === 'string') {
            finalResponse = response.ai_response
          } else if (typeof response.ai_response === 'object' && response.ai_response.answer) {
            finalResponse = response.ai_response.answer
          } else {
            finalResponse = JSON.stringify(response.ai_response)
          }
          console.log('⚠️ [ChatView] 解析失败，使用备用响应:', {
            finalResponse: finalResponse?.substring(0, 100)
          })
        }
        
        const aiMessage = {
          id: generateMessageId(),
          text: finalResponse,
          isUser: false,
          timestamp: new Date()
        }
        console.log('✅ [ChatView] 创建的 AI 消息:', {
          id: aiMessage.id,
          textLength: aiMessage.text?.length || 0,
          textPreview: aiMessage.text?.substring(0, 100) || ''
        })
        
        // 🔧 关键修复：统一消息添加逻辑，确保消息正确显示
        const currentMessages = messagesRef.current || window.chatViewMessagesRef || []
        const exists = currentMessages.some(m => m.id === aiMessage.id)
        
        if (!exists) {
          // 🔧 创建新消息列表，并按时间升序排序（确保显示顺序正确）
          const newMessages = [...currentMessages, aiMessage].sort(
            (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
          )
          
          // 🔧 先更新全局 ref
          messagesRef.current = newMessages
          window.chatViewMessagesRef = newMessages
          
          // 🔧 同步到 localStorage（保存时按降序，保留最新的200条）
          const allFromLS = loadAllMessagesFromLS()
          const withoutCurrent = allFromLS.filter(m => !newMessages.some(n => n.id === m.id))
          const merged = [...withoutCurrent, ...newMessages.map(m => ({ ...m, articleId }))]
          merged.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
          const trimmed = merged.slice(0, 200)
          saveAllMessagesToLS(trimmed)
          
          // 🔧 使用函数式更新，但基于最新的全局 ref
          setMessages(() => {
            console.log('✅ [ChatView] setMessages 执行', {
              newLength: newMessages.length,
              messageId: aiMessage.id
            })
            return newMessages
          })
          
          console.log('✅ [ChatView] AI 消息已添加到状态', {
            newLength: newMessages.length,
            messageId: aiMessage.id
          })
        } else {
          console.log('⚠️ [ChatView] AI 消息已存在，确保状态同步', {
            messageId: aiMessage.id,
            currentLength: currentMessages.length
          })
          // 🔧 即使消息已存在，也确保状态同步
          if (currentMessages.length > messages.length) {
            setMessages([...currentMessages])
          }
        }
        
        document.title = 'AI 回答已显示'
        console.log('📺 [ChatView] AI 回答已立即显示')
        
        // 🔧 关键修复：在显示 AI 回答后立即重置处理状态，不等待后续的 toast 轮询
        // 因为 toast 轮询是异步的，可能会持续很长时间，不应该阻塞 isProcessing 状态
        setIsProcessing(false)
        console.log('✅ [ChatView] isProcessing 已重置为 false（AI 回答显示后）')
      } else {
        // 🔧 如果没有 ai_response，也重置处理状态
        console.warn('⚠️ [ChatView] 响应中没有 ai_response，重置处理状态')
        setIsProcessing(false)
      }
      
      // 🔧 立即添加 notations 到缓存（如果有）
      document.title = '添加 notations...'
      if (response?.created_grammar_notations && response.created_grammar_notations.length > 0) {
        console.log('➕ Adding grammar notations:', response.created_grammar_notations)
        response.created_grammar_notations.forEach(n => {
          console.log('Adding notation:', n)
          if (addGrammarNotationToCache) addGrammarNotationToCache(n)
        })
        document.title = `Added ${response.created_grammar_notations.length} grammar notations`
      }
      if (response?.created_vocab_notations && response.created_vocab_notations.length > 0) {
        console.log('➕ [ChatView] ========== 开始处理 vocab notations ==========')
        console.log('➕ [ChatView] 接收到的 created_vocab_notations:', JSON.stringify(response.created_vocab_notations, null, 2))
        console.log('➕ [ChatView] addVocabNotationToCache 函数类型:', typeof addVocabNotationToCache)
        console.log('➕ [ChatView] addVocabNotationToCache 函数:', addVocabNotationToCache)
        
        response.created_vocab_notations.forEach((n, index) => {
          console.log(`➕ [ChatView] 处理第 ${index + 1} 个 vocab notation:`, n)
          // 🔧 字段名映射：后端返回 token_id，前端期望 token_index
          const mappedNotation = {
            ...n,
            token_index: n.token_id || n.token_index  // 添加 token_index 字段
          }
          console.log(`➕ [ChatView] 映射后的 notation ${index + 1}:`, mappedNotation)
          
          if (addVocabNotationToCache) {
            console.log(`➕ [ChatView] 调用 addVocabNotationToCache 添加第 ${index + 1} 个 notation`)
            addVocabNotationToCache(mappedNotation)
            console.log(`✅ [ChatView] addVocabNotationToCache 调用完成（第 ${index + 1} 个）`)
          } else {
            console.error('❌ [ChatView] addVocabNotationToCache 函数不存在！')
          }
        })
        console.log('➕ [ChatView] ========== vocab notations 处理完成 ==========')
        document.title = `Added ${response.created_vocab_notations.length} vocab notations`
      } else {
        console.log('⚠️ [ChatView] 响应中没有 created_vocab_notations 或为空:', {
          hasCreatedVocabNotations: !!response?.created_vocab_notations,
          length: response?.created_vocab_notations?.length || 0,
          created_vocab_notations: response?.created_vocab_notations
        })
      }
      
      // 🔧 移除旧的轮询机制（检查 notations），改用新的 pending-knowledge API 轮询
      // 新的轮询机制在下面的 toast 处理逻辑中统一实现
      
      // 🔧 检查是否有新创建的 notations
      const hasGrammarNotations = response?.created_grammar_notations && Array.isArray(response.created_grammar_notations) && response.created_grammar_notations.length > 0
      const hasVocabNotations = response?.created_vocab_notations && Array.isArray(response.created_vocab_notations) && response.created_vocab_notations.length > 0
      
      // 🔧 自动刷新 grammar/vocab 列表（如果有新数据或新notations）
      const hasNewGrammar = response?.grammar_to_add && response.grammar_to_add.length > 0
      const hasNewVocab = response?.vocab_to_add && response.vocab_to_add.length > 0
      
      // 如果有新语法被创建，或者有新的 grammar notation（为现有语法添加例句），都刷新
      if (hasNewGrammar || hasGrammarNotations) {
        refreshGrammar()
      }
      
      // 如果有新词汇被创建，或者有新的 vocab notation（为现有词汇添加例句），都刷新
      if (hasNewVocab || hasVocabNotations) {
        refreshVocab()
      }
      
      // 🔧 重构：直接从响应中获取新创建的知识点并显示 Toast
      const toastItems = []
      
      if (response?.grammar_to_add && response.grammar_to_add.length > 0) {
        response.grammar_to_add.forEach(g => {
          if (g.name) {
            toastItems.push(`🆕 语法: ${g.name}`)
          }
        })
      }
      
      if (response?.vocab_to_add && response.vocab_to_add.length > 0) {
        response.vocab_to_add.forEach(v => {
          if (v.vocab) {
            toastItems.push(`🆕 词汇: ${v.vocab}`)
          }
        })
      }
      
      // 🔧 如果有新知识点，立即显示 Toast
      if (toastItems.length > 0) {
        console.log('🍞 [Toast Debug] 立即显示 toast（从响应中获取）:', toastItems)
        toastItems.forEach((item, idx) => {
          setTimeout(() => {
            showKnowledgeToast(item)
          }, idx * 600)
        })
      } else if (!hasGrammarNotations && !hasVocabNotations) {
        // 如果响应中没有 vocab_to_add/grammar_to_add，但后台可能正在创建，启动轮询
          // 🔧 轮询获取后台任务创建的新知识点
          let textId = selectionContext?.sentence?.text_id || articleId
          // 确保 textId 是整数类型
          if (textId) {
            textId = parseInt(textId) || textId
          }
          // 从 localStorage 获取 user_id
          const storedUserId = typeof localStorage !== 'undefined' ? localStorage.getItem('user_id') : null
          const userId = storedUserId ? parseInt(storedUserId) : 2
          
          console.log('🍞 [Toast Debug] 启动轮询检测新知识点:', { userId, textId, articleId, selectionContext: !!selectionContext })
          
          // 确保 textId 存在
          if (!textId) {
            console.warn('⚠️ [Toast Debug] textId 不存在，无法启动轮询')
          } else {
            let pollCount = 0
            const maxPolls = 10
            const pollInterval = 500
            
            const pollPendingKnowledge = setInterval(async () => {
              pollCount++
              console.log(`🍞 [Toast Debug] 轮询第 ${pollCount} 次，检查新知识点...`)
              
              try {
                const { apiService } = await import('../../../services/api')
                const pendingResponse = await apiService.getPendingKnowledge(userId, textId)
                
                console.log('🍞 [Toast Debug] 轮询响应:', pendingResponse)
                console.log('🍞 [Toast Debug] 轮询响应类型:', typeof pendingResponse)
                console.log('🍞 [Toast Debug] 轮询响应 keys:', pendingResponse ? Object.keys(pendingResponse) : 'null')
                
                // 🔧 处理响应格式：API 拦截器可能已经提取了内层 data
                let grammar_to_add = []
                let vocab_to_add = []
                
                if (pendingResponse) {
                  // 🔧 处理响应格式：API 拦截器已经保留了完整结构 { success: true, data: {...} }
                  if (pendingResponse.success !== undefined && pendingResponse.data) {
                    grammar_to_add = pendingResponse.data.grammar_to_add || []
                    vocab_to_add = pendingResponse.data.vocab_to_add || []
                    console.log('🍞 [Toast Debug] 从 success.data 中提取:', { grammar_to_add, vocab_to_add })
                  }
                  // 如果响应格式已经被拦截器提取为 { grammar_to_add: [], vocab_to_add: [] }
                  else if (pendingResponse.grammar_to_add !== undefined || pendingResponse.vocab_to_add !== undefined) {
                    grammar_to_add = pendingResponse.grammar_to_add || []
                    vocab_to_add = pendingResponse.vocab_to_add || []
                    console.log('🍞 [Toast Debug] 从直接字段中提取:', { grammar_to_add, vocab_to_add })
                  } else {
                    console.warn('🍞 [Toast Debug] 无法解析响应格式:', pendingResponse)
                  }
                } else {
                  console.warn('🍞 [Toast Debug] pendingResponse 为空')
                }
                
                console.log('🍞 [Toast Debug] 解析后的数据:', { grammar_to_add, vocab_to_add })
                
                const pendingToasts = []
                
                if (grammar_to_add && grammar_to_add.length > 0) {
                  grammar_to_add.forEach(g => {
                    if (g.name) {
                      pendingToasts.push(`🆕 语法: ${g.name}`)
                    }
                  })
                }
                
                if (vocab_to_add && vocab_to_add.length > 0) {
                  vocab_to_add.forEach(v => {
                    if (v.vocab) {
                      pendingToasts.push(`🆕 词汇: ${v.vocab}`)
                    }
                  })
                }
                
                if (pendingToasts.length > 0) {
                  console.log('🍞 [Toast Debug] 从轮询获取到新知识点，准备显示 toast:', pendingToasts)
                  pendingToasts.forEach((item, idx) => {
                    setTimeout(() => {
                      console.log('🍞 [Toast Debug] 调用 showKnowledgeToast:', item)
                      showKnowledgeToast(item)
                    }, idx * 600)
                  })
                  clearInterval(pollPendingKnowledge)
                } else {
                  console.log('🍞 [Toast Debug] 没有新知识点需要显示')
                }
              } catch (err) {
                console.warn('⚠️ [ChatView] 轮询获取新知识点失败:', err)
              }
              
              if (pollCount >= maxPolls) {
                console.log('🍞 [Toast Debug] 达到最大轮询次数，停止轮询')
                clearInterval(pollPendingKnowledge)
              }
            }, pollInterval)
            
            // 5秒后自动停止轮询
            setTimeout(() => {
              clearInterval(pollPendingKnowledge)
            }, maxPolls * pollInterval)
          }
      }
      
      document.title = '完成'
      
    } catch (error) {
      console.error('💥 [Frontend] Chat request 发生错误:', error)
      const errorMsg = {
        id: generateMessageId(),
        text: `抱歉，处理您的问题时出现错误: ${error.message}`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
    }
    
    // 下面的代码已废弃（保留作为参考）
    /* 原标记逻辑
      ;(async () => {
        if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
        console.log('✅ [ChatView] 进入标记逻辑')
        console.log('🏷️ [ChatView] Checking if tokens should be marked as asked...')
        
        // 从响应中提取 vocab_id（如果有新词汇）
        const vocabIdMap = new Map()
        if (response && response.vocab_to_add && Array.isArray(response.vocab_to_add)) {
          response.vocab_to_add.forEach(v => {
            if (v.vocab && v.vocab_id) {
              vocabIdMap.set(v.vocab.toLowerCase(), v.vocab_id)
            }
          })
          console.log('📝 [ChatView] Vocab ID map:', Object.fromEntries(vocabIdMap))
        }
        
        // 获取所有新生成的词汇（vocab_to_add中的词汇对应的tokens）
        const newVocabTokens = new Set()
        if (response && response.vocab_to_add && Array.isArray(response.vocab_to_add)) {
          response.vocab_to_add.forEach(v => {
            // 将词汇名转换为小写，用于匹配
            if (v.vocab) {
              newVocabTokens.add(v.vocab.toLowerCase())
            }
          })
        }
        console.log('📋 [ChatView] New vocab tokens:', Array.from(newVocabTokens))
        
        // 只标记那些在vocab example的token_indices中的tokens
        const markPromises = currentSelectionContext.tokens.map(async (token, tokenIdx) => {
          // 使用fallback确保字段存在
          const sentenceTokenId = token.sentence_token_id ?? (tokenIdx + 1)
          const sentenceId = currentSelectionContext.sentence?.sentence_id
          const textId = currentSelectionContext.sentence?.text_id ?? articleId  // ← 使用articleId作为fallback
          
          // 尝试查找 vocab_id
          const tokenBody = token.token_body?.toLowerCase() || ''
          const vocabId = vocabIdMap.get(tokenBody) || null
          
          // 检查该token是否在新生成的词汇中
          const shouldMark = newVocabTokens.has(tokenBody)
          
          console.log(`🔍 [DEBUG] Token ${tokenIdx}:`, {
            token_body: token.token_body,
            textId,
            sentenceId,
            sentenceTokenId,
            vocabId,
            shouldMark,
            reason: shouldMark ? '在vocab_to_add中' : '不在vocab_to_add中'
          })
          
          if (shouldMark && sentenceId && textId && sentenceTokenId != null) {
            console.log(`🏷️ [ChatView] Marking token: "${token.token_body}" (${textId}:${sentenceId}:${sentenceTokenId}) with vocabId=${vocabId}`)
            
            // 优先使用新API创建vocab notation
            if (createVocabNotation) {
              console.log('✅ [ChatView] Using new API (createVocabNotation)')
              const result = await createVocabNotation(textId, sentenceId, sentenceTokenId, vocabId)
              if (result.success) {
                console.log('✅ [ChatView] Vocab notation created via new API:', result.notation)
                return true
              } else {
                console.warn('⚠️ [ChatView] Failed to create vocab notation via new API, falling back to old API')
                // 回退到旧API
                if (markAsAsked) {
                  return markAsAsked(textId, sentenceId, sentenceTokenId, vocabId)
                }
                return false
              }
            } else if (markAsAsked) {
              // 如果没有新API，使用旧API（向后兼容）
              console.log('⚠️ [ChatView] Using old API (markAsAsked) - new API not available')
              return markAsAsked(textId, sentenceId, sentenceTokenId, vocabId)
            } else {
              console.error('❌ [ChatView] No API available to mark token')
              return false
            }
          } else {
            console.log(`⏭️ [ChatView] Skipping token: "${token.token_body}" - ${shouldMark ? 'missing fields' : 'not in vocab example'}`)
            return Promise.resolve(false)
          }
        })
        
        try {
          const results = await Promise.all(markPromises)
          const successCount = results.filter(r => r).length
          const usedNewAPI = createVocabNotation !== null
          
          console.log(`✅ [ChatView] Successfully marked ${successCount}/${markPromises.length} tokens (usedNewAPI=${usedNewAPI})`)
          
          // 如果标记成功
          if (successCount > 0) {
            if (usedNewAPI) {
              // 使用新API时，vocab notation已经实时添加到缓存，不需要刷新
              console.log('✅ [ChatView] Vocab notations already updated in cache via new API, skipping refresh')
              
              // 只刷新vocab数据（如果有新创建的vocab例子）
              try {
                console.log('🔄 [ChatView] Refreshing vocab data...')
                await apiService.refreshVocab()
                console.log('✅ [ChatView] Vocab data refreshed successfully')
              } catch (err) {
                console.warn('⚠️ [ChatView] Failed to refresh vocab data:', err)
              }
            } else {
              // 使用旧API时，需要刷新asked tokens和vocab数据
              console.log('⏳ [ChatView] Waiting for backend to save vocab data (old API)...')
              
              // 等待500ms确保后端异步保存完成
              await new Promise(resolve => setTimeout(resolve, 500))
              
              // 刷新vocab数据和asked tokens
              try {
                console.log('🔄 [ChatView] Refreshing vocab data and asked tokens (old API)...')
                await apiService.refreshVocab()
                console.log('✅ [ChatView] Vocab data refreshed successfully')
                
                // 同时刷新asked tokens状态
                if (refreshAskedTokens) {
                  await refreshAskedTokens()
                  console.log('✅ [ChatView] Asked tokens refreshed successfully')
                }
              } catch (err) {
                console.warn('⚠️ [ChatView] Failed to refresh data:', err)
              }
            }
            
            // 实时更新缓存而不是完全刷新
            console.log('🔄 [ChatView] 开始实时更新缓存...')
            
            // 更新grammar notations缓存
            if (response && response.grammar_to_add && Array.isArray(response.grammar_to_add)) {
              console.log('➕ [ChatView] 添加新的grammar rules到缓存:', response.grammar_to_add)
              response.grammar_to_add.forEach(rule => {
                if (addGrammarRuleToCache) {
                  addGrammarRuleToCache(rule)
                }
              })
            }
            
            // 更新vocab notations缓存
            if (response && response.vocab_to_add && Array.isArray(response.vocab_to_add)) {
              console.log('➕ [ChatView] 添加新的vocab examples到缓存:', response.vocab_to_add)
              response.vocab_to_add.forEach(vocab => {
                if (addVocabExampleToCache && vocab.vocab_id) {
                  // 构造vocab example对象
                  const vocabExample = {
                    vocab_id: vocab.vocab_id,
                    text_id: articleId,
                    sentence_id: currentSelectionContext.sentence?.sentence_id,
                    token_index: currentSelectionContext.tokens?.[0]?.sentence_token_id,
                    context_explanation: vocab.explanation || '',
                    token_indices: currentSelectionContext.tokenIndices || []
                  }
                  addVocabExampleToCache(vocabExample)
                }
              })
            }
            
            // 如果有新的grammar notation被创建，也添加到缓存
            if (response && response.new_grammar_notation) {
              console.log('➕ [ChatView] 添加新的grammar notation到缓存:', response.new_grammar_notation)
              if (addGrammarNotationToCache) {
                addGrammarNotationToCache(response.new_grammar_notation)
              }
            }
            
            // 如果有新的vocab notation被创建，也添加到缓存
            if (response && response.new_vocab_notation) {
              console.log('➕ [ChatView] 添加新的vocab notation到缓存:', response.new_vocab_notation)
              if (addVocabNotationToCache) {
                addVocabNotationToCache(response.new_vocab_notation)
              }
            }
            
            // 如果实时更新不可用，回退到完全刷新
            if (!addGrammarNotationToCache && refreshGrammarNotations) {
              console.log('🔄 [ChatView] 回退到完全刷新grammar notations...')
              try {
                await refreshGrammarNotations()
                console.log('✅ [ChatView] Grammar notations refreshed successfully')
              } catch (grammarError) {
                console.error('❌ [ChatView] Failed to refresh grammar notations:', grammarError)
              }
            }
            
            console.log('🎉 [ChatView] Token states updated - green underlines should be visible now')
          } else {
            console.warn('⚠️ [ChatView] 没有token被成功标记')
          }
        } catch (error) {
          console.error('❌ [ChatView] Error marking tokens as asked:', error)
        }
      } else {
        console.warn('⚠️ [ChatView] 标记条件不满足（未进入标记逻辑）')
      }
      
      // 添加session state调试信息
      console.log('🔍 [SESSION STATE DEBUG] After sending message:')
      console.log('  - Question text:', questionText)
      console.log('  - Quoted text:', quotedText || 'None')
      console.log('  - Update payload:', updatePayload)
      console.log('  - Update response:', updateResponse)
      
      // 响应拦截器已经提取了 innerData，所以 response 直接就是 data
      if (response && response.ai_response !== undefined) {
        const { ai_response, grammar_summaries, vocab_summaries, grammar_to_add, vocab_to_add, examples } = response
        
        // 详细打印session state中的vocab/grammar/example状态
        console.log('\n' + '='.repeat(80))
        console.log('📊 [SESSION STATE] 本轮对话生成的知识点状态：')
        console.log('='.repeat(80))
        
        // 新增语法
        if (grammar_to_add && grammar_to_add.length > 0) {
          console.log('🆕 新增语法 (grammar_to_add):', grammar_to_add.length, '个')
          grammar_to_add.forEach((g, idx) => {
            console.log(`  ${idx + 1}. ${g.name}`)
            console.log(`     - 总结: ${g.summary || '无'}`)
            console.log(`     - 详情: ${g.explanation || '无'}`)
          })
        } else {
          console.log('🆕 新增语法 (grammar_to_add): 无')
        }
        
        // 新增词汇
        if (vocab_to_add && vocab_to_add.length > 0) {
          console.log('🆕 新增词汇 (vocab_to_add):', vocab_to_add.length, '个')
          vocab_to_add.forEach((v, idx) => {
            console.log(`  ${idx + 1}. ${v.vocab}`)
            console.log(`     - 翻译: ${v.translation || '无'}`)
            console.log(`     - 用法: ${v.usage || '无'}`)
          })
        } else {
          console.log('🆕 新增词汇 (vocab_to_add): 无')
        }
        
        // 相关语法总结
        if (grammar_summaries && grammar_summaries.length > 0) {
          console.log('📚 相关语法总结 (grammar_summaries):', grammar_summaries.length, '个')
          grammar_summaries.forEach((g, idx) => {
            console.log(`  ${idx + 1}. ${g.name}`)
            console.log(`     - 总结: ${g.summary || '无'}`)
          })
        } else {
          console.log('📚 相关语法总结 (grammar_summaries): 无')
        }
        
        // 相关词汇总结
        if (vocab_summaries && vocab_summaries.length > 0) {
          console.log('📖 相关词汇总结 (vocab_summaries):', vocab_summaries.length, '个')
          vocab_summaries.forEach((v, idx) => {
            console.log(`  ${idx + 1}. ${v.vocab}`)
            console.log(`     - 翻译: ${v.translation || '无'}`)
          })
        } else {
          console.log('📖 相关词汇总结 (vocab_summaries): 无')
        }
        
        // 例句
        if (examples && examples.length > 0) {
          console.log('📝 例句 (examples):', examples.length, '个')
          examples.forEach((ex, idx) => {
            console.log(`  ${idx + 1}. ${ex.example || ex.sentence || ex}`)
            if (ex.translation) {
              console.log(`     译文: ${ex.translation}`)
            }
          })
        } else {
          console.log('📝 例句 (examples): 无')
        }
        
        console.log('='.repeat(80) + '\n')
        
        // 🔧 注意：AI 回答已在上面立即显示（第255-267行），这里不再重复显示
        
        // 显示总结的语法和词汇（通过 Toast）
        const summaryItems = []
        
        if (grammar_to_add && grammar_to_add.length > 0) {
          grammar_to_add.forEach(g => {
            summaryItems.push(`🆕 语法: ${g.name}`)
          })
        }
        
        if (vocab_to_add && vocab_to_add.length > 0) {
          vocab_to_add.forEach(v => {
            summaryItems.push(`🆕 词汇: ${v.vocab}`)
          })
        }
        
        if (grammar_summaries && grammar_summaries.length > 0) {
          grammar_summaries.forEach(g => {
            summaryItems.push(`📚 语法: ${g.name}`)
          })
        }
        
        if (vocab_summaries && vocab_summaries.length > 0) {
          vocab_summaries.forEach(v => {
            summaryItems.push(`📖 词汇: ${v.vocab}`)
          })
        }
        
        // 逐个显示 Toast
        summaryItems.forEach((item, idx) => {
          setTimeout(() => {
            showKnowledgeToast(item)
          }, idx * 600)
        })
      } else {
        console.error('❌ [Frontend] Chat request failed or returned empty response')
        console.error('  Response:', response)
        // 显示错误消息
        const errorMessage = {
          id: generateMessageId(),
          text: `抱歉，处理您的问题时出现错误或返回了空响应`,
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      }
      
      // ✅ 不再自动清空引用 - 保持引用以便用户继续追问
      // 引用会在用户选择新的 token 或点击文章空白处时自动更新/清空
      console.log('✅ [ChatView] 消息发送完成，保持引用以便继续追问')
      
      // 🔧 处理完成，重置处理状态
      setIsProcessing(false)
    } catch (error) {
      console.error('💥 [Frontend] ❌❌❌ Chat request 发生错误 (handleSendMessage) ❌❌❌')
      console.error('💥 [Frontend] 错误对象:', error)
      console.error('💥 [Frontend] 错误消息:', error.message)
      console.error('💥 [Frontend] 错误堆栈:', error.stack)
      if (error.response) {
        console.error('💥 [Frontend] 响应状态:', error.response.status)
        console.error('💥 [Frontend] 响应数据:', error.response.data)
      }
      
      // 检查是否是超时错误
      let errorMessage = '发送消息时发生错误'
      if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
        errorMessage = '请求超时，AI 处理时间过长。请尝试简化问题或稍后重试。'
        console.warn('⏰ [Frontend] 检测到超时错误，建议用户简化问题')
      } else if (error.message.includes('timeout')) {
        errorMessage = '请求超时，请检查网络连接或稍后重试。'
      } else if (error.response?.status === 500) {
        // 尝试从响应中获取详细错误信息
        const errorData = error.response?.data
        if (errorData?.error) {
          errorMessage = `服务器错误: ${errorData.error}`
        } else if (errorData?.data?.error) {
          errorMessage = `服务器错误: ${errorData.data.error}`
        } else {
          errorMessage = '服务器内部错误，请稍后重试。'
        }
        console.error('💥 [Frontend] 服务器错误详情:', errorData)
      } else if (error.response?.status === 503) {
        errorMessage = '服务暂时不可用，请稍后重试。'
      } else if (error.response?.data?.error) {
        // 尝试从响应中获取错误信息
        errorMessage = error.response.data.error
      }
      
      // 显示错误消息
      const errorMsg = {
        id: Date.now() + 1,
        text: `抱歉，处理您的问题时出现错误: ${errorMessage}`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
      
      // ✅ 即使出错也不清空引用，保持引用以便用户重试
      
      // 🔧 处理完成（即使出错），重置处理状态
      setIsProcessing(false)
    */
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleToastClose = () => {
    setShowToast(false)
    setToastMessage('')
  }

  // 🔧 解析 AI 响应，去除 JSON 符号
  const parseAIResponse = (responseText) => {
    if (!responseText) return ''
    
    // 如果响应是对象，直接提取 answer 字段
    if (typeof responseText === 'object' && responseText.answer) {
      return responseText.answer
    }
    
    // 如果响应是字符串，尝试解析 JSON
    if (typeof responseText === 'string') {
      const trimmed = responseText.trim()
      
      // 尝试使用 JSON.parse（处理标准 JSON 格式 {"answer": "..."}）
      try {
        const parsed = JSON.parse(trimmed)
        if (parsed && typeof parsed === 'object' && parsed.answer) {
          return parsed.answer
        }
      } catch (e) {
        // 不是标准 JSON，继续处理
      }
      
      // 尝试匹配 {'answer': '...'} 或 {"answer": "..."} 格式
      // 使用更可靠的方法：手动解析字符串
      if (trimmed.startsWith('{') && (trimmed.includes("'answer'") || trimmed.includes('"answer"'))) {
        // 找到 'answer': ' 或 "answer": " 的位置
        const answerKeyPattern = /['"]answer['"]\s*:\s*['"]/
        const keyMatch = trimmed.match(answerKeyPattern)
        
        if (keyMatch) {
          const startIndex = keyMatch.index + keyMatch[0].length
          const quoteChar = trimmed[startIndex - 1] // 获取引号字符（' 或 "）
          
          // 从开始位置向后查找，找到匹配的结束引号（考虑转义）
          let endIndex = startIndex
          let escaped = false
          let foundEnd = false
          
          while (endIndex < trimmed.length) {
            const char = trimmed[endIndex]
            if (escaped) {
              escaped = false
            } else if (char === '\\') {
              escaped = true
            } else if (char === quoteChar) {
              // 找到结束引号
              foundEnd = true
              break
            }
            endIndex++
          }
          
          if (foundEnd) {
            const answer = trimmed.substring(startIndex, endIndex)
            // 处理转义字符
            let processed = answer
            processed = processed.replace(/\\n/g, '\n')
            processed = processed.replace(/\\'/g, "'")
            processed = processed.replace(/\\"/g, '"')
            processed = processed.replace(/\\\\/g, '\\')
            processed = processed.replace(/\\t/g, '\t')
            processed = processed.replace(/\\r/g, '\r')
            return processed
          }
        }
      }
      
      // 如果以上方法都失败，尝试简单的正则匹配（作为后备方案）
      // 匹配 {'answer': '...'} 格式，支持多行（但可能不准确处理转义）
      // 🔧 改进：使用非贪婪匹配，但需要找到最后一个匹配的引号（在 } 之前）
      const simpleMatch = trimmed.match(/['"]answer['"]\s*:\s*['"](.*?)['"]\s*\}/s)
      if (simpleMatch && simpleMatch[1]) {
        let answer = simpleMatch[1]
        // 处理常见的转义字符
        answer = answer.replace(/\\n/g, '\n')
        answer = answer.replace(/\\'/g, "'")
        answer = answer.replace(/\\"/g, '"')
        answer = answer.replace(/\\\\/g, '\\')
        answer = answer.replace(/\\t/g, '\t')
        answer = answer.replace(/\\r/g, '\r')
        return answer
      }
      
      // 🔧 新增：如果字符串以 {'answer': 开头，尝试从最后一个 '} 向前查找
      // 这样可以处理内容中包含引号的情况
      if (trimmed.startsWith("{'answer'") || trimmed.startsWith('{"answer"')) {
        // 找到最后一个 } 的位置
        const lastBraceIndex = trimmed.lastIndexOf('}')
        if (lastBraceIndex > 0) {
          // 从 'answer': ' 之后到最后一个 } 之前的内容
          const answerKeyPattern = /['"]answer['"]\s*:\s*['"]/
          const keyMatch = trimmed.match(answerKeyPattern)
          if (keyMatch) {
            const startIndex = keyMatch.index + keyMatch[0].length
            // 从最后一个 } 向前查找匹配的引号
            let endIndex = lastBraceIndex - 1
            const quoteChar = trimmed[startIndex - 1]
            
            // 从后向前查找匹配的引号（跳过空格）
            while (endIndex >= startIndex && trimmed[endIndex] !== quoteChar) {
              endIndex--
            }
            
            if (endIndex >= startIndex) {
              const answer = trimmed.substring(startIndex, endIndex)
              // 处理转义字符
              let processed = answer
              processed = processed.replace(/\\n/g, '\n')
              processed = processed.replace(/\\'/g, "'")
              processed = processed.replace(/\\"/g, '"')
              processed = processed.replace(/\\\\/g, '\\')
              processed = processed.replace(/\\t/g, '\t')
              processed = processed.replace(/\\r/g, '\r')
              return processed
            }
          }
        }
      }
    }
    
    // 否则返回原始文本（如果原始文本是 {'answer': '...'} 格式，至少显示一些内容）
    // 🔧 改进：如果原始文本看起来是字典格式，尝试提取一些内容
    if (typeof responseText === 'string' && responseText.includes("'answer'") && responseText.includes(':')) {
      // 至少返回一些提示，而不是整个字典字符串
      const match = responseText.match(/['"]answer['"]\s*:\s*['"](.{1,200})/)
      if (match && match[1]) {
        return match[1] + '...'
      }
    }
    
    return responseText
  }

  const handleSuggestedQuestionSelect = async (question) => {
    // 🔧 如果正在处理，禁止发送新的提问
    if (isProcessing) {
      console.log('⚠️ [ChatView] Main assistant 正在处理中，禁止发送新的提问')
      return
    }
    
    // 🔧 设置处理状态为 true
    setIsProcessing(true)
    
    // 🔧 保存当前的引用文本和上下文（用于 UI 显示）
    const currentQuotedText = quotedText
    const currentSelectionContext = selectionContext
    
    // 🔧 关键：如果有新的选择上下文，先更新 session state，确保后端使用最新的句子
    // 这样可以避免使用旧的 session state 中的句子
    if (currentSelectionContext && currentSelectionContext.sentence) {
      console.log('🔧 [ChatView] 检测到新的选择上下文（建议问题），先更新 session state 以确保使用最新句子...')
      try {
        const { apiService } = await import('../../../services/api')
        const preUpdatePayload = {
          sentence: currentSelectionContext.sentence
        }
        
        // 添加token信息（如果有）
        if (currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
          if (currentSelectionContext.tokens.length > 1) {
            preUpdatePayload.token = {
              multiple_tokens: currentSelectionContext.tokens,
              token_indices: currentSelectionContext.tokenIndices,
              token_text: currentSelectionContext.selectedTexts.join(' ')
            }
          } else {
            const token = currentSelectionContext.tokens[0]
            preUpdatePayload.token = {
              token_body: token.token_body,
              sentence_token_id: token.sentence_token_id
            }
          }
        } else {
          // 如果只选择了句子而没有token，清除旧的token
          preUpdatePayload.token = null
        }
        
        await apiService.session.updateContext(preUpdatePayload)
        console.log('✅ [ChatView] Session state 已更新为最新选择（建议问题）')
      } catch (error) {
        console.error('❌ [ChatView] 更新 session state 失败（建议问题）:', error)
        // 继续执行，不阻止发送消息
      }
    }
    
    // 自动发送已选择的问题
    const userMessage = {
      id: generateMessageId(),
      text: question,
      isUser: true,
      timestamp: new Date(),
      quote: currentQuotedText || null
    }
    
    // 🔧 关键修复：在调用 setMessages 之前就更新全局 ref
    const currentMessages = messagesRef.current || window.chatViewMessagesRef || []
    const newMessages = [...currentMessages, userMessage]
    messagesRef.current = newMessages
    window.chatViewMessagesRef = newMessages
    
    setMessages(prev => {
      // 🔧 检查是否已经存在相同的消息（避免重复添加）
      const exists = prev.some(m => m.id === userMessage.id)
      if (exists) {
        return prev
      }
      return [...prev, userMessage]
    })

    // 调用后端 chat API（与 handleSendMessage 相同的逻辑）
    try {
      
      const { apiService } = await import('../../../services/api')
      
      // 🔧 关键修复：只更新 current_input，不更新句子和token
      // 因为句子和token已经在选择时更新了（或者在发送前刚刚更新）
      // 这样可以确保使用后端当前已设置的 session state，而不是前端可能已过时的上下文
      const updatePayload = {
        current_input: question
      }
      
      console.log('💬 [ChatView] 只更新 current_input（建议问题），使用后端当前已设置的 session state')
      console.log('💬 [ChatView] 当前选择上下文（仅用于日志，建议问题）:', {
        hasContext: !!currentSelectionContext,
        sentenceId: currentSelectionContext?.sentence?.sentence_id,
        sentenceBody: currentSelectionContext?.sentence?.sentence_body?.substring(0, 50),
        tokenCount: currentSelectionContext?.tokens?.length || 0
      })
      
      const updateResponse = await apiService.session.updateContext(updatePayload)
      console.log('✅ [ChatView] Session context 更新完成（仅更新 current_input，建议问题）:', updateResponse)
      
      // 调用 chat 接口
      const response = await apiService.sendChat({
        user_question: question
      })
      
      console.log('✅ [Frontend] Chat response received:', response)
      
      // 🔧 立即显示 AI 回答（不等待后续流程）
      if (response && response.ai_response) {
        document.title = '显示 AI 回答...'
        console.log('🔍 [ChatView] 原始 AI 响应（建议问题）:', {
          type: typeof response.ai_response,
          value: response.ai_response,
          isString: typeof response.ai_response === 'string',
          isObject: typeof response.ai_response === 'object',
          stringLength: typeof response.ai_response === 'string' ? response.ai_response.length : 0
        })
        // 🔧 解析 AI 响应，去除 JSON 符号
        const parsedResponse = parseAIResponse(response.ai_response)
        console.log('🔍 [ChatView] 解析后的 AI 响应（建议问题）:', {
          parsed: parsedResponse,
          length: parsedResponse?.length || 0,
          isEmpty: !parsedResponse || parsedResponse.trim() === ''
        })
        
        // 🔧 如果解析失败或为空，使用原始响应或尝试其他方式
        let finalResponse = parsedResponse
        if (!finalResponse || finalResponse.trim() === '') {
          if (typeof response.ai_response === 'string') {
            finalResponse = response.ai_response
          } else if (typeof response.ai_response === 'object' && response.ai_response.answer) {
            finalResponse = response.ai_response.answer
          } else {
            finalResponse = JSON.stringify(response.ai_response)
          }
          console.log('⚠️ [ChatView] 解析失败，使用备用响应（建议问题）:', {
            finalResponse: finalResponse?.substring(0, 100)
          })
        }
        
        const aiMessage = {
          id: generateMessageId(),
          text: finalResponse,
          isUser: false,
          timestamp: new Date()
        }
        console.log('✅ [ChatView] 创建的 AI 消息（建议问题）:', {
          id: aiMessage.id,
          textLength: aiMessage.text?.length || 0,
          textPreview: aiMessage.text?.substring(0, 100) || ''
        })
        
        // 🔧 关键修复：统一消息添加逻辑，确保消息正确显示
        const currentMessages = messagesRef.current || window.chatViewMessagesRef || []
        const exists = currentMessages.some(m => m.id === aiMessage.id)
        
        if (!exists) {
          // 🔧 创建新消息列表，并按时间升序排序（确保显示顺序正确）
          const newMessages = [...currentMessages, aiMessage].sort(
            (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
          )
          
          // 🔧 先更新全局 ref
          messagesRef.current = newMessages
          window.chatViewMessagesRef = newMessages
          
          // 🔧 同步到 localStorage（保存时按降序，保留最新的200条）
          const allFromLS = loadAllMessagesFromLS()
          const withoutCurrent = allFromLS.filter(m => !newMessages.some(n => n.id === m.id))
          const merged = [...withoutCurrent, ...newMessages.map(m => ({ ...m, articleId }))]
          merged.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
          const trimmed = merged.slice(0, 200)
          saveAllMessagesToLS(trimmed)
          
          // 🔧 使用函数式更新，但基于最新的全局 ref
          setMessages(() => {
            console.log('✅ [ChatView] setMessages 执行（建议问题）', {
              newLength: newMessages.length,
              messageId: aiMessage.id
            })
            return newMessages
          })
          
          console.log('✅ [ChatView] AI 消息已添加到状态（建议问题）', {
            newLength: newMessages.length,
            messageId: aiMessage.id
          })
        } else {
          console.log('⚠️ [ChatView] AI 消息已存在，确保状态同步（建议问题）', {
            messageId: aiMessage.id,
            currentLength: currentMessages.length
          })
          // 🔧 即使消息已存在，也确保状态同步
          if (currentMessages.length > messages.length) {
            setMessages([...currentMessages])
          }
        }
        
        document.title = 'AI 回答已显示'
        console.log('📺 [ChatView] AI 回答已立即显示（建议问题）')
        
        // 🔧 关键修复：在显示 AI 回答后立即重置处理状态，不等待后续的 toast 轮询
        setIsProcessing(false)
        console.log('✅ [ChatView] isProcessing 已重置为 false（建议问题，AI 回答显示后）')
      } else {
        // 🔧 如果没有 ai_response，也重置处理状态
        console.warn('⚠️ [ChatView] 响应中没有 ai_response（建议问题），重置处理状态')
        setIsProcessing(false)
      }
      
      // 🔧 立即添加 notations 到缓存（如果有）
      document.title = '添加 notations...'
      if (response?.created_grammar_notations && response.created_grammar_notations.length > 0) {
        console.log('➕ [ChatView] Adding grammar notations (建议问题):', response.created_grammar_notations)
        response.created_grammar_notations.forEach(n => {
          console.log('Adding notation:', n)
          if (addGrammarNotationToCache) addGrammarNotationToCache(n)
        })
        document.title = `Added ${response.created_grammar_notations.length} grammar notations`
      }
      if (response?.created_vocab_notations && response.created_vocab_notations.length > 0) {
        console.log('➕ [ChatView] ========== 开始处理 vocab notations (建议问题) ==========')
        console.log('➕ [ChatView] 接收到的 created_vocab_notations:', JSON.stringify(response.created_vocab_notations, null, 2))
        console.log('➕ [ChatView] addVocabNotationToCache 函数类型:', typeof addVocabNotationToCache)
        
        response.created_vocab_notations.forEach((n, index) => {
          console.log(`➕ [ChatView] 处理第 ${index + 1} 个 vocab notation (建议问题):`, n)
          // 🔧 字段名映射：后端返回 token_id，前端期望 token_index
          const mappedNotation = {
            ...n,
            token_index: n.token_id || n.token_index  // 添加 token_index 字段
          }
          console.log(`➕ [ChatView] 映射后的 notation ${index + 1} (建议问题):`, mappedNotation)
          
          if (addVocabNotationToCache) {
            console.log(`➕ [ChatView] 调用 addVocabNotationToCache 添加第 ${index + 1} 个 notation (建议问题)`)
            addVocabNotationToCache(mappedNotation)
            console.log(`✅ [ChatView] addVocabNotationToCache 调用完成（第 ${index + 1} 个，建议问题）`)
          } else {
            console.error('❌ [ChatView] addVocabNotationToCache 函数不存在（建议问题）！')
          }
        })
        console.log('➕ [ChatView] ========== vocab notations 处理完成 (建议问题) ==========')
        document.title = `Added ${response.created_vocab_notations.length} vocab notations`
      } else {
        console.log('⚠️ [ChatView] 响应中没有 created_vocab_notations 或为空 (建议问题):', {
          hasCreatedVocabNotations: !!response?.created_vocab_notations,
          length: response?.created_vocab_notations?.length || 0,
          created_vocab_notations: response?.created_vocab_notations
        })
      }
      
      // 🔧 移除旧的轮询机制（检查 notations），改用新的 pending-knowledge API 轮询
      // 新的轮询机制在下面的 toast 处理逻辑中统一实现
      
      // 🔧 检查是否有新创建的 notations
      const hasGrammarNotations = response?.created_grammar_notations && Array.isArray(response.created_grammar_notations) && response.created_grammar_notations.length > 0
      const hasVocabNotations = response?.created_vocab_notations && Array.isArray(response.created_vocab_notations) && response.created_vocab_notations.length > 0
      
      // 🔧 自动刷新 grammar/vocab 列表（如果有新数据或新notations）
      const hasNewGrammar = response?.grammar_to_add && response.grammar_to_add.length > 0
      const hasNewVocab = response?.vocab_to_add && response.vocab_to_add.length > 0
      
      // 如果有新语法被创建，或者有新的 grammar notation（为现有语法添加例句），都刷新
      if (hasNewGrammar || hasGrammarNotations) {
        console.log('🔄 [ChatView] 检测到新语法或grammar notation，自动刷新 grammar 列表 (建议问题)...')
        refreshGrammar()
      }
      
      // 如果有新词汇被创建，或者有新的 vocab notation（为现有词汇添加例句），都刷新
      if (hasNewVocab || hasVocabNotations) {
        console.log('🔄 [ChatView] 检测到新词汇或vocab notation，自动刷新 vocab 列表 (建议问题)...')
        refreshVocab()
      }
      
      // 标记选中的tokens为已提问
      console.log('🔍 [DEBUG] 检查标记条件（建议问题）:', {
        hasMarkAsAsked: !!markAsAsked,
        hasContext: !!currentSelectionContext,
        hasTokens: !!(currentSelectionContext?.tokens),
        tokenCount: currentSelectionContext?.tokens?.length,
        articleId: articleId
      })
      
      if (markAsAsked && currentSelectionContext && currentSelectionContext.tokens && currentSelectionContext.tokens.length > 0) {
        console.log('✅ [ChatView] 进入标记逻辑（建议问题）')
        console.log('🏷️ [ChatView] Checking if tokens should be marked as asked (suggested question)...')
        
        // 从响应中提取 vocab_id（如果有新词汇）
        const vocabIdMap = new Map()
        if (response && response.vocab_to_add && Array.isArray(response.vocab_to_add)) {
          response.vocab_to_add.forEach(v => {
            if (v.vocab && v.vocab_id) {
              vocabIdMap.set(v.vocab.toLowerCase(), v.vocab_id)
            }
          })
          console.log('📝 [ChatView] Vocab ID map (建议问题):', Object.fromEntries(vocabIdMap))
        }
        
        // 获取所有新生成的词汇（vocab_to_add中的词汇对应的tokens）
        const newVocabTokens = new Set()
        if (response && response.vocab_to_add && Array.isArray(response.vocab_to_add)) {
          response.vocab_to_add.forEach(v => {
            // 将词汇名转换为小写，用于匹配
            if (v.vocab) {
              newVocabTokens.add(v.vocab.toLowerCase())
            }
          })
        }
        console.log('📋 [ChatView] New vocab tokens (建议问题):', Array.from(newVocabTokens))
        
        // 只标记那些在vocab_to_add中的tokens
        const markPromises = currentSelectionContext.tokens.map(async (token, tokenIdx) => {
          // 使用fallback确保字段存在
          const sentenceTokenId = token.sentence_token_id ?? (tokenIdx + 1)
          const sentenceId = currentSelectionContext.sentence?.sentence_id
          const textId = currentSelectionContext.sentence?.text_id ?? articleId  // ← 使用articleId作为fallback
          
          // 尝试查找 vocab_id
          const tokenBody = token.token_body?.toLowerCase() || ''
          const vocabId = vocabIdMap.get(tokenBody) || null
          
          // 检查该token是否在新生成的词汇中
          const shouldMark = newVocabTokens.has(tokenBody)
          
          console.log(`🔍 [DEBUG] Token ${tokenIdx} (建议问题):`, {
            token_body: token.token_body,
            textId,
            sentenceId,
            sentenceTokenId,
            vocabId,
            shouldMark,
            reason: shouldMark ? '在vocab_to_add中' : '不在vocab_to_add中'
          })
          
          if (shouldMark && sentenceId && textId && sentenceTokenId != null) {
            console.log(`🏷️ [ChatView] Marking token: "${token.token_body}" (${textId}:${sentenceId}:${sentenceTokenId}) with vocabId=${vocabId}`)
            
            // 优先使用新API创建vocab notation
            if (createVocabNotation) {
              console.log('✅ [ChatView] Using new API (createVocabNotation) - 建议问题')
              const result = await createVocabNotation(textId, sentenceId, sentenceTokenId, vocabId)
              if (result.success) {
                console.log('✅ [ChatView] Vocab notation created via new API (建议问题):', result.notation)
                return true
              } else {
                console.warn('⚠️ [ChatView] Failed to create vocab notation via new API (建议问题), falling back to old API')
                // 回退到旧API
                if (markAsAsked) {
                  return markAsAsked(textId, sentenceId, sentenceTokenId, vocabId)
                }
                return false
              }
            } else if (markAsAsked) {
              // 如果没有新API，使用旧API（向后兼容）
              console.log('⚠️ [ChatView] Using old API (markAsAsked) - new API not available - 建议问题')
              return markAsAsked(textId, sentenceId, sentenceTokenId, vocabId)
            } else {
              console.error('❌ [ChatView] No API available to mark token (建议问题)')
              return false
            }
          } else {
            console.log(`⏭️ [ChatView] Skipping token: "${token.token_body}" - ${shouldMark ? 'missing fields' : 'not in vocab example'}`)
            return Promise.resolve(false)
          }
        })
        
        try {
          const results = await Promise.all(markPromises)
          const successCount = results.filter(r => r).length
          const usedNewAPI = createVocabNotation !== null
          
          console.log(`✅ [ChatView] Successfully marked ${successCount}/${markPromises.length} tokens (建议问题, usedNewAPI=${usedNewAPI})`)
          
          // 如果标记成功
          if (successCount > 0) {
            if (usedNewAPI) {
              // 使用新API时，vocab notation已经实时添加到缓存，不需要刷新
              console.log('✅ [ChatView] Vocab notations already updated in cache via new API (建议问题), skipping refresh')
              
              // 只刷新vocab数据（如果有新创建的vocab例子）
              try {
                console.log('🔄 [ChatView] Refreshing vocab data (建议问题)...')
                await apiService.refreshVocab()
                console.log('✅ [ChatView] Vocab data refreshed successfully (建议问题)')
              } catch (err) {
                console.warn('⚠️ [ChatView] Failed to refresh vocab data (建议问题):', err)
              }
            } else {
              // 使用旧API时，需要刷新asked tokens和vocab数据
              console.log('⏳ [ChatView] Waiting for backend to save vocab data (old API, 建议问题)...')
              
              // 等待500ms确保后端异步保存完成
              await new Promise(resolve => setTimeout(resolve, 500))
              
              // 刷新vocab数据和asked tokens
              try {
                console.log('🔄 [ChatView] Refreshing vocab data and asked tokens (old API, 建议问题)...')
                await apiService.refreshVocab()
                console.log('✅ [ChatView] Vocab data refreshed successfully (建议问题)')
                
                // 同时刷新asked tokens状态
                if (refreshAskedTokens) {
                  await refreshAskedTokens()
                  console.log('✅ [ChatView] Asked tokens refreshed successfully (建议问题)')
                }
              } catch (err) {
                console.warn('⚠️ [ChatView] Failed to refresh data (建议问题):', err)
              }
            }
            
            // 刷新grammar notations状态
            if (refreshGrammarNotations) {
              console.log('🔄 [ChatView] 开始刷新grammar notations (建议问题)...')
              try {
                await refreshGrammarNotations()
                console.log('✅ [ChatView] Grammar notations refreshed successfully (suggested question)')
              } catch (grammarError) {
                console.error('❌ [ChatView] Failed to refresh grammar notations (suggested question):', grammarError)
              }
            } else {
              console.warn('⚠️ [ChatView] refreshGrammarNotations function not available (suggested question)')
            }
            
            console.log('🎉 [ChatView] Token states updated - green underlines should be visible now (suggested question)')
          } else {
            console.warn('⚠️ [ChatView] 没有token被成功标记（建议问题）')
          }
        } catch (error) {
          console.error('❌ [ChatView] Error marking tokens as asked (suggested question):', error)
        }
      } else {
        console.warn('⚠️ [ChatView] 标记条件不满足（建议问题，未进入标记逻辑）')
      }
      
      // 添加session state调试信息
      console.log('🔍 [SESSION STATE DEBUG] After suggested question selection:')
      console.log('  - Question text:', question)
      console.log('  - Quoted text:', currentQuotedText || 'None')
      console.log('  - Update payload:', updatePayload)
      
      // 响应拦截器已经提取了 innerData，所以 response 直接就是 data
      if (response && response.ai_response !== undefined) {
        const { ai_response, grammar_summaries, vocab_summaries, grammar_to_add, vocab_to_add, examples, created_grammar_notations, created_vocab_notations } = response
        
        // 详细打印session state中的vocab/grammar/example状态
        console.log('\n' + '='.repeat(80))
        console.log('📊 [SESSION STATE] 本轮对话生成的知识点状态（建议问题）：')
        console.log('='.repeat(80))
        
        // 新增语法
        if (grammar_to_add && grammar_to_add.length > 0) {
          console.log('🆕 新增语法 (grammar_to_add):', grammar_to_add.length, '个')
          grammar_to_add.forEach((g, idx) => {
            console.log(`  ${idx + 1}. ${g.name}`)
            console.log(`     - 总结: ${g.summary || '无'}`)
            console.log(`     - 详情: ${g.explanation || '无'}`)
          })
        } else {
          console.log('🆕 新增语法 (grammar_to_add): 无')
        }
        
        // 新增词汇
        if (vocab_to_add && vocab_to_add.length > 0) {
          console.log('🆕 新增词汇 (vocab_to_add):', vocab_to_add.length, '个')
          vocab_to_add.forEach((v, idx) => {
            console.log(`  ${idx + 1}. ${v.vocab}`)
            console.log(`     - 翻译: ${v.translation || '无'}`)
            console.log(`     - 用法: ${v.usage || '无'}`)
          })
        } else {
          console.log('🆕 新增词汇 (vocab_to_add): 无')
        }
        
        // 检查 created_vocab_notations 和 created_grammar_notations
        console.log('🍞 [Toast Debug] created_vocab_notations:', created_vocab_notations)
        console.log('🍞 [Toast Debug] created_grammar_notations:', created_grammar_notations)
        
        // 相关语法总结
        if (grammar_summaries && grammar_summaries.length > 0) {
          console.log('📚 相关语法总结 (grammar_summaries):', grammar_summaries.length, '个')
          grammar_summaries.forEach((g, idx) => {
            console.log(`  ${idx + 1}. ${g.name}`)
            console.log(`     - 总结: ${g.summary || '无'}`)
          })
        } else {
          console.log('📚 相关语法总结 (grammar_summaries): 无')
        }
        
        // 相关词汇总结
        if (vocab_summaries && vocab_summaries.length > 0) {
          console.log('📖 相关词汇总结 (vocab_summaries):', vocab_summaries.length, '个')
          vocab_summaries.forEach((v, idx) => {
            console.log(`  ${idx + 1}. ${v.vocab}`)
            console.log(`     - 翻译: ${v.translation || '无'}`)
          })
        } else {
          console.log('📖 相关词汇总结 (vocab_summaries): 无')
        }
        
        // 例句
        if (examples && examples.length > 0) {
          console.log('📝 例句 (examples):', examples.length, '个')
          examples.forEach((ex, idx) => {
            console.log(`  ${idx + 1}. ${ex.example || ex.sentence || ex}`)
            if (ex.translation) {
              console.log(`     译文: ${ex.translation}`)
            }
          })
        } else {
          console.log('📝 例句 (examples): 无')
        }
        
        console.log('='.repeat(80) + '\n')
        
        // 🔧 注意：AI 回答已在上面立即显示（第1016-1027行），这里不再重复显示
        
        // Toast - 从响应中直接获取新创建的知识点
        // 🔧 统一处理 toast，避免重复显示
        const toastItems = []
        
        if (grammar_to_add && grammar_to_add.length > 0) {
          grammar_to_add.forEach(g => {
            if (g.name) {
              toastItems.push(`🆕 语法: ${g.name}`)
            }
          })
        }
        
        if (vocab_to_add && vocab_to_add.length > 0) {
          vocab_to_add.forEach(v => {
            if (v.vocab) {
              toastItems.push(`🆕 词汇: ${v.vocab}`)
            }
          })
        }
        
        // 如果响应中没有 vocab_to_add/grammar_to_add，但后台可能正在创建，启动轮询
        if (toastItems.length === 0) {
          // 🔧 轮询获取后台任务创建的新知识点
          let textId = currentSelectionContext?.sentence?.text_id || articleId
          // 确保 textId 是整数类型
          if (textId) {
            textId = parseInt(textId) || textId
          }
          // 从 localStorage 获取 user_id
          const storedUserId = typeof localStorage !== 'undefined' ? localStorage.getItem('user_id') : null
          const userId = storedUserId ? parseInt(storedUserId) : 2
          
          console.log('🍞 [Toast Debug] 启动轮询检测新知识点 (建议问题):', { userId, textId, articleId, currentSelectionContext: !!currentSelectionContext })
          
          // 确保 textId 存在
          if (!textId) {
            console.warn('⚠️ [Toast Debug] textId 不存在，无法启动轮询 (建议问题)')
          } else {
            let pollCount = 0
            const maxPolls = 10
            const pollInterval = 500
            
            const pollPendingKnowledge = setInterval(async () => {
              pollCount++
              console.log(`🍞 [Toast Debug] 轮询第 ${pollCount} 次，检查新知识点 (建议问题)...`)
              
              try {
                const { apiService } = await import('../../../services/api')
                const pendingResponse = await apiService.getPendingKnowledge(userId, textId)
                
                console.log('🍞 [Toast Debug] 轮询响应 (建议问题):', pendingResponse)
                console.log('🍞 [Toast Debug] 轮询响应类型 (建议问题):', typeof pendingResponse)
                console.log('🍞 [Toast Debug] 轮询响应 keys (建议问题):', pendingResponse ? Object.keys(pendingResponse) : 'null')
                
                // 🔧 处理响应格式：API 拦截器可能已经提取了内层 data
                let pending_grammar = []
                let pending_vocab = []
                
                if (pendingResponse) {
                  // 🔧 处理响应格式：API 拦截器已经保留了完整结构 { success: true, data: {...} }
                  if (pendingResponse.success !== undefined && pendingResponse.data) {
                    pending_grammar = pendingResponse.data.grammar_to_add || []
                    pending_vocab = pendingResponse.data.vocab_to_add || []
                    console.log('🍞 [Toast Debug] 从 success.data 中提取 (建议问题):', { pending_grammar, pending_vocab })
                  }
                  // 如果响应格式已经被拦截器提取为 { grammar_to_add: [], vocab_to_add: [] }
                  else if (pendingResponse.grammar_to_add !== undefined || pendingResponse.vocab_to_add !== undefined) {
                    pending_grammar = pendingResponse.grammar_to_add || []
                    pending_vocab = pendingResponse.vocab_to_add || []
                    console.log('🍞 [Toast Debug] 从直接字段中提取 (建议问题):', { pending_grammar, pending_vocab })
                  } else {
                    console.warn('🍞 [Toast Debug] 无法解析响应格式 (建议问题):', pendingResponse)
                  }
                } else {
                  console.warn('🍞 [Toast Debug] pendingResponse 为空 (建议问题)')
                }
                
                console.log('🍞 [Toast Debug] 解析后的数据 (建议问题):', { pending_grammar, pending_vocab })
                
                const pendingToasts = []
                
                if (pending_grammar && pending_grammar.length > 0) {
                  pending_grammar.forEach(g => {
                    if (g.name) {
                      pendingToasts.push(`🆕 语法: ${g.name}`)
                    }
                  })
                }
                
                if (pending_vocab && pending_vocab.length > 0) {
                  pending_vocab.forEach(v => {
                    if (v.vocab) {
                      pendingToasts.push(`🆕 词汇: ${v.vocab}`)
                    }
                  })
                }
                
                if (pendingToasts.length > 0) {
                  console.log('🍞 [Toast Debug] 从轮询获取到新知识点 (建议问题)，准备显示 toast:', pendingToasts)
                  pendingToasts.forEach((item, idx) => {
                    setTimeout(() => {
                      console.log('🍞 [Toast Debug] 调用 showKnowledgeToast (建议问题):', item)
                      showKnowledgeToast(item)
                    }, idx * 600)
                  })
                  clearInterval(pollPendingKnowledge)
                } else {
                  console.log('🍞 [Toast Debug] 没有新知识点需要显示 (建议问题)')
                }
              } catch (err) {
                console.warn('⚠️ [ChatView] 轮询获取新知识点失败 (建议问题):', err)
              }
              
              if (pollCount >= maxPolls) {
                console.log('🍞 [Toast Debug] 达到最大轮询次数，停止轮询 (建议问题)')
                clearInterval(pollPendingKnowledge)
              }
            }, pollInterval)
            
            // 5秒后自动停止轮询
            setTimeout(() => {
              clearInterval(pollPendingKnowledge)
            }, maxPolls * pollInterval)
          }
        } else if (toastItems.length > 0) {
          // 立即显示 toast
          console.log('🍞 [Toast Debug] 立即显示 toast (建议问题):', toastItems)
          toastItems.forEach((item, idx) => {
            setTimeout(() => {
              showKnowledgeToast(item)
            }, idx * 600)
          })
        }
      } else {
        console.error('❌ [Frontend] Chat request failed or returned empty response')
        console.error('  Response:', response)
        // 显示错误消息
        const errorMessage = {
          id: generateMessageId(),
          text: `抱歉，处理您的问题时出现错误或返回了空响应`,
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      }
      
      // ✅ 不再自动清空引用 - 保持引用以便用户继续追问
      console.log('✅ [ChatView] 建议问题发送完成，保持引用以便继续追问')
      
      // 🔧 处理完成，重置处理状态
      setIsProcessing(false)
    } catch (error) {
      console.error('💥 [Frontend] ❌❌❌ Chat request 发生错误 (handleSuggestedQuestionSelect) ❌❌❌')
      console.error('💥 [Frontend] 错误对象:', error)
      console.error('💥 [Frontend] 错误消息:', error.message)
      console.error('💥 [Frontend] 错误堆栈:', error.stack)
      if (error.response) {
        console.error('💥 [Frontend] 响应状态:', error.response.status)
        console.error('💥 [Frontend] 响应数据:', error.response.data)
      }
      
      // 检查是否是超时错误
      let errorMessage = '发送消息时发生错误'
      if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
        errorMessage = '请求超时，AI 处理时间过长。请尝试简化问题或稍后重试。'
        console.warn('⏰ [Frontend] 检测到超时错误，建议用户简化问题')
      } else if (error.message.includes('timeout')) {
        errorMessage = '请求超时，请检查网络连接或稍后重试。'
      } else if (error.response?.status === 500) {
        // 尝试从响应中获取详细错误信息
        const errorData = error.response?.data
        if (errorData?.error) {
          errorMessage = `服务器错误: ${errorData.error}`
        } else if (errorData?.data?.error) {
          errorMessage = `服务器错误: ${errorData.data.error}`
        } else {
          errorMessage = '服务器内部错误，请稍后重试。'
        }
        console.error('💥 [Frontend] 服务器错误详情:', errorData)
      } else if (error.response?.status === 503) {
        errorMessage = '服务暂时不可用，请稍后重试。'
      } else if (error.response?.data?.error) {
        // 尝试从响应中获取错误信息
        errorMessage = error.response.data.error
      }
      
      // 显示错误消息
      const errorMsg = {
        id: Date.now() + 1,
        text: `抱歉，处理您的问题时出现错误: ${errorMessage}`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMsg])
      
      // ✅ 即使出错也不清空引用，保持引用以便用户重试
      
      // 🔧 处理完成（即使出错），重置处理状态
      setIsProcessing(false)
    }
  }

  const handleQuestionClick = (question) => {
    // 当问题被点击时，可以在这里添加额外的逻辑
    console.log('Question clicked:', question)
  }

  const handleChatContainerClick = (e) => {
    // 如果点击的是聊天容器而不是输入框或建议问题，可以在这里添加逻辑
    // 目前这个功能由SuggestedQuestions组件内部处理
  }

  const formatTime = (date) => {
    // 🔧 处理 Date 对象或字符串（深拷贝后可能变成字符串）
    if (!date) return ''
    const dateObj = date instanceof Date ? date : new Date(date)
    if (isNaN(dateObj.getTime())) {
      return ''
    }
    return dateObj.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className={`w-80 flex flex-col bg-white rounded-lg shadow-md flex-shrink-0 relative ${disabled ? 'opacity-50' : ''}`}>
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg flex-shrink-0">
        <h2 className="text-lg font-semibold text-gray-800">
          {disabled ? '聊天助手 (暂时不可用)' : '聊天助手'}
        </h2>
        <p className="text-sm text-gray-600">
          {disabled ? '请先上传文章内容' : '随时为您提供帮助'}
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
        <div
          ref={scrollContainerRef}
          className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3"
        >
          {messages.length === 0 ? (
            <div className="text-center text-gray-400 py-8">
              <p>暂无消息</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs px-3 py-2 rounded-lg ${
                    message.isUser
                      ? 'bg-white text-gray-900 border border-gray-300 rounded-br-none'
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                  }`}
                >
                  {/* Quote display */}
                  {message.quote && (
                    <div 
                      className={`mb-2 p-2 rounded text-xs ${
                        message.isUser 
                          ? '' 
                          : 'bg-gray-200 text-gray-600'
                      }`}
                      style={message.isUser ? {
                        backgroundColor: colors.primary[100],
                        color: colors.semantic.text.primary
                      } : {}}
                    >
                      <div className="font-medium mb-1">引用</div>
                      <div className="italic">"{message.quote}"</div>
                    </div>
                  )}
                  
                  <p className="text-sm">{message.text}</p>
                  <p 
                    className={`text-xs mt-1 ${
                      message.isUser ? 'text-gray-500' : 'text-gray-500'
                    }`}
                  >
                    {formatTime(message.timestamp)}
                  </p>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Quote Display */}
      {quotedText && (
        <div 
          className={`px-4 py-2 border-t flex-shrink-0 ${hasSelectedSentence ? 'bg-green-50 border-green-200' : ''}`}
          style={!hasSelectedSentence ? {
            backgroundColor: colors.primary[50],
            borderColor: colors.primary[200]
          } : {}}
        >
          <div className="flex items-start gap-2">
            <div className="flex-1 min-w-0">
              <div 
                className={`text-xs font-medium mb-1 ${hasSelectedSentence ? 'text-green-600' : ''}`}
                style={!hasSelectedSentence ? {
                  color: colors.primary[600]
                } : {}}
              >
                {hasSelectedSentence ? '引用整句（继续提问将保持此引用）' : '引用（继续提问将保持此引用）'}
              </div>
              <div 
                className={`text-sm italic ${hasSelectedSentence ? 'text-green-800' : ''}`}
                style={{
                  ...(!hasSelectedSentence ? { color: colors.primary[800] } : {}),
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  wordBreak: 'break-word'
                }}
              >
                "{quotedText}"
              </div>
            </div>
            <button
              onClick={onClearQuote}
              className={`flex-shrink-0 p-1.5 rounded-lg transition-colors ${hasSelectedSentence ? 'hover:bg-green-100' : ''}`}
              style={!hasSelectedSentence ? {
                '--hover-bg': colors.primary[100]
              } : {}}
              onMouseEnter={(e) => {
                if (!hasSelectedSentence) {
                  e.currentTarget.style.backgroundColor = colors.primary[100]
                }
              }}
              onMouseLeave={(e) => {
                if (!hasSelectedSentence) {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }
              }}
              title="清空引用"
            >
              <svg 
                className={`w-4 h-4 ${hasSelectedSentence ? 'text-green-600' : ''}`} 
                style={!hasSelectedSentence ? {
                  color: colors.primary[600]
                } : {}}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Suggested Questions */}
      <SuggestedQuestions
        quotedText={quotedText}
        onQuestionSelect={handleSuggestedQuestionSelect}
        isVisible={!!quotedText}
        inputValue={inputText}
        onQuestionClick={handleQuestionClick}
        tokenCount={selectedTokenCount}
        hasSelectedSentence={hasSelectedSentence}
        disabled={isProcessing}
      />

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg flex-shrink-0">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              disabled ? "聊天暂时不可用" : 
              isProcessing ? "AI 正在处理中，请稍候..." :
              (!hasSelectedToken && !hasSelectedSentence) ? "请先选择文章中的词汇或句子" :
              (quotedText ? `回复引用："${quotedText}"` : "输入消息...")
            }
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
            style={{
              '--tw-ring-color': colors.primary[500]
            }}
            onFocus={(e) => {
              e.currentTarget.style.boxShadow = `0 0 0 2px ${colors.primary[500]}40`
            }}
            onBlur={(e) => {
              e.currentTarget.style.boxShadow = ''
            }}
            disabled={disabled || isProcessing || (!hasSelectedToken && !hasSelectedSentence)}
          />
          <button
            onClick={handleSendMessage}
            disabled={inputText.trim() === '' || disabled || isProcessing || (!hasSelectedToken && !hasSelectedSentence)}
            className="px-4 py-2 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors hover:brightness-95 active:brightness-90"
            style={{
              backgroundColor: colors.primary[600],
              '--tw-ring-color': colors.primary[300],
            }}
            title={(!hasSelectedToken && !hasSelectedSentence) ? "请先选择文章中的词汇或句子" : "发送消息"}
          >
            发送
          </button>
        </div>
      </div>

      {/* 🔧 重构：Toast Stack - 底部居中，固定槽位，避免上移 */}
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[9999] pointer-events-none" style={{ position: 'fixed', width: '100%', maxWidth: '100vw' }}>
        {/* 🔧 调试：显示toasts状态 */}
        {(() => {
          console.log('🍞 [Toast Debug] 渲染 Toast Stack，toasts.length:', toasts.length, 'toasts:', toasts)
          return null
        })()}
        {toasts.length > 0 && (
          <div className="text-xs text-red-500 mb-2 bg-white px-2 py-1 rounded" style={{ position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)', zIndex: 10001 }}>
            调试：toasts数量: {toasts.length} | IDs: [{toasts.map(t => t.id.toString().slice(-4)).join(', ')}]
          </div>
        )}
        {toasts.length > 0 ? (
          toasts.map(t => {
            console.log('🍞 [Toast Debug] 渲染 toast:', t)
            return (
          <div
            key={t.id}
            className="pointer-events-auto"
            style={{
              position: 'absolute',
                  bottom: `${t.slot * 80}px`, // 每个槽位 80px 间距
              left: '50%',
              transform: 'translateX(-50%)',
                  zIndex: 10000 + t.slot,
                  width: 'auto',
                  minWidth: '320px'
            }}
          >
            <ToastNotice
              message={t.message}
              isVisible={true}
                  duration={5000} // 5秒后自动关闭
                  onClose={() => {
                    console.log('🍞 [Toast Debug] Toast 关闭，ID:', t.id)
                    setToasts(prev => {
                      const newToasts = prev.filter(x => x.id !== t.id)
                      // 重新计算 slot
                      const reindexedToasts = newToasts.map((toast, index) => ({
                        ...toast,
                        slot: index
                      }))
                      toastsRef.current = reindexedToasts
                      window.chatViewToastsRef = reindexedToasts
                      return reindexedToasts
                    })
                  }}
            />
          </div>
            )
          })
        ) : (
          <div className="text-xs text-gray-400" style={{ position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)' }}>
            无 toasts (length: {toasts.length})
          </div>
        )}
      </div>
    </div>
  )
}



