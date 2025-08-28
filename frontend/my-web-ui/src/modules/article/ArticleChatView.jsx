import { useState } from 'react'
import ArticleViewer from './components/ArticleViewer'
import UploadInterface from './components/UploadInterface'
import UploadProgress from './components/UploadProgress'
import ChatView from './components/ChatView'

export default function ArticleChatView({ articleId, onBack, isUploadMode = false, onUploadComplete }) {
  const [selectedTokens, setSelectedTokens] = useState([])
  const [quotedText, setQuotedText] = useState('')
  const [showUploadProgress, setShowUploadProgress] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  
  // Sample text for the ArticleViewer
  const sampleText = isUploadMode ? '' : `React 是一个用于构建用户界面的 JavaScript 库。它由 Facebook 开发和维护，被广泛用于构建单页应用程序。React 使用组件化的架构，让开发者可以创建可重用的 UI 组件。它的虚拟 DOM 技术提供了高效的渲染性能，而 JSX 语法让组件的编写更加直观。React 生态系统非常丰富，包括 React Router 用于路由管理，Redux 用于状态管理，以及各种 UI 组件库。`

  const handleTokenSelect = (token, allSelectedTokens) => {
    setSelectedTokens(Array.from(allSelectedTokens))
    // 设置引用文本为选中的词汇
    if (allSelectedTokens.size > 0) {
      setQuotedText(Array.from(allSelectedTokens).join(' '))
    } else {
      setQuotedText('')
    }
    console.log('Selected token:', token)
    console.log('All selected tokens:', Array.from(allSelectedTokens))
  }

  const handleClearQuote = () => {
    setQuotedText('')
  }

  const handleUploadStart = () => {
    setShowUploadProgress(true)
  }

  const handleUploadComplete = () => {
    setUploadComplete(true)
    setShowUploadProgress(false)
    // 调用父组件的完成回调
    if (onUploadComplete) {
      onUploadComplete()
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header with Back Button */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span>Back to Articles</span>
          </button>
        </div>
        <div className="text-sm text-gray-500">
          Article ID: {articleId}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex gap-8 h-full min-h-0 p-4">
        {isUploadMode ? (
          showUploadProgress ? (
            <UploadProgress onComplete={handleUploadComplete} />
          ) : (
            <UploadInterface onUploadStart={handleUploadStart} />
          )
        ) : (
          <ArticleViewer 
            text={sampleText} 
            onTokenSelect={handleTokenSelect}
          />
        )}
        <ChatView 
          quotedText={quotedText}
          onClearQuote={handleClearQuote}
          disabled={isUploadMode && !uploadComplete}
        />
      </div>
    </div>
  )
} 