import { useState, useEffect, useRef, useMemo } from 'react'
import ArticleViewer from './components/ArticleViewer'
import UploadInterface from './components/UploadInterface'
import UploadProgress from './components/UploadProgress'
import ChatView from './components/ChatView'
import { ChatEventProvider } from './contexts/ChatEventContext'
import { NotationContext } from './contexts/NotationContext'
import { SelectionProvider } from './selection/SelectionContext'
import { useSelection } from './selection/hooks/useSelection'

function ArticleCanvas({ children }) {
  const { clearSelection } = useSelection()
  return (
    <div onClick={() => clearSelection()}>
      {children}
    </div>
  )
}
import { useAskedTokens } from './hooks/useAskedTokens'
import { useTokenNotations } from './hooks/useTokenNotations'
import { useNotationCache } from './hooks/useNotationCache'
import { apiService } from '../../services/api'

export default function ArticleChatView({ articleId, onBack, isUploadMode = false, onUploadComplete }) {
  // 🔧 从 URL 参数读取 sentenceId（用于自动滚动和高亮）
  const getSentenceIdFromURL = () => {
    const params = new URLSearchParams(window.location.search)
    const sentenceId = params.get('sentenceId')
    return sentenceId ? parseInt(sentenceId) : null
  }
  const [targetSentenceId, setTargetSentenceId] = useState(getSentenceIdFromURL())
  
  // 空白处清空选择逻辑已移至 ArticleCanvas（在 SelectionProvider 内部使用 useSelection）
  const [selectedTokens, setSelectedTokens] = useState([])
  const [quotedText, setQuotedText] = useState('')
  const [showUploadProgress, setShowUploadProgress] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [hasSelectedToken, setHasSelectedToken] = useState(false)
  const [currentContext, setCurrentContext] = useState(null)  // 新增：保存完整的选择上下文
  const [selectedSentence, setSelectedSentence] = useState(null)  // 新增：保存选中的句子
  const [hasSelectedSentence, setHasSelectedSentence] = useState(false)  // 新增：是否有选中的句子
  
  // 获取asked tokens功能（统一在这里管理，避免多次调用）
  const { askedTokenKeys, isTokenAsked, markAsAsked, refreshAskedTokens } = useAskedTokens(articleId, 'default_user')
  
  // 调试日志已关闭以提升性能
  
  // 获取token notations功能
  const { getNotationContent, setNotationContent, clearNotationContent } = useTokenNotations()
  
  // 获取统一的notation缓存功能
  const {
    isLoading: isNotationLoading,
    error: notationError,
    isInitialized: isNotationInitialized,
    grammarNotations,
    getGrammarNotationsForSentence,
    getGrammarRuleById,
    hasGrammarNotation,
    vocabNotations,
    getVocabNotationsForSentence,
    getVocabExampleForToken,
    hasVocabNotation,
    refreshCache: refreshNotationCache,
    // 实时缓存更新函数
    addGrammarNotationToCache,
    addVocabNotationToCache,
    addGrammarRuleToCache,
    addVocabExampleToCache,
    // 创建功能（新API）
    createVocabNotation
  } = useNotationCache(articleId)
  
  // 调试日志已关闭以提升性能
  
  // Sample text for the ArticleViewer
  const sampleText = isUploadMode ? '' : 'Sample text for demo'

  const handleTokenSelect = async (tokenText, selectedSet, selectedTexts = [], context = null) => {
    console.log('🎯 [ArticleChatView] Token selection triggered:')
    console.log('  - Token text:', tokenText)
    console.log('  - Selected texts:', selectedTexts)
    console.log('  - Context:', context)
    console.log('  - Current hasSelectedSentence:', hasSelectedSentence)
    console.log('  - Current selectedSentence:', selectedSentence)
    
    // Token选择优先：总是清除句子选择
    if (hasSelectedSentence) {
      console.log('🧹 [ArticleChatView] Token selection takes priority - clearing sentence selection')
      setSelectedSentence(null)
      setHasSelectedSentence(false)
    }
    
    setSelectedTokens(selectedTexts)
    setQuotedText(selectedTexts.join(' '))
    setHasSelectedToken(selectedTexts.length > 0)
    setCurrentContext(context)  // 保存完整的上下文信息
    
    console.log('✅ [ArticleChatView] Token selection state updated:')
    console.log('  - hasSelectedToken:', selectedTexts.length > 0)
    console.log('  - quotedText:', selectedTexts.join(' '))
    
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
    } else if (selectedTexts.length === 0 && hasSelectedToken) {
      // 只在"之前有选择 → 现在变为0"时才清空后端，避免拖拽中间状态误触发
      console.log('🧹 [ArticleChatView] Clearing token selection and backend session token (was selected, now cleared)')
      try {
        const clearPayload = { token: null }
        console.log('📤 [ArticleChatView] Clearing token via updateContext:', clearPayload)
        await apiService.session.updateContext(clearPayload)
        console.log('✅ [ArticleChatView] Backend token cleared')
      } catch (error) {
        console.error('❌ [ArticleChatView] Failed to clear backend token:', error)
      }
    }
  }

  const handleClearQuote = () => {
    console.log('🧹 [ArticleChatView] Clearing all selections and quotes')
    setQuotedText('')
    setSelectedTokens([])
    setHasSelectedToken(false)
    setCurrentContext(null)  // 同时清除上下文
    setSelectedSentence(null)  // 清除句子选择
    setHasSelectedSentence(false)
    // 同步清空后端的当前 token 选择，避免状态残留
    try {
      const clearPayload = { token: null }
      console.log('📤 [ArticleChatView] Clearing backend token via updateContext:', clearPayload)
      apiService.session.updateContext(clearPayload)
    } catch (error) {
      console.error('❌ [ArticleChatView] Failed to clear backend token on clearQuote:', error)
    }
  }

  const handleSentenceSelect = async (sentenceIndex, sentenceText, sentenceData) => {
    console.log('📝 [ArticleChatView] Sentence selection triggered:')
    console.log('  - Sentence index:', sentenceIndex)
    console.log('  - Sentence text:', sentenceText)
    console.log('  - Sentence data:', sentenceData)
    console.log('  - Current hasSelectedToken:', hasSelectedToken)
    console.log('  - Current selectedTokens:', selectedTokens)
    
    if (sentenceIndex !== null && sentenceText) {
      // 如果当前有token选择，则清除token并继续设置句子，确保前后端一致
      if (hasSelectedToken) {
        console.log('🧹 [ArticleChatView] Clearing token selection to apply sentence selection')
        setSelectedTokens([])
        setHasSelectedToken(false)
        setCurrentContext(null)
      }
      
      // 选择句子（只有在没有token选择时）
      setSelectedSentence({
        index: sentenceIndex,
        text: sentenceText,
        data: sentenceData
      })
      setHasSelectedSentence(true)
      setQuotedText(sentenceText)
      
      console.log('✅ [ArticleChatView] Sentence selection state updated:')
      console.log('  - hasSelectedSentence:', true)
      console.log('  - quotedText:', sentenceText)
      
      // 发送句子上下文到后端session state（统一字段为后端期望的 snake_case）
      try {
        // 归一化句子数据，防止 camelCase / snake_case 混用导致会话态错乱
        const normalizedSentence = {
          text_id: sentenceData?.text_id ?? sentenceData?.textId ?? articleId,
          sentence_id: sentenceData?.sentence_id ?? sentenceData?.sentenceId ?? (typeof sentenceIndex === 'number' ? sentenceIndex + 1 : undefined),
          sentence_body: sentenceData?.sentence_body ?? sentenceData?.sentenceBody ?? sentenceText ?? sentenceData?.text ?? ''
        }
        // 无条件显式清空后端 token，避免任何历史残留导致错配
        const updatePayload = { sentence: normalizedSentence, token: null }
        
        console.log('📤 [ArticleChatView] Sending sentence context to backend...')
        console.log('🧭 [ArticleChatView] Normalized sentence:', normalizedSentence)
        console.log('📤 [ArticleChatView] Update payload:', updatePayload)
        const response = await apiService.session.updateContext(updatePayload)
        console.log('✅ [ArticleChatView] Session context updated:', response)
      } catch (error) {
        console.error('❌ [ArticleChatView] Failed to update session context:', error)
      }
    } else {
      // 清除句子选择
      setSelectedSentence(null)
      setHasSelectedSentence(false)
      setQuotedText('')
    }
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

  // 构建 NotationContext 的值
  // 🔧 添加 vocabNotations 和 grammarNotations 到依赖，确保缓存更新时 Context 值也更新
  const notationContextValue = useMemo(() => {
    console.log('🔄 [ArticleChatView] NotationContext 值更新:', {
      vocabNotationsCount: vocabNotations.length,
      grammarNotationsCount: grammarNotations.length,
      vocabNotations: vocabNotations,
      grammarNotations: grammarNotations
    })
    
    return {
      // Grammar 相关
      getGrammarNotationsForSentence,
      getGrammarRuleById,
      hasGrammarNotation,
      
      // Vocab 相关
      getVocabNotationsForSentence,
      getVocabExampleForToken,
      hasVocabNotation,
      
      // 兼容层（暂时保留用于向后兼容）
      isTokenAsked,
      getNotationContent,
      setNotationContent,
      
      // 🔧 添加缓存数据本身，确保缓存更新时 Context 值也更新
      vocabNotations,
      grammarNotations
    }
  }, [
    getGrammarNotationsForSentence,
    getGrammarRuleById,
    hasGrammarNotation,
    getVocabNotationsForSentence,
    getVocabExampleForToken,
    hasVocabNotation,
    isTokenAsked,
    getNotationContent,
    setNotationContent,
    vocabNotations,  // 🔧 添加依赖
    grammarNotations  // 🔧 添加依赖
  ])

  return (
    <ChatEventProvider>
      <NotationContext.Provider value={notationContextValue}>
        <SelectionProvider>
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

          {/* Main Content - allow overlays to extend beyond article view */}
          <div className="flex gap-8 flex-1 p-4 overflow-visible min-h-0">
            {isUploadMode ? (
              showUploadProgress ? (
                <UploadProgress onComplete={handleUploadComplete} />
              ) : (
                <UploadInterface onUploadStart={handleUploadStart} />
              )
            ) : (
              <ArticleCanvas>
                <ArticleViewer 
                  articleId={articleId} 
                  onTokenSelect={handleTokenSelect}
                  isTokenAsked={isTokenAsked}
                  markAsAsked={markAsAsked}
                  getNotationContent={getNotationContent}
                  setNotationContent={setNotationContent}
                  onSentenceSelect={handleSentenceSelect}
                  targetSentenceId={targetSentenceId}
                  onTargetSentenceScrolled={() => setTargetSentenceId(null)}
                />
              </ArticleCanvas>
            )}
          <ChatView 
            quotedText={quotedText}
            onClearQuote={handleClearQuote}
            disabled={isUploadMode && !uploadComplete}
            hasSelectedToken={hasSelectedToken}
            selectedTokenCount={selectedTokens.length || 1}
            selectionContext={currentContext}
            markAsAsked={markAsAsked}  // 保留作为备用（向后兼容）
            createVocabNotation={createVocabNotation}  // 新API（优先使用）
            hasSelectedSentence={hasSelectedSentence}
            selectedSentence={selectedSentence}
            refreshAskedTokens={refreshAskedTokens}
            refreshGrammarNotations={refreshNotationCache}
            articleId={articleId}
            // 实时缓存更新函数
            addGrammarNotationToCache={addGrammarNotationToCache}
            addVocabNotationToCache={addVocabNotationToCache}
            addGrammarRuleToCache={addGrammarRuleToCache}
            addVocabExampleToCache={addVocabExampleToCache}
          />
        </div>
      </div>
        </SelectionProvider>
      </NotationContext.Provider>
    </ChatEventProvider>
  )
} 



