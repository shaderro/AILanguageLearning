/**
 * ⚠️ IMPORTANT: Language Logic Safety Boundaries
 * 
 * UI language ≠ System language
 * 
 * This component uses useTranslate() for presentation-only purposes:
 * - Displaying UI labels, placeholders, and messages in the appropriate language
 * - Showing error messages and user-facing text
 * 
 * 🚫 STRICTLY FORBIDDEN:
 * - ❌ Do NOT affect data fetching logic (React Query, useArticle, useApi)
 * - ❌ Do NOT affect hooks lifecycle (enabled, queryKey, useEffect dependencies)
 * - ❌ Do NOT affect conditional rendering related to loading / error states
 * 
 * Language is presentation-only and MUST NOT affect:
 * - React Query queryKeys
 * - useArticle / useApi enabled states
 * - isLoading / early return logic
 * - Data fetching dependencies
 * - Component lifecycle hooks
 */

import { useState, useRef, useEffect, useCallback, memo, useMemo } from 'react'
import { flushSync, createPortal } from 'react-dom'
import ToastNotice from './ToastNotice'
import SuggestedQuestions from './SuggestedQuestions'
import { useChatEvent } from '../contexts/ChatEventContext'
import { useTranslationDebug } from '../../../contexts/TranslationDebugContext'
import { useRefreshData } from '../../../hooks/useApi'
import { useUiLanguage } from '../../../contexts/UiLanguageContext'
import { colors } from '../../../design-tokens'
import { useUser } from '../../../contexts/UserContext'
import { isTokenInsufficient } from '../../../utils/tokenUtils'
import authService from '../../auth/services/authService'
import { useTranslate } from '../../../i18n/useTranslate'
import { useUIText } from '../../../i18n/useUIText'

// 🔧 本地持久化
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
    console.warn('⚠️ [ChatView] 读取本地消息失败', e)
    return []
  }
}

const saveAllMessagesToLS = (messagesAll) => {
  try {
    localStorage.setItem(LS_KEY_CHAT_MESSAGES_ALL, JSON.stringify(messagesAll))
  } catch (e) {
    console.warn('⚠️ [ChatView] 写入本地消息失败', e)
  }
}

// 🔧 全局消息存储（按 articleId 分组）
if (!window.chatViewMessagesRef) {
  window.chatViewMessagesRef = {}
}

