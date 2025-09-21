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

  // 发送消息到Chat
  const sendMessageToChat = (message, quotedText = null) => {
    setPendingMessage({
      text: message,
      quotedText: quotedText,
      timestamp: new Date()
    })
  }

  // 清除待发送消息
  const clearPendingMessage = () => {
    setPendingMessage(null)
  }

  return (
    <ChatEventContext.Provider value={{
      pendingMessage,
      sendMessageToChat,
      clearPendingMessage
    }}>
      {children}
    </ChatEventContext.Provider>
  )
} 