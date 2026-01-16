import { useState, useRef, useEffect, useCallback } from 'react'
import { flushSync } from 'react-dom'
import ToastNotice from './ToastNotice'
import SuggestedQuestions from './SuggestedQuestions'
import { useChatEvent } from '../contexts/ChatEventContext'
import { useTranslationDebug } from '../../../contexts/TranslationDebugContext'
import { useRefreshData } from '../../../hooks/useApi'
import { colors } from '../../../design-tokens'

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

export default function ChatView({ 
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
  
  const scrollContainerRef = useRef(null)
  const messageIdCounterRef = useRef(0)
  const generateMessageId = () => {
    messageIdCounterRef.current += 1
    return Date.now() + Math.random() + messageIdCounterRef.current
  }
  
  const normalizedArticleId = articleId ? String(articleId) : 'default'
  
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
    
    return fromLS.length > 0 ? fromLS : [
      { id: 1, text: "你好！我是聊天助手，有什么可以帮助你的吗？", isUser: false, timestamp: new Date() }
    ]
  }
  
  const [messages, setMessages] = useState(getInitialMessages)
  const [inputText, setInputText] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  
  // 🔧 Toast 管理
  if (!window.chatViewToastsRef) {
    window.chatViewToastsRef = []
  }
  const [toasts, setToasts] = useState(() => window.chatViewToastsRef || [])
  
  // 🔧 同步全局 ref
  useEffect(() => {
    window.chatViewMessagesRef[normalizedArticleId] = messages
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
    
    loadingHistoryRef.current = true
    const loadHistory = async () => {
      try {
        const { apiService } = await import('../../../services/api')
        const resp = await apiService.getChatHistory({ textId: articleId, limit: 200 })
        const items = resp?.data?.data?.items || []
        
        if (items.length > 0) {
          const historyMessages = items.map(item => ({
            id: item.id,
            text: item.message,
            isUser: item.is_user,
            timestamp: new Date(item.created_at),
            quote: item.quote || null
          })).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
          
          // 🔧 合并历史记录和当前消息（去重）
          setMessages(prev => {
            const existingIds = new Set(prev.map(m => m.id))
            const newMessages = historyMessages.filter(m => !existingIds.has(m.id))
            const merged = [...prev, ...newMessages].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
            window.chatViewMessagesRef[normalizedArticleId] = merged
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
  }, [articleId, normalizedArticleId])
  
  // 🔧 添加消息（立即显示）
  const addMessage = useCallback((newMessage) => {
    flushSync(() => {
      setMessages(prev => {
        if (prev.some(m => m.id === newMessage.id)) {
          return prev
        }
        const updated = [...prev, newMessage].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
        window.chatViewMessagesRef[normalizedArticleId] = updated
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
  }, [normalizedArticleId])
  
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
  
  // 🔧 处理 pendingMessage（来自 useChatEvent）
  useEffect(() => {
    if (!pendingMessage || isProcessing) return
    
    console.log('📥 [ChatView] 收到 pendingMessage', {
      text: pendingMessage.text,
      quotedText: pendingMessage.quotedText,
      hasContext: !!pendingContext
    })
    
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
        quote: currentQuotedText || null
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
        
        const response = await apiService.sendChat({ user_question: questionText })
        
        // 🔧 添加 AI 回答
        if (response?.ai_response) {
          const parsedResponse = parseAIResponse(response.ai_response)
          const aiMessage = {
            id: generateMessageId(),
            text: parsedResponse || response.ai_response,
            isUser: false,
            timestamp: new Date()
          }
          addMessage(aiMessage)
        }
        
        // 🔧 处理 notations（与 handleSendMessage 相同）
        if (response?.created_grammar_notations?.length > 0) {
          response.created_grammar_notations.forEach(n => {
            if (addGrammarNotationToCache) addGrammarNotationToCache(n)
          })
        }
        if (response?.created_vocab_notations?.length > 0) {
          response.created_vocab_notations.forEach(n => {
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
      } catch (error) {
        console.error('❌ [ChatView] 发送 pendingMessage 失败:', error)
        const errorMsg = {
          id: generateMessageId(),
          text: `抱歉，处理您的问题时出现错误: ${error.message || '未知错误'}`,
          isUser: false,
          timestamp: new Date()
        }
        addMessage(errorMsg)
      } finally {
        setIsProcessing(false)
        clearPendingMessage()
        clearPendingContext()
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
  
  // 🔧 发送消息
  const handleSendMessage = async () => {
    if (inputText.trim() === '' || isProcessing) return
    
    setIsProcessing(true)
    const questionText = inputText
    const currentQuotedText = quotedText
    const currentSelectionContext = selectionContext
    
    // 🔧 立即添加用户消息
    const userMessage = {
      id: generateMessageId(),
      text: questionText,
      isUser: true,
      timestamp: new Date(),
      quote: currentQuotedText || null
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
      
      const response = await apiService.sendChat({ user_question: questionText })
      
      // 🔧 添加 AI 回答
      if (response?.ai_response) {
        const parsedResponse = parseAIResponse(response.ai_response)
        const aiMessage = {
          id: generateMessageId(),
          text: parsedResponse || response.ai_response,
          isUser: false,
          timestamp: new Date()
        }
        addMessage(aiMessage)
      }
      
      // 🔧 处理 notations
      if (response?.created_grammar_notations?.length > 0) {
        response.created_grammar_notations.forEach(n => {
          if (addGrammarNotationToCache) addGrammarNotationToCache(n)
        })
      }
      if (response?.created_vocab_notations?.length > 0) {
        response.created_vocab_notations.forEach(n => {
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
      
      // 🔧 轮询新知识点
      if (response && !response.grammar_to_add?.length && !response.vocab_to_add?.length) {
        const textId = currentSelectionContext?.sentence?.text_id || articleId
        const userId = parseInt(localStorage.getItem('user_id') || '2')
        
        if (textId) {
          let pollCount = 0
          const maxPolls = 10
          const pollInterval = 1000
          
          const pollPendingKnowledge = setInterval(async () => {
            pollCount++
            try {
              const { apiService } = await import('../../../services/api')
              const resp = await apiService.getPendingKnowledge({ user_id: userId, text_id: textId })
              const data = resp?.data?.data || {}
              
              const pendingGrammar = data.pending_grammar || []
              const pendingVocab = data.pending_vocab || []
              
              if (pendingGrammar.length > 0 || pendingVocab.length > 0) {
                const items = [
                  ...pendingGrammar.map(g => `🆕 语法: ${g.title || g.rule || '新语法'}`),
                  ...pendingVocab.map(v => `🆕 词汇: ${v.vocab || '新词汇'}`)
                ]
                
                items.forEach((item, idx) => {
                  setTimeout(() => {
                    const id = Date.now() + Math.random()
                    const newToast = { id, message: `${item} 知识点已总结并加入列表`, slot: toasts.length + idx }
                    setToasts(prev => {
                      const updated = [...prev, newToast]
                      window.chatViewToastsRef = updated
                      return updated
                    })
                  }, idx * 600)
                })
                
                clearInterval(pollPendingKnowledge)
              }
            } catch (err) {
              console.warn('⚠️ [ChatView] 轮询失败:', err)
            }
            
            if (pollCount >= maxPolls) {
              clearInterval(pollPendingKnowledge)
            }
          }, pollInterval)
          
          setTimeout(() => clearInterval(pollPendingKnowledge), maxPolls * pollInterval)
        }
      }
    } catch (error) {
      console.error('❌ [ChatView] 发送消息失败:', error)
      const errorMsg = {
        id: generateMessageId(),
        text: `抱歉，处理您的问题时出现错误: ${error.message || '未知错误'}`,
        isUser: false,
        timestamp: new Date()
      }
      addMessage(errorMsg)
    } finally {
      setIsProcessing(false)
    }
  }
  
  // 🔧 建议问题选择
  const handleSuggestedQuestionSelect = async (question) => {
    if (isProcessing) return
    
    setIsProcessing(true)
    const currentQuotedText = quotedText
    const currentSelectionContext = selectionContext
    
    // 🔧 立即添加用户消息
    const userMessage = {
      id: generateMessageId(),
      text: question,
      isUser: true,
      timestamp: new Date(),
      quote: currentQuotedText || null
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
      
      const response = await apiService.sendChat({ user_question: question })
      
      // 🔧 添加 AI 回答
      if (response?.ai_response) {
        const parsedResponse = parseAIResponse(response.ai_response)
        const aiMessage = {
          id: generateMessageId(),
          text: parsedResponse || response.ai_response,
          isUser: false,
          timestamp: new Date()
        }
        addMessage(aiMessage)
      }
      
      // 🔧 处理 notations（与 handleSendMessage 相同）
      if (response?.created_grammar_notations?.length > 0) {
        response.created_grammar_notations.forEach(n => {
          if (addGrammarNotationToCache) addGrammarNotationToCache(n)
        })
      }
      if (response?.created_vocab_notations?.length > 0) {
        response.created_vocab_notations.forEach(n => {
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
    } catch (error) {
      console.error('❌ [ChatView] 发送消息失败:', error)
      const errorMsg = {
        id: generateMessageId(),
        text: `抱歉，处理您的问题时出现错误: ${error.message || '未知错误'}`,
        isUser: false,
        timestamp: new Date()
      }
      addMessage(errorMsg)
    } finally {
      setIsProcessing(false)
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
              style={!hasSelectedSentence ? { '--hover-bg': colors.primary[100] } : {}}
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
                style={!hasSelectedSentence ? { color: colors.primary[600] } : {}}
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
        onQuestionClick={() => {}}
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
            style={{ '--tw-ring-color': colors.primary[500] }}
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

      {/* Toast Stack */}
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[9999] pointer-events-none">
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
              minWidth: '320px'
            }}
          >
            <ToastNotice
              message={t.message}
              isVisible={true}
              duration={5000}
              onClose={() => {
                setToasts(prev => {
                  const newToasts = prev.filter(x => x.id !== t.id)
                  const reindexed = newToasts.map((toast, index) => ({
                    ...toast,
                    slot: index
                  }))
                  window.chatViewToastsRef = reindexed
                  return reindexed
                })
              }}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