function ChatView({ 
  quotedText, 
  onClearQuote, 
  disabled = false, 
  hasSelectedToken = false, 
  selectedTokenCount = 1, 
  selectionContext = null, 
  markAsAsked = null,
  createVocabNotation = null,
  refreshAskedTokens = null, 
  refreshGrammarNotations = null, 
  articleId = null, 
  hasSelectedSentence = false, 
  selectedSentence = null,
  addGrammarNotationToCache = null,
  addVocabNotationToCache = null,
  addGrammarRuleToCache = null,
  addVocabExampleToCache = null,
  isProcessing: externalIsProcessing = null,
  onProcessingChange = null
}) {
  const { pendingMessage, clearPendingMessage, pendingContext, clearPendingContext, pendingToast, clearPendingToast } = useChatEvent()
  const { refreshGrammar, refreshVocab } = useRefreshData()
  const { addLog } = useTranslationDebug()
  const { token } = useUser()
  
  // 🔧 Token不足检查相关状态
  const [userInfo, setUserInfo] = useState(null)
  const [tokenInsufficient, setTokenInsufficient] = useState(false)
  
  // 🔧 可调整宽度功能
  const CHAT_WIDTH_STORAGE_KEY = 'chat_view_width'
  const MIN_CHAT_WIDTH = 280
  const MAX_CHAT_WIDTH = 600
  const DEFAULT_CHAT_WIDTH = 320 // w-80 = 320px
  
  const [chatWidth, setChatWidth] = useState(() => {
    try {
      const saved = localStorage.getItem(CHAT_WIDTH_STORAGE_KEY)
      if (saved) {
        const width = parseInt(saved, 10)
        if (width >= MIN_CHAT_WIDTH && width <= MAX_CHAT_WIDTH) {
          return width
        }
      }
    } catch (e) {
      console.warn('⚠️ [ChatView] 读取保存的宽度失败', e)
    }
    return DEFAULT_CHAT_WIDTH
  })
  
  const [isResizing, setIsResizing] = useState(false)
  const chatContainerRef = useRef(null)
  
  // 保存宽度到 localStorage
  useEffect(() => {
    try {
      localStorage.setItem(CHAT_WIDTH_STORAGE_KEY, String(chatWidth))
    } catch (e) {
      console.warn('⚠️ [ChatView] 保存宽度失败', e)
    }
  }, [chatWidth])
  
  // 处理拖拽调整宽度
  useEffect(() => {
    if (!isResizing) return
    
    const handleMouseMove = (e) => {
      if (!chatContainerRef.current) return
      
      const containerRect = chatContainerRef.current.getBoundingClientRect()
      const newWidth = containerRect.right - e.clientX
      
      if (newWidth >= MIN_CHAT_WIDTH && newWidth <= MAX_CHAT_WIDTH) {
        setChatWidth(newWidth)
      }
    }
    
    const handleMouseUp = () => {
      setIsResizing(false)
    }
    
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])
  
  const scrollContainerRef = useRef(null)
  const messageIdCounterRef = useRef(0)
  const pollPendingKnowledgeRef = useRef(null)  // 🔧 存储轮询定时器引用，用于清理
  const messagesRef = useRef([])
  const generateMessageId = () => {
    messageIdCounterRef.current += 1
    return Date.now() + Math.random() + messageIdCounterRef.current
  }
  
  const normalizedArticleId = articleId ? String(articleId) : 'default'

  const normalizeTextForSignature = (text) => String(text || '').replace(/\s+/g, ' ').trim()
  const isWelcomeMessageText = (text) => {
    const normalized = normalizeTextForSignature(text)
    return (
      normalized === normalizeTextForSignature("选择有疑问的句子或词汇，向我提问吧！") ||
      normalized === normalizeTextForSignature("你好！我是聊天助手，有什么可以帮助你的吗？")
    )
  }
  const getMessageSignature = (msg) => {
    const role = msg?.isUser ? 'user' : 'ai'
    const text = normalizeTextForSignature(msg?.text)
    const quote = normalizeTextForSignature(msg?.quote)
    return `${role}|${text}|${quote}`
  }
  const getMessageSignatureLoose = (msg) => {
    // 不包含 quote：用于识别“同一条问答被后端/前端以不同引用文本记录”的重复
    const role = msg?.isUser ? 'user' : 'ai'
    const text = normalizeTextForSignature(msg?.text)
    return `${role}|${text}`
  }
  const getMessageTimeMs = (msg) => {
    if (!msg?.timestamp) return 0
    const d = msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp)
    return Number.isNaN(d.getTime()) ? 0 : d.getTime()
  }
  const isLikelyDuplicateMessage = (a, b, timeWindowMs = 20000) => {
    if (!a || !b) return false
    const strictSame = getMessageSignature(a) === getMessageSignature(b)
    const looseSame = getMessageSignatureLoose(a) === getMessageSignatureLoose(b)
    if (!strictSame && !looseSame) return false
    const ta = getMessageTimeMs(a)
    const tb = getMessageTimeMs(b)
    // 允许前后 20 秒偏差，覆盖“本地立即插入 + 后端落库返回时间稍后”的重复场景
    return ta > 0 && tb > 0 ? Math.abs(ta - tb) <= timeWindowMs : true
  }
  const isLikelyDuplicateUserMessage = (a, b, timeWindowMs = 3000) => {
    if (!a || !b) return false
    if (!a.isUser || !b.isUser) return false
    // 用户消息去重必须带引用一起判断，避免“同样问题模板 + 不同引用”被误吞
    if (getMessageSignature(a) !== getMessageSignature(b)) return false
    const ta = getMessageTimeMs(a)
    const tb = getMessageTimeMs(b)
    // 仅用于防双击/重复触发，时间窗口缩短到 3 秒
    return ta > 0 && tb > 0 ? Math.abs(ta - tb) <= timeWindowMs : true
  }
  const sortMessagesStable = (arr) => {
    return [...arr].sort((a, b) => {
      const t = getMessageTimeMs(a) - getMessageTimeMs(b)
      if (t !== 0) return t
      const aId = String(a?.id ?? '')
      const bId = String(b?.id ?? '')
      return aId.localeCompare(bId)
    })
  }
  
  // Helper function to get translated text without hook (for initialization)
  const getTranslatedText = (key) => {
    try {
      const { translateText } = require('../../../i18n/useUIText')
      const savedLang = localStorage.getItem('ui_language') || 'zh'
      return translateText(key, savedLang)
    } catch (e) {
      // Fallback to Chinese if translation fails
      return key
    }
  }

  // 🔧 初始化消息：优先从全局 ref，否则从 localStorage
  const getInitialMessages = () => {
    const globalMessages = window.chatViewMessagesRef[normalizedArticleId] || []
    if (globalMessages.length > 0) {
      return globalMessages
    }
    
    const allFromLS = loadAllMessagesFromLS()
    const fromLS = normalizedArticleId !== 'default'
      ? allFromLS.filter(m => String(m.articleId) === normalizedArticleId)
          .map(({ articleId: _aid, ...rest }) => rest)
          .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      : allFromLS.filter(m => !m.articleId)
          .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
    
    // ⚠️ Language detection: Presentation-only, does NOT affect data fetching
    // Called at initialization time, NOT in render or hooks
    // Using translateText helper function (not hook) for initialization
    const defaultMessage = getTranslatedText("选择有疑问的句子或词汇，向我提问吧！")
    
    return fromLS.length > 0 ? fromLS : [
      { id: 1, text: defaultMessage, isUser: false, timestamp: new Date() }
    ]
  }
  
  const t = useTranslate()
  const tUI = useUIText()
  const { uiLanguage } = useUiLanguage()
  const [messages, setMessages] = useState(getInitialMessages)
  const [inputText, setInputText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  
  // 🔧 获取用户信息并检查token是否不足
  useEffect(() => {
    const fetchUserInfo = async () => {
      if (!token) {
        setUserInfo(null)
        setTokenInsufficient(false)
        return
      }
      
      try {
        const info = await authService.getCurrentUser(token)
        setUserInfo(info)
        // 检查token是否不足（只在没有main assistant流程时判断）
        if (!isProcessing) {
          const insufficient = isTokenInsufficient(info?.token_balance, info?.role)
          setTokenInsufficient(insufficient)
        }
      } catch (err) {
        console.error('获取用户信息失败:', err)
        setUserInfo(null)
        setTokenInsufficient(false)
      }
    }
    
    fetchUserInfo()
    // 定期刷新用户信息（每30秒）
    const interval = setInterval(fetchUserInfo, 30000)
    return () => clearInterval(interval)
  }, [token, isProcessing])
  
  // 🔧 当isProcessing状态变化时，重新检查token是否不足
  useEffect(() => {
    if (!isProcessing && userInfo) {
      const insufficient = isTokenInsufficient(userInfo.token_balance, userInfo.role)
      setTokenInsufficient(insufficient)
    }
  }, [isProcessing, userInfo])
  
  // 🔧 Toast 管理
  if (!window.chatViewToastsRef) {
    window.chatViewToastsRef = []
  }
  const [toasts, setToasts] = useState(() => window.chatViewToastsRef || [])
  
  // 🔧 优化：使用 useCallback 稳定 onClose 回调，避免每次渲染都创建新函数
  const handleToastClose = useCallback((toastId) => {
    setToasts(prev => {
      const newToasts = prev.filter(x => x.id !== toastId)
      const reindexed = newToasts.map((toast, index) => ({
        ...toast,
        slot: index
      }))
      window.chatViewToastsRef = reindexed
      return reindexed
    })
  }, [])
  
  // 🔧 同步全局 ref
  useEffect(() => {
    window.chatViewMessagesRef[normalizedArticleId] = messages
    messagesRef.current = messages
  }, [messages, normalizedArticleId])
  
  // 🔧 自动滚动到底部
  useEffect(() => {
    const container = scrollContainerRef.current
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  }, [messages.length])
  
  // 🔧 从后端加载历史记录（添加去重机制，避免重复请求）
  const loadingHistoryRef = useRef(false)
  useEffect(() => {
    if (!articleId || isProcessing || loadingHistoryRef.current) return
    
    console.log('💬 [ChatView] 尝试加载历史记录:', {
      articleId,
      isProcessing,
      loadingHistoryRef: loadingHistoryRef.current,
      currentMessagesCount: messages.length,
      normalizedArticleId,
    })
    
    loadingHistoryRef.current = true
    const loadHistory = async () => {
      try {
        const { apiService } = await import('../../../services/api')
        // 注意：apiService.getChatHistory 已经过 Axios 拦截器处理，直接返回 innerData（即 { items, count, ... }）
        const resp = await apiService.getChatHistory({ textId: articleId, limit: 200 })
        const items = resp?.items || []
        console.log('💬 [ChatView] /api/chat/history 响应:', {
          raw: resp,
          itemsLength: items.length,
          firstItem: items[0] || null,
        })
        
        if (items.length > 0) {
          // 🔧 与后端 /api/chat/history 的返回字段对齐：
          // backend 返回字段为 text / quote_text / is_user / created_at
          const defaultWelcome = getTranslatedText("选择有疑问的句子或词汇，向我提问吧！")
          const historyMessages = items.map(item => ({
            id: item.id,
            text: item.text, // 修复：使用后端返回的 text 字段，而不是不存在的 message
            isUser: item.is_user,
            timestamp: new Date(item.created_at),
            quote: item.quote_text || null
          }))
          
          console.log('💬 [ChatView] 映射后的 historyMessages:', {
            count: historyMessages.length,
            first: historyMessages[0] || null,
          })
          
          // 🔧 有历史记录时的策略：
          // - 如果当前只有一条本地欢迎语，则直接用历史记录替换（不再显示欢迎语）
          // - 否则合并并去重
          setMessages(prev => {
            console.log('💬 [ChatView] setMessages(before merge):', {
              prevCount: prev.length,
              prevSample: prev.slice(0, 3),
            })
            const isOnlyWelcome =
              prev.length === 1 &&
              !prev[0].isUser &&
              typeof prev[0].text === 'string' &&
              (prev[0].text === defaultWelcome || isWelcomeMessageText(prev[0].text))

            if (isOnlyWelcome) {
              // 直接用历史记录替换欢迎语
              const historySorted = sortMessagesStable(historyMessages)
              window.chatViewMessagesRef[normalizedArticleId] = historySorted
              console.log('💬 [ChatView] 检测到仅欢迎语，直接用历史记录替换:', {
                replacedCount: historySorted.length,
              })
              return historySorted
            }

            // 否则合并去重
            // 先按 ID 去重，再按“角色+文本+引用+时间窗口”去重，避免线上重复展示同一轮问答
            const existingIds = new Set(prev.map(m => m.id))
            
            const newMessages = historyMessages.filter(m => {
              // 检查ID是否已存在
              if (existingIds.has(m.id)) {
                return false
              }
              
              // 检查“同一条消息的不同来源副本”（本地 optimistic 与后端历史）
              const hasDuplicateByContent = prev.some(existing => isLikelyDuplicateMessage(existing, m))
              if (hasDuplicateByContent) {
                console.warn('⚠️ [ChatView] 历史记录中发现重复内容（不同ID），跳过:', {
                  historyId: m.id,
                  historyText: m.text?.substring(0, 50),
                  historyTimestamp: m.timestamp
                })
                return false
              }
              
              return true
            })
            
            // 有真实历史时，清理欢迎语，避免欢迎语插入到会话中间造成顺序错乱观感
            const prevWithoutWelcome =
              historyMessages.length > 0
                ? prev.filter(m => !(m && !m.isUser && isWelcomeMessageText(m.text)))
                : prev

            const merged = sortMessagesStable([...prevWithoutWelcome, ...newMessages])
            window.chatViewMessagesRef[normalizedArticleId] = merged
            console.log('💬 [ChatView] 合并历史记录:', {
              existingCount: prevWithoutWelcome.length,
              newMessagesCount: newMessages.length,
              mergedCount: merged.length,
              skippedByContent: historyMessages.length - newMessages.length - (historyMessages.length - historyMessages.filter(m => !existingIds.has(m.id)).length)
            })
            return merged
          })
        }
      } catch (error) {
        console.error('❌ [ChatView] 加载历史记录失败:', error)
      } finally {
        loadingHistoryRef.current = false
      }
    }
    
    loadHistory()
    
    // 🔧 组件卸载时清理轮询
    return () => {
      if (pollPendingKnowledgeRef.current) {
        clearInterval(pollPendingKnowledgeRef.current)
        pollPendingKnowledgeRef.current = null
      }
    }
  }, [articleId, normalizedArticleId])
  
  // 🔧 添加消息（立即显示）
  const addMessage = useCallback((newMessage) => {
    // 🔍 诊断日志：追踪消息添加
    const stackTrace = new Error().stack
    console.log('🔍 [ChatView] addMessage 被调用:', {
      messageId: newMessage.id,
      messageText: newMessage.text?.substring(0, 50) + '...',
      isUser: newMessage.isUser,
      timestamp: newMessage.timestamp,
      articleId: newMessage.articleId,
      normalizedArticleId,
      currentMessagesCount: messages.length,
      callStack: stackTrace?.split('\n').slice(1, 4).join(' -> ')
    })
    
    flushSync(() => {
      setMessages(prev => {
        // 🔍 诊断日志：检查是否已存在
        const existingMessage = prev.find(m => m.id === newMessage.id)
        if (existingMessage) {
          console.warn('⚠️ [ChatView] addMessage - 消息已存在，跳过添加:', {
            messageId: newMessage.id,
            existingMessage: {
              text: existingMessage.text?.substring(0, 50),
              timestamp: existingMessage.timestamp,
              isUser: existingMessage.isUser
            },
            newMessage: {
              text: newMessage.text?.substring(0, 50),
              timestamp: newMessage.timestamp,
              isUser: newMessage.isUser
            }
          })
          return prev
        }
        
        // 检查是否有相同内容但不同 ID 的消息（重复触发/并发返回）
        const duplicateContent = newMessage.isUser
          ? prev.find(m => isLikelyDuplicateUserMessage(m, newMessage))
          : prev.find(m => isLikelyDuplicateMessage(m, newMessage))
        if (duplicateContent) {
          const bothAI = !duplicateContent.isUser && !newMessage.isUser
          // AI 回答宁可偶发重复，也不能误杀导致“只显示提问不显示回答”
          if (bothAI) {
            console.warn('⚠️ [ChatView] addMessage - 检测到 AI 可能重复，保留本次消息以避免漏显示回答:', {
              existingId: duplicateContent.id,
              newId: newMessage.id,
              text: newMessage.text?.substring(0, 50)
            })
          } else {
          console.warn('⚠️ [ChatView] addMessage - 检测到重复内容（不同ID）:', {
            existingId: duplicateContent.id,
            newId: newMessage.id,
            text: newMessage.text?.substring(0, 50),
            timeDiff: Math.abs(new Date(duplicateContent.timestamp).getTime() - new Date(newMessage.timestamp).getTime())
          })
          return prev
          }
        }
        
        const updated = sortMessagesStable([...prev, newMessage])
        window.chatViewMessagesRef[normalizedArticleId] = updated
        
        console.log('✅ [ChatView] addMessage - 消息已添加:', {
          messageId: newMessage.id,
          prevCount: prev.length,
          updatedCount: updated.length,
          allMessageIds: updated.map(m => m.id)
        })
        
        return updated
      })
    })
    
    // 🔧 保存到 localStorage
    const allMessages = Object.values(window.chatViewMessagesRef).flat()
    const normalized = allMessages.map(m => ({
      ...m,
      articleId: m.articleId ? String(m.articleId) : undefined,
      timestamp: m.timestamp instanceof Date ? m.timestamp.toISOString() : m.timestamp
    }))
    const trimmed = normalized.slice(0, 200)
    saveAllMessagesToLS(trimmed)
  }, [normalizedArticleId, messages.length])
  
  // 🔧 保存消息到 localStorage
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      const allMessages = Object.values(window.chatViewMessagesRef).flat()
      const normalized = allMessages.map(m => ({
        ...m,
        articleId: m.articleId ? String(m.articleId) : undefined,
        timestamp: m.timestamp instanceof Date ? m.timestamp.toISOString() : m.timestamp
      }))
      const trimmed = normalized.slice(0, 200)
      saveAllMessagesToLS(trimmed)
    }, 500)
    
    return () => clearTimeout(timeoutId)
  }, [messages.length])
  
  // 🔧 修复问题3：防止重复处理 pendingMessage
  const processingPendingMessageRef = useRef(false)
  // 🔧 防止发送消息/建议问题被重复触发（setState 异步，isProcessing 可能尚未更新）
  const sendingRef = useRef(false)
  
  // 🔧 处理 pendingMessage（来自 useChatEvent）
  useEffect(() => {
    // 🔍 诊断日志：追踪 useEffect 触发
    console.log('🔍 [ChatView] useEffect(pendingMessage) 触发:', {
      hasPendingMessage: !!pendingMessage,
      pendingMessageText: pendingMessage?.text?.substring(0, 50),
      isProcessing,
      processingPendingMessageRef: processingPendingMessageRef.current,
      pendingContext: !!pendingContext
    })
    
    if (!pendingMessage || isProcessing || processingPendingMessageRef.current) {
      if (processingPendingMessageRef.current) {
        console.log('⏭️ [ChatView] 跳过重复处理 pendingMessage（正在处理中）')
      } else if (isProcessing) {
        console.log('⏭️ [ChatView] 跳过处理 pendingMessage（isProcessing=true）')
      } else if (!pendingMessage) {
        console.log('⏭️ [ChatView] 跳过处理 pendingMessage（pendingMessage为空）')
      }
      return
    }
    
    console.log('📥 [ChatView] 收到 pendingMessage，开始处理', {
      text: pendingMessage.text,
      quotedText: pendingMessage.quotedText,
      hasContext: !!pendingContext,
      timestamp: pendingMessage.timestamp
    })
    
    // 🔧 标记为正在处理，并立即清除 pending，避免因依赖变化导致 effect 再次用同一 pending 处理
    processingPendingMessageRef.current = true
    clearPendingMessage()
    clearPendingContext()
    console.log('🔍 [ChatView] 设置 processingPendingMessageRef.current = true，已清除 pending')
    
    // 🔧 自动发送消息
    const sendPendingMessage = async () => {
      const questionText = pendingMessage.text
      const currentQuotedText = pendingMessage.quotedText || quotedText
      const currentSelectionContext = pendingContext || selectionContext
      
      setIsProcessing(true)
      
      // 🔧 立即添加用户消息
      const userMessage = {
        id: generateMessageId(),
        text: questionText,
        isUser: true,
        timestamp: new Date(),
        quote: currentQuotedText || null,
        articleId: articleId ? String(articleId) : undefined  // 🔧 添加 articleId 用于跨设备同步
      }
      addMessage(userMessage)
      
      // 🔧 调用 API（合并 session 更新，避免重复请求）
      try {
        const { apiService } = await import('../../../services/api')
        
        // 🔧 合并 session 更新：将句子上下文和 current_input 合并到一次调用
        const sessionUpdatePayload = { current_input: questionText }
        
        if (currentSelectionContext?.sentence) {
          sessionUpdatePayload.sentence = currentSelectionContext.sentence
          
          if (currentSelectionContext.tokens?.length > 0) {
            if (currentSelectionContext.tokens.length > 1) {
              sessionUpdatePayload.token = {
                multiple_tokens: currentSelectionContext.tokens,
                token_indices: currentSelectionContext.tokenIndices,
                token_text: currentSelectionContext.selectedTexts.join(' ')
              }
            } else {
              const token = currentSelectionContext.tokens[0]
              sessionUpdatePayload.token = {
                token_body: token.token_body,
                sentence_token_id: token.sentence_token_id
              }
            }
          } else {
            sessionUpdatePayload.token = null
          }
        }
        
        // 🔧 一次性更新所有上下文，而不是分两次调用
        await apiService.session.updateContext(sessionUpdatePayload)
        
        // 🔧 传递 UI 语言参数，用于控制 AI 输出的语言
        const uiLanguageForBackend = uiLanguage === 'en' ? '英文' : '中文'
        const requestStartedAt = Date.now()
        const response = await apiService.sendChat({ 
          user_question: questionText,
          ui_language: uiLanguageForBackend
        })
        console.log(`🔍 [ChatView] sendPendingMessage - sendChat 响应:`, response)
        console.log(`🔍 [ChatView] sendPendingMessage - response.grammar_to_add:`, response?.grammar_to_add)
        console.log(`🔍 [ChatView] sendPendingMessage - response.vocab_to_add:`, response?.vocab_to_add)
        
        // 🔧 添加 AI 回答（字段兼容 + history 兜底）
        await appendAiReplyWithHistoryFallback({ response, apiService, requestStartedAt })
        
        // 🔧 处理 notations（与 handleSendMessage 相同）
        // 🔍 诊断日志：追踪 notation 添加
        if (response?.created_grammar_notations?.length > 0) {
          console.log('🔍 [ChatView] sendPendingMessage - 处理 grammar notations:', {
            count: response.created_grammar_notations.length,
            notations: response.created_grammar_notations.map(n => ({
              notation_id: n.notation_id,
              grammar_id: n.grammar_id,
              text_id: n.text_id,
              sentence_id: n.sentence_id
            }))
          })
          response.created_grammar_notations.forEach((n, idx) => {
            console.log(`🔍 [ChatView] sendPendingMessage - 添加 grammar notation ${idx + 1}/${response.created_grammar_notations.length}:`, {
              notation_id: n.notation_id,
              grammar_id: n.grammar_id,
              text_id: n.text_id,
              sentence_id: n.sentence_id
            })
            if (addGrammarNotationToCache) addGrammarNotationToCache(n)
          })
        }
        if (response?.created_vocab_notations?.length > 0) {
          console.log('🔍 [ChatView] sendPendingMessage - 处理 vocab notations:', {
            count: response.created_vocab_notations.length,
            notations: response.created_vocab_notations.map(n => ({
              notation_id: n.notation_id,
              vocab_id: n.vocab_id,
              text_id: n.text_id,
              sentence_id: n.sentence_id,
              token_index: n.token_id || n.token_index
            }))
          })
          response.created_vocab_notations.forEach((n, idx) => {
            console.log(`🔍 [ChatView] sendPendingMessage - 添加 vocab notation ${idx + 1}/${response.created_vocab_notations.length}:`, {
              notation_id: n.notation_id,
              vocab_id: n.vocab_id,
              text_id: n.text_id,
              sentence_id: n.sentence_id,
              token_index: n.token_id || n.token_index
            })
            if (addVocabNotationToCache) addVocabNotationToCache({
              ...n,
              token_index: n.token_id || n.token_index
            })
          })
        }
        
        if (response?.grammar_to_add?.length > 0 || response?.created_grammar_notations?.length > 0) {
          refreshGrammar()
        }
        if (response?.vocab_to_add?.length > 0 || response?.created_vocab_notations?.length > 0) {
          refreshVocab()
        }
        
        // 🔧 即时响应中的语法/词汇也显示知识点弹窗（部分用户后端直接返回 created_*_notations，不经过轮询）
        const immGrammar = response?.created_grammar_notations || []
        const immVocab = response?.created_vocab_notations || []
        if (immGrammar.length > 0 || immVocab.length > 0) {
          const items = []
          immGrammar.forEach((n) => {
            const name = n.rule_name || n.name || n.display_name || tUI('语法')
            items.push({ message: `🆕 ${tUI('语法')}: ${name} ${tUI('知识点已总结并加入列表')}`, key: `imm-g-${n.notation_id || n.grammar_id}` })
          })
          immVocab.forEach((n) => {
            const vocab = n.vocab || n.vocab_body || tUI('词汇')
            items.push({ message: `🆕 ${tUI('词汇')}: ${vocab} ${tUI('知识点已总结并加入列表')}`, key: `imm-v-${n.notation_id || n.vocab_id}` })
          })
          if (items.length > 0) {
            setToasts(prev => {
              const baseSlot = prev.length
              const newToasts = items.map((item, idx) => ({
                id: Date.now() + idx + Math.random() * 1000,
                message: item.message,
                slot: baseSlot + idx
              }))
              const updated = [...prev, ...newToasts]
              window.chatViewToastsRef = updated
              return updated
            })
          }
        }
        
        // 🔧 轮询新知识点（与 handleSendMessage 相同的逻辑）
        console.log(`🔍 [ChatView] sendPendingMessage - 检查轮询条件: response存在=${!!response}, grammar_to_add长度=${response?.grammar_to_add?.length || 0}, vocab_to_add长度=${response?.vocab_to_add?.length || 0}`)
        
        if (response && !response.grammar_to_add?.length && !response.vocab_to_add?.length) {
          const textId = currentSelectionContext?.sentence?.text_id || articleId
          const userId = parseInt(localStorage.getItem('user_id') || '2')
          
          console.log(`🔍 [ChatView] sendPendingMessage - ✅ 满足轮询条件，准备启动轮询`)
          console.log(`🔍 [ChatView] sendPendingMessage - 启动轮询: textId=${textId}, userId=${userId}`)
          console.log(`🔍 [ChatView] sendPendingMessage - currentSelectionContext:`, currentSelectionContext)
          console.log(`🔍 [ChatView] sendPendingMessage - articleId:`, articleId)
          
          if (textId) {
            console.log(`🔍 [ChatView] sendPendingMessage - ✅ textId有效，开始设置轮询`)
            // 🔧 先清理之前的轮询（如果存在）
            if (pollPendingKnowledgeRef.current) {
              clearInterval(pollPendingKnowledgeRef.current)
              pollPendingKnowledgeRef.current = null
            }
            
            let pollCount = 0
            const maxPolls = 15  // 🔧 增加最大轮询次数，适应线上服务器延迟
            const pollInterval = 1500  // 🔧 缩短到1.5秒一次，加快响应速度（线上服务器需要更频繁的轮询）
            
            // 🔧 立即执行第一次轮询（不等待 pollInterval），减少延迟
            const pollOnce = async () => {
              pollCount++
              try {
                const { apiService } = await import('../../../services/api')
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] 开始轮询 pending-knowledge: user_id=${userId}, text_id=${textId}`)
                const resp = await apiService.getPendingKnowledge({ user_id: userId, text_id: textId })
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] 原始响应:`, JSON.stringify(resp, null, 2))
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] 原始响应类型:`, typeof resp)
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] resp.success:`, resp?.success)
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] resp.data:`, resp?.data)
                
                // 🔧 修复：API 响应拦截器已经返回 response.data，所以 resp 是 { success: true, data: {...} }
                // 需要访问 resp.data，而不是 resp.data.data
                const data = resp?.data || {}
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] 提取的data:`, JSON.stringify(data, null, 2))
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] data.grammar_to_add:`, data.grammar_to_add)
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] data.vocab_to_add:`, data.vocab_to_add)
                
                // 🔧 修复：后端返回的字段名是 grammar_to_add 和 vocab_to_add
                const pendingGrammar = data.grammar_to_add || []
                const pendingVocab = data.vocab_to_add || []
                
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] ========== Toast 诊断日志 ==========`)
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] 原始响应:`, resp)
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] 提取的data:`, data)
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] 解析后的数据: grammar=${pendingGrammar.length} (${JSON.stringify(pendingGrammar)}), vocab=${pendingVocab.length} (${JSON.stringify(pendingVocab)})`)
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] pendingGrammar 类型: ${Array.isArray(pendingGrammar)}, 长度: ${pendingGrammar.length}`)
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] pendingVocab 类型: ${Array.isArray(pendingVocab)}, 长度: ${pendingVocab.length}`)
                
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] 检查条件: pendingGrammar.length=${pendingGrammar.length}, pendingVocab.length=${pendingVocab.length}`)
                if (pendingGrammar.length > 0 || pendingVocab.length > 0) {
                  console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] ✅ 检测到知识点: grammar=${pendingGrammar.length}, vocab=${pendingVocab.length}`)
                  
                  // 🔧 根据类型生成不同的 toast 消息
                  const items = []
                  const seenItems = new Set()  // 🔧 用于去重
                  console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] 开始生成 toast items...`)
                  
                  // 处理语法知识点
                  pendingGrammar.forEach(g => {
                    // 🔧 修复：后端返回的字段名是 'name'，不是 'display_name'
                    const name = g.name || g.display_name || g.title || g.rule || tUI('语法')
                    const type = g.type || 'new'  // 默认为新知识点
                    
                    // 🔧 去重：使用 name 作为唯一标识
                    const itemKey = `grammar:${name}`
                    if (seenItems.has(itemKey)) {
                      console.log(`⚠️ [ChatView] sendPendingMessage - [轮询${pollCount}] 跳过重复的语法知识点: ${name}`)
                      return
                    }
                    seenItems.add(itemKey)
                    
                    if (type === 'existing') {
                      // 已有知识点：使用新文案
                      const message = tUI('已有知识点：{type} {name} 加入新例句')
                        .replace('{type}', tUI('语法'))
                        .replace('{name}', name)
                      items.push({ message, type: 'existing', key: itemKey })
                    } else {
                      // 新知识点：保持现状
                      items.push({ 
                        message: `🆕 ${tUI('语法')}: ${name} ${tUI('知识点已总结并加入列表')}`, 
                        type: 'new',
                        key: itemKey
                      })
                    }
                  })
                  
                  // 处理词汇知识点
                  pendingVocab.forEach(v => {
                    const vocab = v.vocab || tUI('词汇')
                    const type = v.type || 'new'  // 默认为新知识点
                    
                    // 🔧 去重：使用 vocab 作为唯一标识
                    const itemKey = `vocab:${vocab}`
                    if (seenItems.has(itemKey)) {
                      console.log(`⚠️ [ChatView] sendPendingMessage - [轮询${pollCount}] 跳过重复的词汇知识点: ${vocab}`)
                      return
                    }
                    seenItems.add(itemKey)
                    
                    if (type === 'existing') {
                      // 已有知识点：使用新文案
                      const message = tUI('已有知识点：{type} {name} 加入新例句')
                        .replace('{type}', tUI('词汇'))
                        .replace('{name}', vocab)
                      items.push({ message, type: 'existing', key: itemKey })
                    } else {
                      // 新知识点：保持现状
                      items.push({ 
                        message: `🆕 ${tUI('词汇')}: ${vocab} ${tUI('知识点已总结并加入列表')}`, 
                        type: 'new',
                        key: itemKey
                      })
                    }
                  })
                  
                  console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] 准备创建 ${items.length} 个toast`)
                  console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] items:`, items)
                  console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] 当前toasts数量:`, toasts.length)
                  console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] 当前toasts状态:`, toasts)
                  
                  if (items.length === 0) {
                    console.warn(`⚠️ [ChatView] sendPendingMessage - [轮询${pollCount}] items 为空，无法创建 toast`)
                  } else {
                    console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] 开始创建 ${items.length} 个toast...`)
                    // 🔧 修复：一次性创建所有 toast，确保所有知识点都能显示
                    // 所有 toast 立即显示，通过 slot 控制位置（垂直堆叠）
                    setToasts(prev => {
                      const baseSlot = prev.length
                      console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] 当前toasts数量: ${prev.length}, 基础slot: ${baseSlot}`)
                      
                      // 一次性创建所有 toast
                      const newToasts = items.map((item, idx) => {
                        const id = Date.now() + Math.random() * 1000 + idx
                        const newToast = { 
                          id, 
                          message: item.message, 
                          slot: baseSlot + idx
                        }
                        console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] 创建toast ${idx + 1}/${items.length}:`, newToast)
                        console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] toast message: "${newToast.message}"`)
                        return newToast
                      })
                      
                      const updated = [...prev, ...newToasts]
                      console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] setToasts更新: 从${prev.length}个增加到${updated.length}个`)
                      console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] 更新后的toasts:`, updated)
                      window.chatViewToastsRef = updated
                      return updated
                    })
                    
                    console.log(`🍞 [ChatView] sendPendingMessage - [轮询${pollCount}] 已创建 ${items.length} 个toast（全部立即显示）`)
                  }
                  
                  // 🔧 刷新 notation 缓存，使 article view 自动更新（使用 await 确保完成）
                  if (refreshGrammarNotations) {
                    console.log('🔄 [ChatView] sendPendingMessage - 检测到新知识点，刷新 notation 缓存...')
                    console.log('🔄 [ChatView] sendPendingMessage - refreshGrammarNotations 类型:', typeof refreshGrammarNotations)
                    try {
                      // 🔧 如果是异步函数，等待完成；否则立即执行
                      const refreshResult = refreshGrammarNotations()
                      if (refreshResult && typeof refreshResult.then === 'function') {
                        await refreshResult
                        console.log('✅ [ChatView] sendPendingMessage - notation 缓存刷新完成（异步）')
                      } else {
                        console.log('✅ [ChatView] sendPendingMessage - notation 缓存刷新完成（同步）')
                      }
                    } catch (err) {
                      console.error('❌ [ChatView] sendPendingMessage - notation 缓存刷新失败:', err)
                    }
                  } else {
                    console.warn('⚠️ [ChatView] sendPendingMessage - refreshGrammarNotations 未定义，无法刷新缓存')
                  }
                  
                  // 🔧 找到数据后立即停止轮询
                  if (pollPendingKnowledgeRef.current) {
                    clearInterval(pollPendingKnowledgeRef.current)
                    pollPendingKnowledgeRef.current = null
                    console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] ✅ 已停止轮询`)
                  }
                  return
                } else {
                  console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] ⏸️ 暂无知识点，继续轮询...`)
                }
              } catch (err) {
                console.error(`⚠️ [ChatView] sendPendingMessage - [轮询${pollCount}] 轮询失败:`, err)
                console.error(`⚠️ [ChatView] sendPendingMessage - [轮询${pollCount}] 错误详情:`, err.message, err.stack)
                // 🔧 出错时也停止轮询，避免无限重试
                if (pollPendingKnowledgeRef.current) {
                  clearInterval(pollPendingKnowledgeRef.current)
                  pollPendingKnowledgeRef.current = null
                  console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] ❌ 因错误停止轮询`)
                }
              }
              
              // 🔧 达到最大轮询次数后停止
              if (pollCount >= maxPolls) {
                console.log(`🔍 [ChatView] sendPendingMessage - [轮询${pollCount}] ⏸️ 达到最大轮询次数(${maxPolls})，停止轮询`)
                if (pollPendingKnowledgeRef.current) {
                  clearInterval(pollPendingKnowledgeRef.current)
                  pollPendingKnowledgeRef.current = null
                }
              }
            }
            
            // 🔧 延迟启动轮询，给后台任务一些时间执行（线上服务器可能需要更长时间）
            setTimeout(() => {
              // 立即执行第一次轮询
              pollOnce()
              
              // 然后设置定时轮询
              pollPendingKnowledgeRef.current = setInterval(pollOnce, pollInterval)
              console.log(`🔍 [ChatView] sendPendingMessage - ✅ 轮询已设置，interval ID:`, pollPendingKnowledgeRef.current)
            }, 500)  // 🔧 延迟 500ms 启动，确保后台任务有时间开始执行
            
            // 🔧 设置超时清理（双重保险）
            setTimeout(() => {
              if (pollPendingKnowledgeRef.current) {
                clearInterval(pollPendingKnowledgeRef.current)
                pollPendingKnowledgeRef.current = null
                console.log(`🔍 [ChatView] sendPendingMessage - ⏸️ 超时清理轮询`)
              }
            }, 500 + maxPolls * pollInterval)  // 🔧 加上延迟启动的时间
          } else {
            console.log(`🔍 [ChatView] sendPendingMessage - ❌ textId无效(${textId})，无法启动轮询`)
          }
        } else {
          console.log(`🔍 [ChatView] sendPendingMessage - ⏸️ 不满足轮询条件（响应中有即时返回的新知识点或response为空），跳过轮询`)
        }
      } catch (error) {
        console.error('❌ [ChatView] 发送 pendingMessage 失败:', error)
        // ⚠️ Language detection in error handler: Presentation-only, does NOT affect error handling logic
        const errorMsg = {
          id: generateMessageId(),
          text: `${t("抱歉，处理您的问题时出现错误: ")}${error.message || t("未知错误")}`,
          isUser: false,
          timestamp: new Date(),
          articleId: articleId ? String(articleId) : undefined  // 🔧 添加 articleId 用于跨设备同步
        }
        addMessage(errorMsg)
      } finally {
        setIsProcessing(false)
        clearPendingMessage()
        clearPendingContext()
        // 🔧 修复问题3：处理完成后，重置处理标记
        processingPendingMessageRef.current = false
      }
    }
    
    sendPendingMessage()
  }, [pendingMessage, pendingContext, isProcessing, selectionContext, quotedText, addMessage, addGrammarNotationToCache, addVocabNotationToCache, refreshGrammar, refreshVocab, clearPendingMessage, clearPendingContext])
  
  // 🔧 解析 AI 响应
  const parseAIResponse = (responseText) => {
    if (!responseText) return ''
    
    // 如果已经是对象且包含 answer 字段
    if (typeof responseText === 'object' && responseText !== null && responseText.answer) {
      return responseText.answer
    }
    
    if (typeof responseText === 'string') {
      const trimmed = responseText.trim()
      
      // 🔧 尝试标准 JSON 解析
      try {
        const parsed = JSON.parse(trimmed)
        if (parsed && typeof parsed === 'object') {
          if (parsed.answer) {
          return parsed.answer
          }
          // 如果解析成功但格式不对，返回原始文本
          return trimmed
        }
      } catch (e) {
        // 不是标准 JSON，继续尝试其他方法
      }
      
      // 🔧 尝试提取 JSON 中的 answer 字段（使用正则表达式）
      // 匹配 {"answer": "..."} 或 {'answer': '...'} 格式
      const jsonAnswerPattern = /['"]answer['"]\s*:\s*['"](.*?)['"]/s
      const match = trimmed.match(jsonAnswerPattern)
      if (match && match[1]) {
        // 替换转义字符
        return match[1]
          .replace(/\\n/g, '\n')
          .replace(/\\t/g, '\t')
          .replace(/\\'/g, "'")
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, '\\')
      }
      
      // 🔧 尝试多行 JSON（answer 字段可能跨多行）
      const multiLineJsonPattern = /['"]answer['"]\s*:\s*['"]((?:[^'"]|\\['"])*)['"]/s
      const multiLineMatch = trimmed.match(multiLineJsonPattern)
      if (multiLineMatch && multiLineMatch[1]) {
        return multiLineMatch[1]
          .replace(/\\n/g, '\n')
          .replace(/\\t/g, '\t')
          .replace(/\\'/g, "'")
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, '\\')
          }
      
      // 🔧 如果都失败了，直接返回原始文本
      return trimmed
    }
    
    return String(responseText)
  }

  const normalizeAiDisplayText = (text) => {
    const raw = String(text ?? '')
    return raw.trim()
  }

  const renderSimpleMarkdown = (text) => {
    const source = String(text ?? '')
    // 仅支持常用且安全的行内格式：**bold** 与 `inline code`
    const parts = source.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
    return parts.map((part, idx) => {
      if (!part) return null
      if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
        return <strong key={`md-b-${idx}`}>{part.slice(2, -2)}</strong>
      }
      if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
        return (
          <code key={`md-c-${idx}`} className="rounded bg-gray-200 px-1 py-0.5 text-[0.95em]">
            {part.slice(1, -1)}
          </code>
        )
      }
      return <span key={`md-t-${idx}`}>{part}</span>
    })
  }

  const extractAiReplyFromSendChatResponse = (response) => {
    if (!response) return ''
    const candidates = [
      response?.ai_response,
      response?.answer,
      response?.assistant_response,
      response?.response,
      response?.message,
      response?.data?.ai_response,
      response?.data?.answer,
      response?.data?.assistant_response,
      response?.data?.response,
      response?.data?.message
    ]
    for (const item of candidates) {
      if (item == null) continue
      const parsed = parseAIResponse(item)
      if (typeof parsed === 'string' && parsed.trim()) return normalizeAiDisplayText(parsed)
    }
    return ''
  }

  const appendAiReplyWithHistoryFallback = async ({ response, apiService, requestStartedAt = Date.now() }) => {
    // 1) 优先使用 sendChat 直接返回
    const directReply = extractAiReplyFromSendChatResponse(response)
    if (directReply) {
      addMessage({
        id: generateMessageId(),
        text: directReply,
        isUser: false,
        timestamp: new Date(),
        articleId: articleId ? String(articleId) : undefined
      })
      return
    }

    // 2) 兜底：从 history 轮询最近 AI 回答（后端已成功写入但本次响应字段不一致/稍晚写入时）
    if (!articleId) return
    try {
      const maxAttempts = 6
      const retryDelayMs = 450
      for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        const historyResp = await apiService.getChatHistory({ textId: articleId, limit: 50 })
        const items = historyResp?.items || []
        if (Array.isArray(items) && items.length > 0) {
          const current = Array.isArray(messagesRef.current) ? messagesRef.current : []
          const existingAiIds = new Set(
            current.filter(m => !m?.isUser && m?.id != null).map(m => String(m.id))
          )
          const existingAiTextSet = new Set(
            current.filter(m => !m?.isUser).map(m => normalizeTextForSignature(m?.text))
          )
          const targetAi = [...items]
            .filter(item => item && item.is_user === false && typeof item.text === 'string' && item.text.trim())
            .filter(item => {
              const createdAt = item.created_at ? new Date(item.created_at).getTime() : 0
              // 允许服务端时间轻微漂移，向前放宽 2 秒
              return createdAt >= (requestStartedAt - 2000)
            })
            .filter(item => !existingAiIds.has(String(item.id)))
            .filter(item => !existingAiTextSet.has(normalizeTextForSignature(item.text)))
            .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))[0]

          if (targetAi) {
            addMessage({
              id: targetAi.id || generateMessageId(),
        text: normalizeAiDisplayText(targetAi.text),
              isUser: false,
              timestamp: targetAi.created_at ? new Date(targetAi.created_at) : new Date(),
              articleId: articleId ? String(articleId) : undefined
            })
            return
          }
        }

        if (attempt < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, retryDelayMs))
        }
      }
    } catch (e) {
      console.warn('⚠️ [ChatView] AI 回答兜底加载失败:', e)
    }
  }
  
  // 🔧 发送消息
  const handleSendMessage = async () => {
    // 🔧 同步防重：避免 Enter + 点击或快速双击导致同一条消息发送两次
    if (sendingRef.current) {
      console.log(`🔍 [ChatView] handleSendMessage 被跳过: sendingRef 已锁定`)
      return
    }
    if (inputText.trim() === '' || isProcessing) {
      console.log(`🔍 [ChatView] handleSendMessage 被跳过: inputText为空或正在处理`)
      return
    }
    sendingRef.current = true
    // 🔍 诊断日志：追踪函数调用
    const stackTrace = new Error().stack
    console.log(`🔍 [ChatView] handleSendMessage 开始:`, {
      inputText: inputText?.substring(0, 50),
      isProcessing,
      hasPendingMessage: !!pendingMessage,
      callStack: stackTrace?.split('\n').slice(1, 4).join(' -> ')
    })
    
    // 🔍 诊断日志：检查是否与 pendingMessage 冲突
    if (pendingMessage && pendingMessage.text === inputText.trim()) {
      console.warn('⚠️ [ChatView] handleSendMessage - 检测到与 pendingMessage 相同的消息，可能导致重复:', {
        inputText: inputText.trim(),
        pendingMessageText: pendingMessage.text,
        isProcessing,
        processingPendingMessageRef: processingPendingMessageRef.current
      })
    }
    
    // 🔍 诊断日志：检查是否正在处理 pendingMessage
    if (processingPendingMessageRef.current) {
      console.warn('⚠️ [ChatView] handleSendMessage - processingPendingMessageRef.current = true，可能导致重复处理')
    }
    
    // 🔧 检查token是否不足（只在当前没有main assistant流程时判断）
    if (!isProcessing && userInfo) {
      const insufficient = isTokenInsufficient(userInfo.token_balance, userInfo.role)
      if (insufficient) {
        console.log(`⚠️ [ChatView] Token不足，无法使用AI聊天功能`)
        sendingRef.current = false
        return
      }
    } else if (!isProcessing && tokenInsufficient) {
      // 如果userInfo还未加载，但之前检查过token不足，也阻止
      console.log(`⚠️ [ChatView] Token不足，无法使用AI聊天功能`)
      sendingRef.current = false
      return
    }
    
    setIsProcessing(true)
    const questionText = inputText
    console.log(`🔍 [ChatView] handleSendMessage 开始处理: questionText="${questionText}"`)
    const currentQuotedText = quotedText
    const currentSelectionContext = selectionContext
    
    // 🔧 立即添加用户消息
    const userMessage = {
      id: generateMessageId(),
      text: questionText,
      isUser: true,
      timestamp: new Date(),
      quote: currentQuotedText || null,
      articleId: articleId ? String(articleId) : undefined  // 🔧 添加 articleId 用于跨设备同步
    }
    addMessage(userMessage)
    setInputText('')
    
    // 🔧 调用 API（合并 session 更新，避免重复请求）
    try {
      const { apiService } = await import('../../../services/api')
      
      // 🔧 合并 session 更新：将句子上下文和 current_input 合并到一次调用
      const sessionUpdatePayload = { current_input: questionText }
      
      if (currentSelectionContext?.sentence) {
        sessionUpdatePayload.sentence = currentSelectionContext.sentence
        
        if (currentSelectionContext.tokens?.length > 0) {
          if (currentSelectionContext.tokens.length > 1) {
            sessionUpdatePayload.token = {
              multiple_tokens: currentSelectionContext.tokens,
              token_indices: currentSelectionContext.tokenIndices,
              token_text: currentSelectionContext.selectedTexts.join(' ')
            }
          } else {
            const token = currentSelectionContext.tokens[0]
            sessionUpdatePayload.token = {
              token_body: token.token_body,
              sentence_token_id: token.sentence_token_id
            }
          }
        } else {
          sessionUpdatePayload.token = null
        }
      }
      
      // 🔧 一次性更新所有上下文，而不是分两次调用
      await apiService.session.updateContext(sessionUpdatePayload)
      
      // 🔧 传递 UI 语言参数，用于控制 AI 输出的语言
      const uiLanguageForBackend = uiLanguage === 'en' ? '英文' : '中文'
      const requestStartedAt = Date.now()
      const response = await apiService.sendChat({ 
        user_question: questionText,
        ui_language: uiLanguageForBackend
      })
      console.log(`🔍 [ChatView] sendChat 响应:`, response)
      console.log(`🔍 [ChatView] response.grammar_to_add:`, response?.grammar_to_add)
      console.log(`🔍 [ChatView] response.vocab_to_add:`, response?.vocab_to_add)
      
      // 🔧 添加 AI 回答（字段兼容 + history 兜底）
      await appendAiReplyWithHistoryFallback({ response, apiService, requestStartedAt })
      
      // 🔧 处理 notations
      // 🔍 诊断日志：追踪 notation 添加
      if (response?.created_grammar_notations?.length > 0) {
        console.log('🔍 [ChatView] handleSendMessage - 处理 grammar notations:', {
          count: response.created_grammar_notations.length,
          notations: response.created_grammar_notations.map(n => ({
            notation_id: n.notation_id,
            grammar_id: n.grammar_id,
            text_id: n.text_id,
            sentence_id: n.sentence_id
          }))
        })
        response.created_grammar_notations.forEach((n, idx) => {
          console.log(`🔍 [ChatView] handleSendMessage - 添加 grammar notation ${idx + 1}/${response.created_grammar_notations.length}:`, {
            notation_id: n.notation_id,
            grammar_id: n.grammar_id,
            text_id: n.text_id,
            sentence_id: n.sentence_id
          })
          if (addGrammarNotationToCache) addGrammarNotationToCache(n)
        })
      }
      if (response?.created_vocab_notations?.length > 0) {
        console.log('🔍 [ChatView] handleSendMessage - 处理 vocab notations:', {
          count: response.created_vocab_notations.length,
          notations: response.created_vocab_notations.map(n => ({
            notation_id: n.notation_id,
            vocab_id: n.vocab_id,
            text_id: n.text_id,
            sentence_id: n.sentence_id,
            token_index: n.token_id || n.token_index
          }))
        })
        response.created_vocab_notations.forEach((n, idx) => {
          console.log(`🔍 [ChatView] handleSendMessage - 添加 vocab notation ${idx + 1}/${response.created_vocab_notations.length}:`, {
            notation_id: n.notation_id,
            vocab_id: n.vocab_id,
            text_id: n.text_id,
            sentence_id: n.sentence_id,
            token_index: n.token_id || n.token_index
          })
          if (addVocabNotationToCache) addVocabNotationToCache({
            ...n,
            token_index: n.token_id || n.token_index
          })
        })
      }
      
      // 🔧 刷新列表
      if (response?.grammar_to_add?.length > 0 || response?.created_grammar_notations?.length > 0) {
        refreshGrammar()
      }
      if (response?.vocab_to_add?.length > 0 || response?.created_vocab_notations?.length > 0) {
        refreshVocab()
      }
      
      // 🔧 即时响应中的语法/词汇也显示知识点弹窗
      const immGrammar = response?.created_grammar_notations || []
      const immVocab = response?.created_vocab_notations || []
      if (immGrammar.length > 0 || immVocab.length > 0) {
        const items = []
        immGrammar.forEach((n) => {
          const name = n.rule_name || n.name || n.display_name || tUI('语法')
          items.push({ message: `🆕 ${tUI('语法')}: ${name} ${tUI('知识点已总结并加入列表')}`, key: `imm-g-${n.notation_id || n.grammar_id}` })
        })
        immVocab.forEach((n) => {
          const vocab = n.vocab || n.vocab_body || tUI('词汇')
          items.push({ message: `🆕 ${tUI('词汇')}: ${vocab} ${tUI('知识点已总结并加入列表')}`, key: `imm-v-${n.notation_id || n.vocab_id}` })
        })
        if (items.length > 0) {
          setToasts(prev => {
            const baseSlot = prev.length
            const newToasts = items.map((item, idx) => ({
              id: Date.now() + idx + Math.random() * 1000,
              message: item.message,
              slot: baseSlot + idx
            }))
            const updated = [...prev, ...newToasts]
            window.chatViewToastsRef = updated
            return updated
          })
        }
      }
      
      // 🔧 标记 tokens
      if (markAsAsked && currentSelectionContext?.tokens?.length > 0) {
        const vocabIdMap = new Map()
        if (response?.vocab_to_add) {
          response.vocab_to_add.forEach(v => {
            if (v.vocab && v.vocab_id) {
              vocabIdMap.set(v.vocab.toLowerCase(), v.vocab_id)
            }
          })
        }
        
        const newVocabTokens = new Set()
        if (response?.vocab_to_add) {
          response.vocab_to_add.forEach(v => {
            if (v.vocab) newVocabTokens.add(v.vocab.toLowerCase())
          })
        }
        
        currentSelectionContext.tokens.forEach(token => {
          const tokenBody = token.token_body?.toLowerCase() || ''
          if (newVocabTokens.has(tokenBody)) {
            const vocabId = vocabIdMap.get(tokenBody)
            markAsAsked({
              token_body: token.token_body,
              sentence_token_id: token.sentence_token_id,
              sentence_id: currentSelectionContext.sentence?.sentence_id,
              text_id: currentSelectionContext.sentence?.text_id || articleId,
              vocab_id: vocabId
            })
          }
        })
      }
      
      // 🔧 轮询新知识点（优化：降低频率，确保清理）
      // 🔧 只在响应中没有即时返回的新知识点时才启动轮询
      console.log(`🔍 [ChatView] 检查轮询条件: response存在=${!!response}, grammar_to_add长度=${response?.grammar_to_add?.length || 0}, vocab_to_add长度=${response?.vocab_to_add?.length || 0}`)
      
      if (response && !response.grammar_to_add?.length && !response.vocab_to_add?.length) {
        const textId = currentSelectionContext?.sentence?.text_id || articleId
        const userId = parseInt(localStorage.getItem('user_id') || '2')
        
        console.log(`🔍 [ChatView] ✅ 满足轮询条件，准备启动轮询`)
        console.log(`🔍 [ChatView] 启动轮询: textId=${textId}, userId=${userId}`)
        console.log(`🔍 [ChatView] currentSelectionContext:`, currentSelectionContext)
        console.log(`🔍 [ChatView] articleId:`, articleId)
        
        if (textId) {
          console.log(`🔍 [ChatView] ✅ textId有效，开始设置轮询`)
          // 🔧 先清理之前的轮询（如果存在）
          if (pollPendingKnowledgeRef.current) {
            clearInterval(pollPendingKnowledgeRef.current)
            pollPendingKnowledgeRef.current = null
          }
          
          let pollCount = 0
          const maxPolls = 15  // 🔧 增加最大轮询次数，适应线上服务器延迟
          const pollInterval = 1500  // 🔧 缩短到1.5秒一次，加快响应速度（线上服务器需要更频繁的轮询）
          
          // 🔧 立即执行第一次轮询（不等待 pollInterval），减少延迟
          const pollOnce = async () => {
            pollCount++
            try {
              const { apiService } = await import('../../../services/api')
              console.log(`🔍 [ChatView] [轮询${pollCount}] 开始轮询 pending-knowledge: user_id=${userId}, text_id=${textId}`)
              const resp = await apiService.getPendingKnowledge({ user_id: userId, text_id: textId })
              console.log(`🔍 [ChatView] [轮询${pollCount}] 原始响应:`, JSON.stringify(resp, null, 2))
              
              // 🔧 修复：API 响应拦截器已经返回 response.data，所以 resp 是 { success: true, data: {...} }
              // 需要访问 resp.data，而不是 resp.data.data
              const data = resp?.data || {}
              console.log(`🔍 [ChatView] [轮询${pollCount}] 提取的data:`, JSON.stringify(data, null, 2))
              
              // 🔧 修复：后端返回的字段名是 grammar_to_add 和 vocab_to_add
              const pendingGrammar = data.grammar_to_add || []
              const pendingVocab = data.vocab_to_add || []
              
              console.log(`🔍 [ChatView] [轮询${pollCount}] 解析后的数据: grammar=${pendingGrammar.length} (${JSON.stringify(pendingGrammar)}), vocab=${pendingVocab.length} (${JSON.stringify(pendingVocab)})`)
              
              if (pendingGrammar.length > 0 || pendingVocab.length > 0) {
                console.log(`🍞 [ChatView] [轮询${pollCount}] ✅ 检测到知识点: grammar=${pendingGrammar.length}, vocab=${pendingVocab.length}`)
                
                // 🔧 根据类型生成不同的 toast 消息
                const items = []
                const seenItems = new Set()  // 🔧 用于去重（基于知识点名称）
                
                // 处理语法知识点
                pendingGrammar.forEach(g => {
                  // 🔧 修复：后端返回的字段名是 'name'，不是 'display_name'
                  const name = g.name || g.display_name || g.title || g.rule || tUI('语法')
                  const type = g.type || 'new'  // 默认为新知识点
                  
                  // 🔧 去重：使用 name 作为唯一标识
                  const itemKey = `grammar:${name}`
                  if (seenItems.has(itemKey)) {
                    console.log(`⚠️ [ChatView] [轮询${pollCount}] 跳过重复的语法知识点: ${name}`)
                    return
                  }
                  seenItems.add(itemKey)
                  
                  if (type === 'existing') {
                    // 已有知识点：使用新文案
                    const message = tUI('已有知识点：{type} {name} 加入新例句')
                      .replace('{type}', tUI('语法'))
                      .replace('{name}', name)
                    items.push({ message, type: 'existing', key: itemKey })
                  } else {
                    // 新知识点：保持现状
                    items.push({ 
                      message: `🆕 ${tUI('语法')}: ${name} ${tUI('知识点已总结并加入列表')}`, 
                      type: 'new',
                      key: itemKey
                    })
                  }
                })
                
                // 处理词汇知识点
                pendingVocab.forEach(v => {
                  const vocab = v.vocab || tUI('词汇')
                  const type = v.type || 'new'  // 默认为新知识点
                  
                  // 🔧 去重：使用 vocab 作为唯一标识
                  const itemKey = `vocab:${vocab}`
                  if (seenItems.has(itemKey)) {
                    console.log(`⚠️ [ChatView] [轮询${pollCount}] 跳过重复的词汇知识点: ${vocab}`)
                    return
                  }
                  seenItems.add(itemKey)
                  
                  if (type === 'existing') {
                    // 已有知识点：使用新文案
                    const message = tUI('已有知识点：{type} {name} 加入新例句')
                      .replace('{type}', tUI('词汇'))
                      .replace('{name}', vocab)
                    items.push({ message, type: 'existing', key: itemKey })
                  } else {
                    // 新知识点：保持现状
                    items.push({ 
                      message: `🆕 ${tUI('词汇')}: ${vocab} ${tUI('知识点已总结并加入列表')}`, 
                      type: 'new',
                      key: itemKey
                    })
                  }
                })
                
                // 🔧 二次去重：使用 Set 去除重复的 items（基于 message，作为额外保障）
                const uniqueItems = []
                const seenMessages = new Set()
                items.forEach(item => {
                  if (!seenMessages.has(item.message)) {
                    seenMessages.add(item.message)
                    uniqueItems.push(item)
                  } else {
                    console.log(`⚠️ [ChatView] [轮询${pollCount}] 跳过重复的 toast 消息: ${item.message}`)
                  }
                })
                
                console.log(`🍞 [ChatView] [轮询${pollCount}] 准备创建 ${uniqueItems.length} 个toast (去重前: ${items.length})`)
                console.log(`🍞 [ChatView] [轮询${pollCount}] items:`, uniqueItems)
                console.log(`🍞 [ChatView] [轮询${pollCount}] 当前toasts数量:`, toasts.length)
                
                // 🔧 修复：一次性创建所有 toast，确保所有知识点都能显示
                setToasts(prev => {
                  const baseSlot = prev.length
                  const newToasts = uniqueItems.map((item, idx) => {
                    const id = Date.now() + Math.random() * 1000 + idx
                    const newToast = { 
                      id, 
                      message: item.message, 
                      slot: baseSlot + idx
                    }
                    console.log(`🍞 [ChatView] [轮询${pollCount}] 创建toast ${idx + 1}/${uniqueItems.length}:`, newToast)
                    return newToast
                  })
                  const updated = [...prev, ...newToasts]
                  console.log(`🍞 [ChatView] [轮询${pollCount}] setToasts更新: 从${prev.length}个增加到${updated.length}个`)
                  window.chatViewToastsRef = updated
                  return updated
                })
                
                // 🔧 刷新 notation 缓存，使 article view 自动更新（使用 await 确保完成）
                if (refreshGrammarNotations) {
                  console.log('🔄 [ChatView] 检测到新知识点，刷新 notation 缓存...')
                  try {
                    // 🔧 如果是异步函数，等待完成；否则立即执行
                    const refreshResult = refreshGrammarNotations()
                    if (refreshResult && typeof refreshResult.then === 'function') {
                      await refreshResult
                      console.log('✅ [ChatView] notation 缓存刷新完成（异步）')
                    } else {
                      console.log('✅ [ChatView] notation 缓存刷新完成（同步）')
                    }
                  } catch (err) {
                    console.error('❌ [ChatView] notation 缓存刷新失败:', err)
                  }
                }
                
                // 🔧 找到数据后立即停止轮询
                if (pollPendingKnowledgeRef.current) {
                  clearInterval(pollPendingKnowledgeRef.current)
                  pollPendingKnowledgeRef.current = null
                  console.log(`🔍 [ChatView] [轮询${pollCount}] ✅ 已停止轮询`)
                }
                return
              } else {
                console.log(`🔍 [ChatView] [轮询${pollCount}] ⏸️ 暂无新知识点，继续轮询...`)
              }
            } catch (err) {
              console.error(`⚠️ [ChatView] [轮询${pollCount}] 轮询失败:`, err)
              console.error(`⚠️ [ChatView] [轮询${pollCount}] 错误详情:`, err.message, err.stack)
              // 🔧 出错时也停止轮询，避免无限重试
              if (pollPendingKnowledgeRef.current) {
                clearInterval(pollPendingKnowledgeRef.current)
                pollPendingKnowledgeRef.current = null
                console.log(`🔍 [ChatView] [轮询${pollCount}] ❌ 因错误停止轮询`)
              }
            }
            
            // 🔧 达到最大轮询次数后停止
            if (pollCount >= maxPolls) {
              console.log(`🔍 [ChatView] [轮询${pollCount}] ⏸️ 达到最大轮询次数(${maxPolls})，停止轮询`)
              if (pollPendingKnowledgeRef.current) {
                clearInterval(pollPendingKnowledgeRef.current)
                pollPendingKnowledgeRef.current = null
              }
            }
          }
          
          // 🔧 延迟启动轮询，给后台任务一些时间执行（线上服务器可能需要更长时间）
          setTimeout(() => {
            // 立即执行第一次轮询
            pollOnce()
            
            // 然后设置定时轮询
            pollPendingKnowledgeRef.current = setInterval(pollOnce, pollInterval)
            console.log(`🔍 [ChatView] ✅ 轮询已设置，interval ID:`, pollPendingKnowledgeRef.current)
          }, 500)  // 🔧 延迟 500ms 启动，确保后台任务有时间开始执行
          
          // 🔧 设置超时清理（双重保险）
          setTimeout(() => {
            if (pollPendingKnowledgeRef.current) {
              clearInterval(pollPendingKnowledgeRef.current)
              pollPendingKnowledgeRef.current = null
              console.log(`🔍 [ChatView] ⏸️ 超时清理轮询`)
            }
          }, 500 + maxPolls * pollInterval)  // 🔧 加上延迟启动的时间
        } else {
          console.log(`🔍 [ChatView] ❌ textId无效(${textId})，无法启动轮询`)
        }
      } else {
        console.log(`🔍 [ChatView] ⏸️ 不满足轮询条件（响应中有即时返回的新知识点或response为空），跳过轮询`)
      }
    } catch (error) {
      console.error('❌ [ChatView] 发送消息失败:', error)
      // ⚠️ Language detection in error handler: Presentation-only, does NOT affect error handling logic
      const errorMsg = {
        id: generateMessageId(),
        text: `${t("抱歉，处理您的问题时出现错误: ")}${error.message || t("未知错误")}`,
        isUser: false,
        timestamp: new Date(),
        articleId: articleId ? String(articleId) : undefined  // 🔧 添加 articleId 用于跨设备同步
      }
      addMessage(errorMsg)
    } finally {
      setIsProcessing(false)
      sendingRef.current = false
    }
  }
  
  // 🔧 建议问题选择
  const handleSuggestedQuestionSelect = async (question) => {
    if (sendingRef.current) {
      console.log(`🔍 [ChatView] handleSuggestedQuestionSelect 被跳过: sendingRef 已锁定`)
      return
    }
    if (isProcessing) {
      console.log(`🔍 [ChatView] handleSuggestedQuestionSelect 被跳过: 正在处理中`)
      return
    }
    sendingRef.current = true
    console.log(`🔍 [ChatView] handleSuggestedQuestionSelect 开始: question="${question}"`)
    
    // 🔧 检查token是否不足（只在当前没有main assistant流程时判断）
    if (!isProcessing && userInfo) {
      const insufficient = isTokenInsufficient(userInfo.token_balance, userInfo.role)
      if (insufficient) {
        console.log(`⚠️ [ChatView] Token不足，无法使用AI聊天功能`)
        sendingRef.current = false
        return
      }
    } else if (!isProcessing && tokenInsufficient) {
      // 如果userInfo还未加载，但之前检查过token不足，也阻止
      console.log(`⚠️ [ChatView] Token不足，无法使用AI聊天功能`)
      sendingRef.current = false
      return
    }
    
    setIsProcessing(true)
    const currentQuotedText = quotedText
    const currentSelectionContext = selectionContext
    console.log(`🔍 [ChatView] handleSuggestedQuestionSelect 开始处理: question="${question}"`)
    
    // 🔧 立即添加用户消息
    const userMessage = {
      id: generateMessageId(),
      text: question,
      isUser: true,
      timestamp: new Date(),
      quote: currentQuotedText || null,
      articleId: articleId ? String(articleId) : undefined  // 🔧 添加 articleId 用于跨设备同步
    }
    addMessage(userMessage)
    
    // 🔧 调用 API（合并 session 更新，避免重复请求）
    try {
      const { apiService } = await import('../../../services/api')
      
      // 🔧 合并 session 更新：将句子上下文和 current_input 合并到一次调用
      const sessionUpdatePayload = { current_input: question }
      
      if (currentSelectionContext?.sentence) {
        sessionUpdatePayload.sentence = currentSelectionContext.sentence
        
        if (currentSelectionContext.tokens?.length > 0) {
          if (currentSelectionContext.tokens.length > 1) {
            sessionUpdatePayload.token = {
              multiple_tokens: currentSelectionContext.tokens,
              token_indices: currentSelectionContext.tokenIndices,
              token_text: currentSelectionContext.selectedTexts.join(' ')
            }
          } else {
            const token = currentSelectionContext.tokens[0]
            sessionUpdatePayload.token = {
              token_body: token.token_body,
              sentence_token_id: token.sentence_token_id
            }
          }
        } else {
          sessionUpdatePayload.token = null
        }
      }
      
      // 🔧 一次性更新所有上下文，而不是分两次调用
      await apiService.session.updateContext(sessionUpdatePayload)
      
      // 🔧 传递 UI 语言参数，用于控制 AI 输出的语言
      const uiLanguageForBackend = uiLanguage === 'en' ? '英文' : '中文'
      const requestStartedAt = Date.now()
      const response = await apiService.sendChat({ 
        user_question: question,
        ui_language: uiLanguageForBackend
      })
      console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - sendChat 响应:`, response)
      console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - response.grammar_to_add:`, response?.grammar_to_add)
      console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - response.vocab_to_add:`, response?.vocab_to_add)
      
      // 🔧 添加 AI 回答（字段兼容 + history 兜底）
      await appendAiReplyWithHistoryFallback({ response, apiService, requestStartedAt })
      
      // 🔧 处理 notations（与 handleSendMessage 相同）
      // 🔍 诊断日志：追踪 notation 添加
      if (response?.created_grammar_notations?.length > 0) {
        console.log('🔍 [ChatView] handleSuggestedQuestionSelect - 处理 grammar notations:', {
          count: response.created_grammar_notations.length,
          notations: response.created_grammar_notations.map(n => ({
            notation_id: n.notation_id,
            grammar_id: n.grammar_id,
            text_id: n.text_id,
            sentence_id: n.sentence_id
          }))
        })
        response.created_grammar_notations.forEach((n, idx) => {
          console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - 添加 grammar notation ${idx + 1}/${response.created_grammar_notations.length}:`, {
            notation_id: n.notation_id,
            grammar_id: n.grammar_id,
            text_id: n.text_id,
            sentence_id: n.sentence_id
          })
          if (addGrammarNotationToCache) addGrammarNotationToCache(n)
        })
      }
      if (response?.created_vocab_notations?.length > 0) {
        console.log('🔍 [ChatView] handleSuggestedQuestionSelect - 处理 vocab notations:', {
          count: response.created_vocab_notations.length,
          notations: response.created_vocab_notations.map(n => ({
            notation_id: n.notation_id,
            vocab_id: n.vocab_id,
            text_id: n.text_id,
            sentence_id: n.sentence_id,
            token_index: n.token_id || n.token_index
          }))
        })
        response.created_vocab_notations.forEach((n, idx) => {
          console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - 添加 vocab notation ${idx + 1}/${response.created_vocab_notations.length}:`, {
            notation_id: n.notation_id,
            vocab_id: n.vocab_id,
            text_id: n.text_id,
            sentence_id: n.sentence_id,
            token_index: n.token_id || n.token_index
          })
          if (addVocabNotationToCache) addVocabNotationToCache({
            ...n,
            token_index: n.token_id || n.token_index
          })
        })
      }
      
      if (response?.grammar_to_add?.length > 0 || response?.created_grammar_notations?.length > 0) {
        refreshGrammar()
      }
      if (response?.vocab_to_add?.length > 0 || response?.created_vocab_notations?.length > 0) {
        refreshVocab()
      }
      
      // 🔧 即时响应中的语法/词汇也显示知识点弹窗
      const immGrammarSug = response?.created_grammar_notations || []
      const immVocabSug = response?.created_vocab_notations || []
      if (immGrammarSug.length > 0 || immVocabSug.length > 0) {
        const itemsSug = []
        immGrammarSug.forEach((n) => {
          const name = n.rule_name || n.name || n.display_name || tUI('语法')
          itemsSug.push({ message: `🆕 ${tUI('语法')}: ${name} ${tUI('知识点已总结并加入列表')}`, key: `imm-g-${n.notation_id || n.grammar_id}` })
        })
        immVocabSug.forEach((n) => {
          const vocab = n.vocab || n.vocab_body || tUI('词汇')
          itemsSug.push({ message: `🆕 ${tUI('词汇')}: ${vocab} ${tUI('知识点已总结并加入列表')}`, key: `imm-v-${n.notation_id || n.vocab_id}` })
        })
        if (itemsSug.length > 0) {
          setToasts(prev => {
            const baseSlot = prev.length
            const newToasts = itemsSug.map((item, idx) => ({
              id: Date.now() + idx + Math.random() * 1000,
              message: item.message,
              slot: baseSlot + idx
            }))
            const updated = [...prev, ...newToasts]
            window.chatViewToastsRef = updated
            return updated
          })
        }
      }
      
      // 🔧 轮询新知识点（与 handleSendMessage 相同的逻辑）
      console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - 检查轮询条件: response存在=${!!response}, grammar_to_add长度=${response?.grammar_to_add?.length || 0}, vocab_to_add长度=${response?.vocab_to_add?.length || 0}`)
      
      if (response && !response.grammar_to_add?.length && !response.vocab_to_add?.length) {
        const textId = currentSelectionContext?.sentence?.text_id || articleId
        const userId = parseInt(localStorage.getItem('user_id') || '2')
        
        console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - ✅ 满足轮询条件，准备启动轮询`)
        console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - 启动轮询: textId=${textId}, userId=${userId}`)
        console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - currentSelectionContext:`, currentSelectionContext)
        console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - articleId:`, articleId)
        
        if (textId) {
          console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - ✅ textId有效，开始设置轮询`)
          // 🔧 先清理之前的轮询（如果存在）
          if (pollPendingKnowledgeRef.current) {
            clearInterval(pollPendingKnowledgeRef.current)
            pollPendingKnowledgeRef.current = null
          }
          
          let pollCount = 0
          const maxPolls = 15  // 🔧 增加最大轮询次数，适应线上服务器延迟
          const pollInterval = 1500  // 🔧 缩短到1.5秒一次，加快响应速度（线上服务器需要更频繁的轮询）
          
          // 🔧 立即执行第一次轮询（不等待 pollInterval），减少延迟
          const pollOnce = async () => {
            pollCount++
            try {
              const { apiService } = await import('../../../services/api')
              console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 开始轮询 pending-knowledge: user_id=${userId}, text_id=${textId}`)
              const resp = await apiService.getPendingKnowledge({ user_id: userId, text_id: textId })
              console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 原始响应:`, JSON.stringify(resp, null, 2))
              
              // 🔧 修复：API 响应拦截器已经返回 response.data，所以 resp 是 { success: true, data: {...} }
              // 需要访问 resp.data，而不是 resp.data.data
              const data = resp?.data || {}
              console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 提取的data:`, JSON.stringify(data, null, 2))
              
              // 🔧 修复：后端返回的字段名是 grammar_to_add 和 vocab_to_add
              const pendingGrammar = data.grammar_to_add || []
              const pendingVocab = data.vocab_to_add || []
              
              console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 解析后的数据: grammar=${pendingGrammar.length} (${JSON.stringify(pendingGrammar)}), vocab=${pendingVocab.length} (${JSON.stringify(pendingVocab)})`)
              
              if (pendingGrammar.length > 0 || pendingVocab.length > 0) {
                console.log(`🍞 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] ✅ 检测到知识点: grammar=${pendingGrammar.length}, vocab=${pendingVocab.length}`)
                
                // 🔧 根据类型生成不同的 toast 消息
                const items = []
                const seenItems = new Set()  // 🔧 用于去重
                
                // 处理语法知识点
                pendingGrammar.forEach(g => {
                  // 🔧 修复：后端返回的字段名是 'name'，不是 'display_name'
                  const name = g.name || g.display_name || g.title || g.rule || tUI('语法')
                  const type = g.type || 'new'  // 默认为新知识点
                  
                  // 🔧 去重：使用 name 作为唯一标识
                  const itemKey = `grammar:${name}`
                  if (seenItems.has(itemKey)) {
                    console.log(`⚠️ [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 跳过重复的语法知识点: ${name}`)
                    return
                  }
                  seenItems.add(itemKey)
                  
                  if (type === 'existing') {
                    // 已有知识点：使用新文案
                    const message = tUI('已有知识点：{type} {name} 加入新例句')
                      .replace('{type}', tUI('语法'))
                      .replace('{name}', name)
                    items.push({ message, type: 'existing', key: itemKey })
                  } else {
                    // 新知识点：保持现状
                    items.push({ 
                      message: `🆕 ${tUI('语法')}: ${name} ${tUI('知识点已总结并加入列表')}`, 
                      type: 'new',
                      key: itemKey
                    })
                  }
                })
                
                // 处理词汇知识点
                pendingVocab.forEach(v => {
                  const vocab = v.vocab || tUI('词汇')
                  const type = v.type || 'new'  // 默认为新知识点
                  
                  // 🔧 去重：使用 vocab 作为唯一标识
                  const itemKey = `vocab:${vocab}`
                  if (seenItems.has(itemKey)) {
                    console.log(`⚠️ [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 跳过重复的词汇知识点: ${vocab}`)
                    return
                  }
                  seenItems.add(itemKey)
                  
                  if (type === 'existing') {
                    // 已有知识点：使用新文案
                    const message = tUI('已有知识点：{type} {name} 加入新例句')
                      .replace('{type}', tUI('词汇'))
                      .replace('{name}', vocab)
                    items.push({ message, type: 'existing', key: itemKey })
                  } else {
                    // 新知识点：保持现状
                    items.push({ 
                      message: `🆕 ${tUI('词汇')}: ${vocab} ${tUI('知识点已总结并加入列表')}`, 
                      type: 'new',
                      key: itemKey
                    })
                  }
                })
                
                console.log(`🍞 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 准备创建 ${items.length} 个toast`)
                console.log(`🍞 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] items:`, items)
                console.log(`🍞 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 当前toasts数量:`, toasts.length)
                
                // 🔧 修复：一次性创建所有 toast，确保所有知识点都能显示
                setToasts(prev => {
                  const baseSlot = prev.length
                  const newToasts = items.map((item, idx) => {
                    const id = Date.now() + Math.random() * 1000 + idx
                    const newToast = { 
                      id, 
                      message: item.message, 
                      slot: baseSlot + idx
                    }
                    console.log(`🍞 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 创建toast ${idx + 1}/${items.length}:`, newToast)
                    return newToast
                  })
                  const updated = [...prev, ...newToasts]
                  console.log(`🍞 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] setToasts更新: 从${prev.length}个增加到${updated.length}个`)
                  window.chatViewToastsRef = updated
                  return updated
                })
                
                // 🔧 刷新 notation 缓存，使 article view 自动更新
                if (refreshGrammarNotations) {
                  console.log('🔄 [ChatView] handleSuggestedQuestionSelect - 检测到新知识点，刷新 notation 缓存...')
                  refreshGrammarNotations()
                }
                
                // 🔧 找到数据后立即停止轮询
                if (pollPendingKnowledgeRef.current) {
                  clearInterval(pollPendingKnowledgeRef.current)
                  pollPendingKnowledgeRef.current = null
                  console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] ✅ 已停止轮询`)
                }
                return
              } else {
                console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] ⏸️ 暂无新知识点，继续轮询...`)
              }
            } catch (err) {
              console.error(`⚠️ [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 轮询失败:`, err)
              console.error(`⚠️ [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] 错误详情:`, err.message, err.stack)
              // 🔧 出错时也停止轮询，避免无限重试
              if (pollPendingKnowledgeRef.current) {
                clearInterval(pollPendingKnowledgeRef.current)
                pollPendingKnowledgeRef.current = null
                console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] ❌ 因错误停止轮询`)
              }
            }
            
            // 🔧 达到最大轮询次数后停止
            if (pollCount >= maxPolls) {
              console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - [轮询${pollCount}] ⏸️ 达到最大轮询次数(${maxPolls})，停止轮询`)
              if (pollPendingKnowledgeRef.current) {
                clearInterval(pollPendingKnowledgeRef.current)
                pollPendingKnowledgeRef.current = null
              }
            }
          }
          
          // 🔧 延迟启动轮询，给后台任务一些时间执行（线上服务器可能需要更长时间）
          setTimeout(() => {
            // 立即执行第一次轮询
            pollOnce()
            
            // 然后设置定时轮询
            pollPendingKnowledgeRef.current = setInterval(pollOnce, pollInterval)
            console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - ✅ 轮询已设置，interval ID:`, pollPendingKnowledgeRef.current)
          }, 500)  // 🔧 延迟 500ms 启动，确保后台任务有时间开始执行
          
          // 🔧 设置超时清理（双重保险）
          setTimeout(() => {
            if (pollPendingKnowledgeRef.current) {
              clearInterval(pollPendingKnowledgeRef.current)
              pollPendingKnowledgeRef.current = null
              console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - ⏸️ 超时清理轮询`)
            }
          }, 500 + maxPolls * pollInterval)  // 🔧 加上延迟启动的时间
        } else {
          console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - ❌ textId无效(${textId})，无法启动轮询`)
        }
      } else {
        console.log(`🔍 [ChatView] handleSuggestedQuestionSelect - ⏸️ 不满足轮询条件（响应中有即时返回的新知识点或response为空），跳过轮询`)
      }
    } catch (error) {
      console.error('❌ [ChatView] 发送消息失败:', error)
      // ⚠️ Language detection in error handler: Presentation-only, does NOT affect error handling logic
      const errorMsg = {
        id: generateMessageId(),
        text: `${t("抱歉，处理您的问题时出现错误: ")}${error.message || t("未知错误")}`,
        isUser: false,
        timestamp: new Date(),
        articleId: articleId ? String(articleId) : undefined  // 🔧 添加 articleId 用于跨设备同步
      }
      addMessage(errorMsg)
    } finally {
      setIsProcessing(false)
      sendingRef.current = false
    }
  }
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }
  
  const formatTime = (date) => {
    if (!date) return ''
    const dateObj = date instanceof Date ? date : new Date(date)
    if (isNaN(dateObj.getTime())) return ''
    return dateObj.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  const handleMessageAreaBlankClickCapture = useCallback((e) => {
    // Only clear quote when user clicks non-interactive blank areas in messages area.
    const target = e.target
    if (!(target instanceof Element)) return

    const interactiveSelector = [
      '[data-chat-message-bubble]',
      'button',
      'input',
      'textarea',
      'a',
      '[role="button"]',
      '[data-keep-quote]',
    ].join(', ')

    if (target.closest(interactiveSelector)) {
      return
    }

    if (quotedText && onClearQuote) {
      onClearQuote()
    }
  }, [quotedText, onClearQuote])
  
  // ⚠️ Language detection: Presentation-only, does NOT affect data fetching
  // Using useTranslate() hook which uses UI language context (same as header)
  
  return (
    <>
      <style>{`
        .chat-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .chat-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .chat-scrollbar::-webkit-scrollbar-thumb {
          background: #d1d5db;
          border-radius: 4px;
        }
        .chat-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #9ca3af;
        }
      `}</style>
      <div 
        ref={chatContainerRef}
        className={`flex flex-col bg-white rounded-lg shadow-md flex-shrink-0 relative ${disabled ? 'opacity-50' : ''}`}
        style={{ width: `${chatWidth}px` }}
      >
      {/* Resize Handle - 左侧拖拽条 */}
      <div
        className="absolute top-0 bottom-0 cursor-col-resize z-10 group"
        style={{ 
          left: '-4px',
          width: '8px'
        }}
        onMouseDown={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setIsResizing(true)
        }}
        title="拖拽调整宽度"
      >
        <div className="absolute inset-0 bg-transparent group-hover:bg-gray-400 active:bg-gray-500 transition-colors" />
      </div>
      
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg flex-shrink-0">
        <h2 className="text-lg font-semibold text-gray-800">
          {disabled ? t('学习助手 (暂时不可用)') : t('学习助手')}
        </h2>
        {disabled && (
          <p className="text-sm text-gray-600">
            {t('请先上传文章内容')}
          </p>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
        <div
          ref={scrollContainerRef}
          className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3 chat-scrollbar"
          onClickCapture={handleMessageAreaBlankClickCapture}
        >
          {messages.length === 0 ? (
            <div className="text-center text-gray-400 py-8">
              <p>{t('暂无消息')}</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  data-chat-message-bubble
                  className={`px-3 py-2 rounded-lg ${
                    message.isUser
                      ? 'bg-white text-gray-900 border border-gray-300 rounded-br-none'
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                  }`}
                  style={{ 
                    maxWidth: `${chatWidth - 64}px` // chatWidth - 左右padding(32px) - 消息间距(32px)
                  }}
                >
                  {message.isUser && message.quote && (
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
                      <div className="font-medium mb-1">{t('引用')}</div>
                      <div
                        className="italic"
                        style={{
                          display: '-webkit-box',
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          wordBreak: 'break-word',
                        }}
                      >
                        "{message.quote}"
                      </div>
                    </div>
                  )}
                  
                  <p className="text-sm">
                    {(!message.isUser && (message.text === '选择有疑问的句子或词汇，向我提问吧！' || message.text === '你好！我是聊天助手，有什么可以帮助你的吗？'))
                      ? t('选择有疑问的句子或词汇，向我提问吧！')
                      : (!message.isUser
                          ? renderSimpleMarkdown(message.text)
                          : message.text)}
                  </p>
                  <p className="text-xs mt-1 text-gray-500">
                    {formatTime(message.timestamp)}
                  </p>
                </div>
              </div>
            ))
          )}
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
                style={!hasSelectedSentence ? { color: colors.primary[600] } : {}}
              >
                {hasSelectedSentence ? t('引用整句（继续提问将保持此引用）') : t('引用（继续提问将保持此引用）')}
              </div>
              <div 
                className={`text-sm italic ${hasSelectedSentence ? 'text-green-800' : ''}`}
                style={{
                  ...(!hasSelectedSentence ? { color: colors.primary[800] } : {}),
                  display: '-webkit-box',
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  wordBreak: 'break-word'
                }}
              >
                "{quotedText}"
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Suggested Questions */}
      <SuggestedQuestions
        quotedText={quotedText}
        onQuestionSelect={handleSuggestedQuestionSelect}
        isVisible={!!quotedText}
        inputValue={inputText}
        onQuestionClick={() => {}}
        tokenCount={selectedTokenCount}
        hasSelectedSentence={hasSelectedSentence}
        disabled={isProcessing}
      />

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg flex-shrink-0">
        {/* 🔧 Token不足提示 */}
        {tokenInsufficient && !isProcessing && (
          <div className="mb-2 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
            {t('积分不足')}
          </div>
        )}
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              disabled 
                ? t("聊天暂时不可用")
                : isProcessing 
                  ? t("AI 正在处理中，请稍候...")
                  : tokenInsufficient 
                    ? t("积分不足，无法使用AI聊天功能")
                    : (!hasSelectedToken && !hasSelectedSentence) 
                      ? t("请先选择文章中的词汇或句子")
                      : (quotedText 
                          ? `${t("回复引用：")}"${quotedText}"`
                          : t("输入消息...")
                        )
            }
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:border-transparent"
            style={{ '--tw-ring-color': colors.primary[500] }}
            onFocus={(e) => {
              e.currentTarget.style.boxShadow = `0 0 0 2px ${colors.primary[500]}40`
            }}
            onBlur={(e) => {
              e.currentTarget.style.boxShadow = ''
            }}
            disabled={disabled || isProcessing || tokenInsufficient || (!hasSelectedToken && !hasSelectedSentence)}
          />
          <button
            type="button"
            onClick={handleSendMessage}
            disabled={inputText.trim() === '' || disabled || isProcessing || tokenInsufficient || (!hasSelectedToken && !hasSelectedSentence)}
            className="px-4 py-2 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors hover:brightness-95 active:brightness-90"
            style={{
              backgroundColor: colors.primary[600],
              '--tw-ring-color': colors.primary[300],
            }}
            title={
              tokenInsufficient 
                ? t("积分不足")
                : (!hasSelectedToken && !hasSelectedSentence) 
                  ? t("请先选择文章中的词汇或句子")
                  : t("发送消息")
            }
          >
            {t("发送")}
          </button>
        </div>
      </div>
      </div>

      {/* Toast Stack - 使用 Portal 渲染到 body 外，避免影响 ChatView 渲染 */}
      {useMemo(() => {
        if (typeof document === 'undefined' || toasts.length === 0) {
          return null
        }
        
        return createPortal(
          <div 
            className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[9999] pointer-events-none"
            style={{
              willChange: 'transform',  // 🔧 优化：提示浏览器优化 transform
              isolation: 'isolate',  // 🔧 创建新的层叠上下文，避免影响其他元素
              // 🔧 注意：contain 属性可能不被所有浏览器支持，如果导致问题可以移除
              // contain: 'layout style paint',  // 🔧 优化：限制重排和重绘的影响范围
              transform: 'translateX(-50%)',  // 🔧 使用 transform 而不是 left，避免布局重排
            }}
          >
            {toasts.map(t => (
              <div
                key={t.id}
                className="pointer-events-auto"
                style={{
                  position: 'absolute',
                  bottom: `${t.slot * 80}px`,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  zIndex: 10000 + t.slot,
                  width: 'auto',
                  minWidth: '320px',
                  willChange: 'transform',  // 🔧 优化：提示浏览器优化 transform
                }}
              >
                <ToastNotice
                  message={t.message}
                  isVisible={true}
                  duration={10000}
                  onClose={() => handleToastClose(t.id)}
                />
              </div>
            ))}
          </div>,
          document.body
        )
      }, [toasts])}
    </>
  )
}

