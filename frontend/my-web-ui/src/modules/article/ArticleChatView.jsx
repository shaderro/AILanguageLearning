import { useState, useEffect } from 'react'
import ArticleViewer from './components/ArticleViewer'
import UploadInterface from './components/UploadInterface'
import UploadProgress from './components/UploadProgress'
import ChatView from './components/ChatView'
import { ChatEventProvider } from './contexts/ChatEventContext'

export default function ArticleChatView({ articleId, onBack, isUploadMode = false, onUploadComplete }) {
  const [selectedTokens, setSelectedTokens] = useState([])
  const [quotedText, setQuotedText] = useState('')
  const [showUploadProgress, setShowUploadProgress] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [hasSelectedToken, setHasSelectedToken] = useState(false)
  
  // Sample text for the ArticleViewer
  const sampleText = isUploadMode ? '' : 'Sample text for demo'

  const handleTokenSelect = (tokenText, selectedSet, selectedTexts = []) => {
    setSelectedTokens(selectedTexts)
    setQuotedText(selectedTexts.join(' '))
    setHasSelectedToken(selectedTexts.length > 0)
    console.log('Selected token:', tokenText)
    console.log('All selected tokens:', selectedTexts)
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
    <ChatEventProvider>
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

        {/* Main Content (slightly shorter than viewport to fully show both panels) */}
        <div className="flex gap-8 flex-1 p-4 overflow-hidden">
          {isUploadMode ? (
            showUploadProgress ? (
              <UploadProgress onComplete={handleUploadComplete} />
            ) : (
              <UploadInterface onUploadStart={handleUploadStart} />
            )
          ) : (
            <ArticleViewer 
              articleId={articleId} 
              onTokenSelect={handleTokenSelect}
            />
          )}
          <ChatView 
            quotedText={quotedText}
            onClearQuote={handleClearQuote}
            disabled={isUploadMode && !uploadComplete}
            hasSelectedToken={hasSelectedToken}
          />
        </div>
      </div>
    </ChatEventProvider>
  )
} 



