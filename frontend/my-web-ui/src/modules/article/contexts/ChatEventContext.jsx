import { createContext, useContext, useState } from 'react'

const ChatEventContext = createContext()

export const useChatEvent = () => {
  const context = useContext(ChatEventContext)
  if (!context) {
    throw new Error('useChatEvent must be used within a ChatEventProvider')
  }
  return context
}

export const ChatEventProvider = ({ children }) => {
  const [pendingMessage, setPendingMessage] = useState(null)
  const [pendingToast, setPendingToast] = useState(null)
  const [pendingContext, setPendingContext] = useState(null) // 新增：保存待发送消息的 context

  // 发送消息到Chat
  const sendMessageToChat = (message, quotedText = null, context = null) => {
    console.log('📤 [ChatEvent] sendMessageToChat 被调用', {
      message,
      quotedText,
      hasContext: !!context
    })
    
    // 过滤空消息
    if (!message || String(message).trim() === '' || message === 'null' || message === 'undefined') {
      console.warn('⚠️ [ChatEvent] Ignoring empty/null message:', message)
      return
    }
    
    console.log('✅ [ChatEvent] 设置 pendingMessage', {
      text: message,
      quotedText: quotedText,
      hasContext: !!context
    })
    
    setPendingMessage({
      text: message,
      quotedText: quotedText,
      timestamp: new Date()
    })
    
    // 如果有 context，也保存起来
    if (context) {
      console.log('✅ [ChatEvent] 设置 pendingContext', {
        hasSentence: !!context.sentence,
        hasTokens: !!context.tokens,
        tokensCount: context.tokens?.length || 0
      })
      setPendingContext(context)
    }
  }
  
  // 清除待发送的 context
  const clearPendingContext = () => {
    setPendingContext(null)
  }

  // 清除待发送消息
  const clearPendingMessage = () => {
    setPendingMessage(null)
  }

  // 触发知识点 Toast
  const triggerKnowledgeToast = (message) => {
    setPendingToast(String(message ?? ''))
  }

  const clearPendingToast = () => setPendingToast(null)

  return (
    <ChatEventContext.Provider value={{
      pendingMessage,
      sendMessageToChat,
      clearPendingMessage,
      pendingContext,
      clearPendingContext,
      pendingToast,
      triggerKnowledgeToast,
      clearPendingToast
    }}>
      {children}
    </ChatEventContext.Provider>
  )
} 