// 🔧 使用 React.memo 包装，避免在 autoTranslationEnabled 变化时不必要的重新渲染
export default memo(ChatView, (prevProps, nextProps) => {
  // 自定义比较函数：只在相关 props 变化时重新渲染
  return (
    prevProps.quotedText === nextProps.quotedText &&
    prevProps.onClearQuote === nextProps.onClearQuote &&
    prevProps.disabled === nextProps.disabled &&
    prevProps.hasSelectedToken === nextProps.hasSelectedToken &&
    prevProps.selectedTokenCount === nextProps.selectedTokenCount &&
    prevProps.selectionContext === nextProps.selectionContext &&
    prevProps.markAsAsked === nextProps.markAsAsked &&
    prevProps.createVocabNotation === nextProps.createVocabNotation &&
    prevProps.refreshAskedTokens === nextProps.refreshAskedTokens &&
    prevProps.refreshGrammarNotations === nextProps.refreshGrammarNotations &&
    prevProps.articleId === nextProps.articleId &&
    prevProps.hasSelectedSentence === nextProps.hasSelectedSentence &&
    prevProps.selectedSentence === nextProps.selectedSentence &&
    prevProps.addGrammarNotationToCache === nextProps.addGrammarNotationToCache &&
    prevProps.addVocabNotationToCache === nextProps.addVocabNotationToCache &&
    prevProps.addGrammarRuleToCache === nextProps.addGrammarRuleToCache &&
    prevProps.addVocabExampleToCache === nextProps.addVocabExampleToCache &&
    prevProps.isProcessing === nextProps.isProcessing &&
    prevProps.onProcessingChange === nextProps.onProcessingChange
  )
})

