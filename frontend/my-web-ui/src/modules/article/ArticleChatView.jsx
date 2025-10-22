import { useState, useEffect } from 'react'
import ArticleViewer from './components/ArticleViewer'
import UploadInterface from './components/UploadInterface'
import UploadProgress from './components/UploadProgress'
import ChatView from './components/ChatView'
import { ChatEventProvider } from './contexts/ChatEventContext'
import { useAskedTokens } from './hooks/useAskedTokens'
import { useTokenNotations } from './hooks/useTokenNotations'
import { apiService } from '../../services/api'

export default function ArticleChatView({ articleId, onBack, isUploadMode = false, onUploadComplete }) {
  const [selectedTokens, setSelectedTokens] = useState([])
  const [quotedText, setQuotedText] = useState('')
  const [showUploadProgress, setShowUploadProgress] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [hasSelectedToken, setHasSelectedToken] = useState(false)
  const [currentContext, setCurrentContext] = useState(null)  // 新增：保存完整的选择上下文
  
  // 获取asked tokens功能（统一在这里管理，避免多次调用）
  const { askedTokenKeys, isTokenAsked, markAsAsked, refreshAskedTokens } = useAskedTokens(articleId, 'default_user')
  
  // 获取token notations功能
  const { getNotationContent, setNotationContent, clearNotationContent } = useTokenNotations()
  
  // Sample text for the ArticleViewer
  const sampleText = isUploadMode ? '' : 'Sample text for demo'

  const handleTokenSelect = async (tokenText, selectedSet, selectedTexts = [], context = null) => {
    setSelectedTokens(selectedTexts)
    setQuotedText(selectedTexts.join(' '))
    setHasSelectedToken(selectedTexts.length > 0)
    setCurrentContext(context)  // 保存完整的上下文信息
    
    console.log('🎯 [ArticleChatView] Token selection changed:')
    console.log('  - Selected text:', tokenText)
    console.log('  - All selected texts:', selectedTexts)
    console.log('  - Context:', context)
    
    // Send selection context to backend session state
    if (context && context.sentence && selectedTexts.length > 0) {
      try {
        console.log('📤 [ArticleChatView] Sending selection context to backend...')
        
        // Prepare the update payload
        const updatePayload = {
          sentence: context.sentence
        }
        
        // Handle multiple tokens
        if (context.tokens.length > 1) {
          updatePayload.token = {
            multiple_tokens: context.tokens,
            token_indices: context.tokenIndices,
            token_text: selectedTexts.join(' ')
          }
        } else if (context.tokens.length === 1) {
          // Single token selection
          const token = context.tokens[0]
          updatePayload.token = {
            token_body: token.token_body,
            sentence_token_id: token.sentence_token_id,
            global_token_id: token.global_token_id
          }
        }
        
        console.log('📤 [ArticleChatView] Update payload:', updatePayload)
        const response = await apiService.session.updateContext(updatePayload)
        console.log('✅ [ArticleChatView] Session context updated:', response)
      } catch (error) {
        console.error('❌ [ArticleChatView] Failed to update session context:', error)
      }
    } else if (selectedTexts.length === 0) {
      // Clear selection - no tokens selected
      console.log('🧹 [ArticleChatView] Clearing selection (no context to send)')
    }
  }

  const handleClearQuote = () => {
    setQuotedText('')
    setCurrentContext(null)  // 同时清除上下文
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
        <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200 flex-shrink-0">
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

        {/* Main Content - Fixed height with no overflow */}
        <div className="flex gap-8 flex-1 p-4 overflow-hidden min-h-0">
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
              isTokenAsked={isTokenAsked}
              markAsAsked={markAsAsked}
              getNotationContent={getNotationContent}
              setNotationContent={setNotationContent}
            />
          )}
          <ChatView 
            quotedText={quotedText}
            onClearQuote={handleClearQuote}
            disabled={isUploadMode && !uploadComplete}
            hasSelectedToken={hasSelectedToken}
            selectedTokenCount={selectedTokens.length || 1}
            selectionContext={currentContext}
            markAsAsked={markAsAsked}
            refreshAskedTokens={refreshAskedTokens}
            articleId={articleId}
          />
        </div>
      </div>
    </ChatEventProvider>
  )
} 



