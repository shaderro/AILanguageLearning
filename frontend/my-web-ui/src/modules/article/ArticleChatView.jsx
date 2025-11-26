import { useState, useEffect, useRef, useMemo } from 'react'
import { createPortal } from 'react-dom'
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
import { useUIText } from '../../i18n/useUIText'

export default function ArticleChatView({ articleId, onBack, isUploadMode = false, onUploadComplete }) {
  const t = useUIText()
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
  const [uploadedArticleId, setUploadedArticleId] = useState(null) // 🔧 保存上传完成的文章ID
  // 长度超限对话框状态（提升到父组件，避免子组件卸载时丢失）
  const [showLengthDialog, setShowLengthDialog] = useState(false)
  const [pendingContent, setPendingContent] = useState(null)
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
          sentence_body: sentenceData?.sentence_body ?? sentenceData?.sentenceBody ?? sentenceText ?? sentenceData?.text ?? '',
          sentence_difficulty_level: sentenceData?.sentence_difficulty_level ?? sentenceData?.sentenceDifficultyLevel ?? null,
          tokens: sentenceData?.tokens ?? [],
          word_tokens: sentenceData?.word_tokens ?? sentenceData?.wordTokens ?? null,
          language: sentenceData?.language ?? null,
          language_code: sentenceData?.language_code ?? sentenceData?.languageCode ?? null,
          is_non_whitespace: sentenceData?.is_non_whitespace ?? sentenceData?.isNonWhitespace ?? null
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

  const handleUploadStart = (show = true) => {
    setShowUploadProgress(show)
  }
  
  const handleLengthDialogClose = () => {
    setShowLengthDialog(false)
    setPendingContent(null)
  }
  
  const handleTruncateContent = async () => {
    if (!pendingContent || !pendingContent.content) {
      console.error('❌ [ArticleChatView] handleTruncateContent: pendingContent 或 content 为空')
      return
    }
    
    const MAX_LENGTH = 5000
    const MAX_LENGTH_DISPLAY = '5,000' // 用于显示，避免在 JSX 中计算
    // 留一些余量，避免 FormData 编码导致超出限制（约 0.3% 的余量）
    const SAFE_LENGTH = Math.floor(MAX_LENGTH * 0.997) // 49850 字符
    // 确保截取后的内容不超过限制（使用 slice 更安全）
    const originalLength = pendingContent.content.length
    // 使用 slice 截取，留一些余量避免编码问题
    const truncatedContent = pendingContent.content.slice(0, SAFE_LENGTH)
    const truncatedLength = truncatedContent.length
    
    console.log('✂️ [Frontend] 截取内容:')
    console.log('  - 原始长度:', originalLength)
    console.log('  - 截取后长度:', truncatedLength)
    console.log('  - MAX_LENGTH:', MAX_LENGTH)
    console.log('  - 截取后内容前50字符:', truncatedContent.substring(0, 50))
    console.log('  - 截取后内容后50字符:', truncatedContent.substring(Math.max(0, truncatedLength - 50)))
    
    // 验证截取后的长度
    if (truncatedLength > MAX_LENGTH) {
      console.error('❌ [Frontend] 截取后长度仍然超过限制！', truncatedLength, '>', MAX_LENGTH)
      alert(t('截取失败：内容长度仍然超过限制'))
      return
    }
    
    if (truncatedLength !== MAX_LENGTH && originalLength > MAX_LENGTH) {
      console.warn('⚠️ [Frontend] 截取后长度不等于 MAX_LENGTH，但应该等于', truncatedLength, 'vs', MAX_LENGTH)
    }
    
    handleLengthDialogClose()
    
    // 调用上传API上传截取后的内容
    try {
      setShowUploadProgress(true)
      console.log('📤 [Frontend] 准备上传截取后的内容，长度:', truncatedLength)
      // 再次确认长度
      if (truncatedContent.length !== truncatedLength) {
        console.error('❌ [Frontend] 内容长度不一致！', truncatedContent.length, 'vs', truncatedLength)
      }
      // 截取后的内容跳过长度检查
      const response = await apiService.uploadText(truncatedContent, pendingContent.title || 'Text Article', pendingContent.language, true)
      
      console.log('📥 [Frontend] 截取后上传响应:', response)
      
      // 检查响应格式（可能是 response.success 或 response.status === 'success'）
      if (response && (response.success || response.status === 'success')) {
        const responseData = response.data || response
        const articleId = responseData.article_id || responseData.text_id
        
        console.log('✅ [Frontend] 截取后上传成功，文章ID:', articleId)
        
        // 调用完成回调，传递文章ID
        handleUploadComplete(articleId)
      } else {
        console.error('❌ [Frontend] 上传响应格式错误:', response)
        setShowUploadProgress(false)
        alert(t('上传失败: 响应格式错误'))
      }
    } catch (error) {
      console.error('❌ [Frontend] 截取后上传失败:', error)
      setShowUploadProgress(false)
      const errorMessage = error.response?.data?.error || error.message || '未知错误'
      alert(t('上传失败: {error}').replace('{error}', errorMessage))
    }
  }

  const handleUploadComplete = (articleId = null) => {
    console.log('✅ [ArticleChatView] handleUploadComplete 被调用，articleId:', articleId)
    if (articleId) {
      // 🔧 如果有 articleId，保存它并让进度条完成动画后再跳转
      setUploadedArticleId(articleId)
      // 不立即调用 onUploadComplete，让进度条完成动画
      // 进度条会在动画完成后调用 onComplete 回调
    } else {
      // 如果没有 articleId，立即完成
      setUploadComplete(true)
      setShowUploadProgress(false)
      if (onUploadComplete) {
        onUploadComplete(articleId)
      }
    }
  }
  
  // 🔧 进度条完成后的回调
  const handleProgressComplete = (articleId = null) => {
    console.log('✅ [ArticleChatView] 进度条完成，准备跳转，articleId:', articleId)
    setUploadComplete(true)
    setShowUploadProgress(false)
    // 调用父组件的完成回调，传递文章ID
    if (onUploadComplete) {
      onUploadComplete(articleId || uploadedArticleId)
    }
  }

  // 构建 NotationContext 的值
  // 🔧 添加 vocabNotations 和 grammarNotations 到依赖，确保缓存更新时 Context 值也更新
  const notationContextValue = useMemo(() => {
    // 🔧 移除频繁的日志输出，减少控制台噪音
    // console.log('🔄 [ArticleChatView] NotationContext 值更新:', {
    //   vocabNotationsCount: vocabNotations.length,
    //   grammarNotationsCount: grammarNotations.length,
    //   vocabNotations: vocabNotations,
    //   grammarNotations: grammarNotations
    // })
    
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
    vocabNotations.length,  // 🔧 只依赖长度，避免数组引用变化导致不必要的重新渲染
    grammarNotations.length  // 🔧 只依赖长度，避免数组引用变化导致不必要的重新渲染
  ])

  // 🔧 错误边界：捕获渲染错误
  try {
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
                <UploadProgress onComplete={handleProgressComplete} articleId={uploadedArticleId} />
              ) : (
                <UploadInterface 
                  onUploadStart={handleUploadStart}
                  onLengthExceeded={(content) => {
                    console.log('📞 [ArticleChatView] onLengthExceeded 被调用，content:', {
                      type: content.type,
                      url: content.url,
                      title: content.title,
                      language: content.language,
                      contentLength: content.content?.length
                    })
                    try {
                      // 🔧 直接更新状态，不使用 setTimeout（避免时序问题）
                      setPendingContent(content)
                      setShowLengthDialog(true)
                      setShowUploadProgress(false)
                      console.log('✅ [ArticleChatView] 状态已更新，showLengthDialog: true, pendingContent:', !!content)
                    } catch (err) {
                      console.error('❌ [ArticleChatView] onLengthExceeded 执行失败:', err)
                      console.error('❌ [ArticleChatView] 错误堆栈:', err.stack)
                    }
                  }}
                  onUploadComplete={handleUploadComplete}
                />
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
      
      {/* 长度超限对话框（在父组件中渲染，避免子组件卸载时丢失） */}
      {showLengthDialog && pendingContent && (() => {
        try {
          console.log('🎨 [ArticleChatView] 渲染对话框，showLengthDialog:', showLengthDialog, 'pendingContent:', {
            type: pendingContent?.type,
            hasContent: !!pendingContent?.content,
            contentLength: pendingContent?.content?.length
          })
          return createPortal(
            <div 
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center" 
              style={{ zIndex: 99999, position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}
              onClick={(e) => {
                if (e.target === e.currentTarget) {
                  handleLengthDialogClose()
                }
              }}
            >
              <div 
                className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 className="text-xl font-semibold text-gray-800 mb-4">{t('文章长度超出限制')}</h3>
                <div className="mb-4">
                  <p className="text-gray-600 mb-2">
                    {t('文章长度为')} <span className="font-semibold text-red-600">{(pendingContent?.content?.length || 0).toLocaleString()}</span> {t('字符， 超过了最大限制')} <span className="font-semibold">5,000</span> {t('字符。')}
                  </p>
                  <p className="text-sm text-gray-500">
                    {t('如果选择自动截取，将只保留前 5,000 个字符。')}
                  </p>
                </div>
                <div className="flex gap-3 justify-end">
                  <button
                    onClick={handleLengthDialogClose}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    {t('重新上传')}
                  </button>
                  <button
                    onClick={handleTruncateContent}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    {t('自动截取前面部分')}
                  </button>
                </div>
              </div>
            </div>,
            document.body
          )
        } catch (err) {
          console.error('❌ [ArticleChatView] 对话框渲染失败:', err)
          console.error('❌ [ArticleChatView] 错误堆栈:', err.stack)
          return null
        }
      })()}
    </SelectionProvider>
    </NotationContext.Provider>
    </ChatEventProvider>
    )
  } catch (err) {
    console.error('❌ [ArticleChatView] 渲染错误:', err)
    console.error('❌ [ArticleChatView] 错误堆栈:', err.stack)
    return (
      <div className="h-full flex flex-col items-center justify-center p-8">
        <div className="text-red-600 text-lg font-semibold mb-4">页面渲染出错</div>
        <div className="text-gray-600 mb-4">{String(err.message || err)}</div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          刷新页面
        </button>
      </div>
    )
  }
}



