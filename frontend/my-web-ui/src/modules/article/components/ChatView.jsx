import { useState, useRef, useEffect } from 'react'
import ToastNotice from './ToastNotice'
import SuggestedQuestions from './SuggestedQuestions'
import { useChatEvent } from '../contexts/ChatEventContext'

export default function ChatView({ quotedText, onClearQuote, disabled = false }) {
  const { pendingMessage, clearPendingMessage } = useChatEvent()
  const [messages, setMessages] = useState([
    { id: 1, text: "你好！我是聊天助手，有什么可以帮助你的吗？", isUser: false, timestamp: new Date() },
    { id: 2, text: "这是一条测试消息，用来测试滚动功能是否正常工作。", isUser: true, timestamp: new Date() },
    { id: 3, text: "另一条测试消息，确保聊天框有足够的内容来测试滚动。", isUser: false, timestamp: new Date() },
    { id: 4, text: "继续添加更多消息来测试滚动功能。", isUser: true, timestamp: new Date() },
    { id: 5, text: "这是第五条消息，应该足够测试滚动功能了。", isUser: false, timestamp: new Date() },
    { id: 6, text: "第六条消息，继续测试滚动。", isUser: true, timestamp: new Date() },
    { id: 7, text: "第七条消息，确保有足够的内容。", isUser: false, timestamp: new Date() },
    { id: 8, text: "第八条消息，测试滚动功能。", isUser: true, timestamp: new Date() },
    { id: 9, text: "第九条消息，继续测试。", isUser: false, timestamp: new Date() },
    { id: 10, text: "第十条消息，应该足够测试滚动功能了。", isUser: true, timestamp: new Date() }
  ])
  const [inputText, setInputText] = useState('')
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const messagesEndRef = useRef(null)

  // 新增：自动滚动到底部的函数
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // 新增：监听messages变化，自动滚动到底部
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 新增：监听待发送消息
  useEffect(() => {
    if (pendingMessage) {
      // 自动发送消息
      const userMessage = {
        id: Date.now(),
        text: pendingMessage.text,
        isUser: true,
        timestamp: pendingMessage.timestamp,
        quote: pendingMessage.quotedText || null
      }
      
      setMessages(prev => [...prev, userMessage])
      
      // 清除待发送消息
      clearPendingMessage()
      
      // 清空当前引用（如果有的话）
      if (onClearQuote) {
        onClearQuote()
      }

      // Auto reply after a short delay
      setTimeout(() => {
        const autoReply = {
          id: Date.now() + 1,
          text: `关于"${pendingMessage.quotedText}"，我来为你提供详细解释。这是一个很好的问题！`,
          isUser: false,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, autoReply])
      }, 1000)
    }
  }, [pendingMessage, clearPendingMessage, onClearQuote])

  const handleSendMessage = () => {
    if (inputText.trim() === '') return

    // Add user message with quote if exists
    const userMessage = {
      id: Date.now(),
      text: inputText,
      isUser: true,
      timestamp: new Date(),
      quote: quotedText || null
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputText('')
    
    // Clear quote after sending
    if (onClearQuote) {
      onClearQuote()
    }

    // Auto reply after a short delay
    setTimeout(() => {
      const autoReply = {
        id: Date.now() + 1,
        text: `我收到了你的消息："${inputText}"。这是一个自动回复，感谢你的输入！`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, autoReply])
      
      // Show toast notice after AI reply
      setTimeout(() => {
        const knowledgePoints = [
          'React 组件化开发',
          '虚拟 DOM 技术',
          'JSX 语法要点',
          '状态管理基础',
          '生命周期钩子',
          '事件处理范式',
          '条件渲染技巧',
          '列表渲染优化'
        ]
        const randomPoint = knowledgePoints[Math.floor(Math.random() * knowledgePoints.length)]
        setToastMessage(`${randomPoint} 知识点已总结并加入列表`)
        setShowToast(true)
      }, 500) // 延迟 500ms 显示 toast
    }, 1000)
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

  const handleSuggestedQuestionSelect = (question) => {
    // 自动发送已选择的问题
    const userMessage = {
      id: Date.now(),
      text: question,
      isUser: true,
      timestamp: new Date(),
      quote: quotedText || null
    }
    
    setMessages(prev => [...prev, userMessage])
    
    // 发送后清空引用
    if (onClearQuote) {
      onClearQuote()
    }

    // Auto reply after a short delay
    setTimeout(() => {
      const autoReply = {
        id: Date.now() + 1,
        text: `关于"${quotedText}"，你问的是「${question}」。这是一个很好的问题，我来为你详细解释`,
        isUser: false,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, autoReply])
      
      // Show toast notice after AI reply
      setTimeout(() => {
        const knowledgePoints = [
          'React 组件化开发',
          '虚拟 DOM 技术',
          'JSX 语法要点',
          '状态管理基础',
          '生命周期钩子',
          '事件处理范式',
          '条件渲染技巧',
          '列表渲染优化'
        ]
        const randomPoint = knowledgePoints[Math.floor(Math.random() * knowledgePoints.length)]
        setToastMessage(`${randomPoint} 知识点已总结并加入列表`)
        setShowToast(true)
      }, 500)
    }, 1000)
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
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className={`w-80 flex flex-col bg-white rounded-lg shadow-md h-full relative ${disabled ? 'opacity-50' : ''}`}>
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <h2 className="text-lg font-semibold text-gray-800">
          {disabled ? '聊天助手 (暂时不可用)' : '聊天助手'}
        </h2>
        <p className="text-sm text-gray-600">
          {disabled ? '请先上传文章内容' : '随时为您提供帮助'}
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3 max-h-[calc(100vh-200px)]">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs px-3 py-2 rounded-lg ${
                message.isUser
                  ? 'bg-blue-500 text-white rounded-br-none'
                  : 'bg-gray-100 text-gray-800 rounded-bl-none'
              }`}
            >
              {/* Quote display */}
              {message.quote && (
                <div className={`mb-2 p-2 rounded text-xs ${
                  message.isUser 
                    ? 'bg-blue-400 text-blue-50' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  <div className="font-medium mb-1">引用</div>
                  <div className="italic">"{message.quote}"</div>
                </div>
              )}
              
              <p className="text-sm">{message.text}</p>
              <p className={`text-xs mt-1 ${
                message.isUser ? 'text-blue-100' : 'text-gray-500'
              }`}>
                {formatTime(message.timestamp)}
              </p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quote Display */}
      {quotedText && (
        <div className="px-4 py-2 bg-blue-50 border-t border-blue-200">
          <div className="flex items-center">
            <div className="flex-1">
              <div className="text-xs text-blue-600 font-medium mb-1">引用</div>
              <div className="text-sm text-blue-800 italic">"{quotedText}"</div>
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
        onQuestionClick={handleQuestionClick}
      />

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={disabled ? "聊天暂时不可用" : (quotedText ? `回复引用："${quotedText}"` : "输入消息...") }
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={disabled}
          />
          <button
            onClick={handleSendMessage}
            disabled={inputText.trim() === '' || disabled}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            发送
          </button>
        </div>
      </div>

      {/* Toast Notice */}
      <ToastNotice
        message={toastMessage}
        isVisible={showToast}
        onClose={handleToastClose}
        duration={2000}
      />
    </div>
  )
}



