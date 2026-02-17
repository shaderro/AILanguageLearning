import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { createPortal } from 'react-dom'
import ArticleViewer from './components/ArticleViewer'
import UploadInterface from './components/UploadInterface'
import UploadProgress from './components/UploadProgress'
import ChatView from './components/ChatView'
import { ChatEventProvider } from './contexts/ChatEventContext'
import { NotationContext } from './contexts/NotationContext'
import { SelectionProvider } from './selection/SelectionContext'
import { useSelection } from './selection/hooks/useSelection'
import { TranslationDebugProvider } from '../../contexts/TranslationDebugContext'
import TranslationDebugPanel from '../../components/TranslationDebugPanel'
import { useChatEvent } from './contexts/ChatEventContext'
import { useTranslationDebug } from '../../contexts/TranslationDebugContext'
import { useUser } from '../../contexts/UserContext'
import { isTokenInsufficient } from '../../utils/tokenUtils'
import authService from '../auth/services/authService'
import { useAskedTokens } from './hooks/useAskedTokens'
import { useTokenNotations } from './hooks/useTokenNotations'
import { useNotationCache } from './hooks/useNotationCache'
import { apiService } from '../../services/api'
import { useUIText } from '../../i18n/useUIText'
import { colors } from '../../design-tokens'
import VocabNotationDebugPanel from './components/VocabNotationDebugPanel'

function ArticleCanvas({ children, onClearQuote }) {
  const { clearSelection } = useSelection()
  return (
    <div className="flex-1 min-h-0 flex flex-col" onClick={(e) => {
      console.log('🖱️ [ArticleCanvas] onClick 被触发', {
        target: e.target?.tagName,
        currentTarget: e.currentTarget?.tagName,
        targetClass: e.target?.className,
        isTokenSpan: e.target?.closest('[data-token-id]') !== null
      })
      // 🔧 如果点击的是 token，不清除选择（让 TokenSpan 的 onClick 处理）
      if (e.target?.closest('[data-token-id]') !== null) {
        console.log('⏭️ [ArticleCanvas] 点击的是 token，跳过清除选择')
        return
      }
      // 🔧 如果点击的是句子容器，不清除选择（让 SentenceContainer 的 onClick 处理）
      // 检查 data-sentence-id 或 data-sentence-index 属性
      if (e.target?.closest('[data-sentence-id]') !== null || 
          e.target?.closest('[data-sentence-index]') !== null ||
          e.target?.closest('[data-sentence]') !== null) {
        console.log('⏭️ [ArticleCanvas] 点击的是句子，跳过清除选择')
        return
      }
      console.log('🧹 [ArticleCanvas] 清除选择和引用')
      clearSelection()
      // 🔧 当点击空白区域时，也清除引用
      if (onClearQuote && typeof onClearQuote === 'function') {
        onClearQuote()
      }
    }}>
      {children}
    </div>
  )
}

export default function ArticleChatView({ articleId, onBack, isUploadMode = false, onUploadComplete }) {
  const t = useUIText()
  // 🔧 从 URL 参数读取 sentenceId（用于自动滚动和高亮）
  const getSentenceIdFromURL = () => {
    const params = new URLSearchParams(window.location.search)
    const sentenceId = params.get('sentenceId')
    return sentenceId ? parseInt(sentenceId) : null
  }
  const [targetSentenceId, setTargetSentenceId] = useState(getSentenceIdFromURL())
  
  // 🔧 使用 useCallback 包装回调函数，避免 ArticleViewer 重新挂载
  const handleTargetSentenceScrolled = useCallback(() => {
    setTargetSentenceId(null)
  }, [])
  
  // 空白处清空选择逻辑已移至 ArticleCanvas（在 SelectionProvider 内部使用 useSelection）
  const [selectedTokens, setSelectedTokens] = useState([])
  const [quotedText, setQuotedText] = useState('')
  const [showUploadProgress, setShowUploadProgress] = useState(false)
  const [uploadComplete, setUploadComplete] = useState(false)
  const [uploadedArticleId, setUploadedArticleId] = useState(null) // 🔧 保存上传完成的文章ID
  const [uploadedArticleLanguage, setUploadedArticleLanguage] = useState(null) // 🔧 保存上传完成的文章语言（用于覆盖上边栏语言）
  // 长度超限对话框状态（提升到父组件，避免子组件卸载时丢失）
  const [showLengthDialog, setShowLengthDialog] = useState(false)
  const [pendingContent, setPendingContent] = useState(null)
  const [hasSelectedToken, setHasSelectedToken] = useState(false)
  const [currentContext, setCurrentContext] = useState(null)  // 新增：保存完整的选择上下文
  const [selectedSentence, setSelectedSentence] = useState(null)  // 新增：保存选中的句子
  const [hasSelectedSentence, setHasSelectedSentence] = useState(false)  // 新增：是否有选中的句子
  const [autoTranslationEnabled, setAutoTranslationEnabled] = useState(false)  // 🔧 自动翻译开关状态

  // 🔧 修复：移除在这里设置全局 window.chatViewMessagesRef 的逻辑
  // ChatView 组件会在 articleId 改变时自动从后端加载对应文章的历史记录
  
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

  // 🔧 新增：跟踪是否正在处理，防止在处理过程中更新 session state
  // 必须在 handleTokenSelect 之前定义，因为 handleTokenSelect 的依赖项中使用了 isProcessing
  const [isProcessing, setIsProcessing] = useState(false)

  const handleTokenSelect = useCallback(async (tokenText, selectedSet, selectedTexts = [], context = null) => {
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
    
    // 🔧 Send selection context to backend session state
    // 🔧 关键：如果正在处理，不更新 session state，避免覆盖正在使用的句子
    if (context && context.sentence && selectedTexts.length > 0) {
      if (isProcessing) {
        console.log('⚠️ [ArticleChatView] 正在处理中，跳过更新 session state（token选择），避免覆盖正在使用的句子')
        return
      }
      
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
  }, [articleId, hasSelectedToken, isProcessing, hasSelectedSentence, selectedSentence])
  
  const handleClearQuote = useCallback(() => {
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
  }, []) // 没有依赖项，因为只是清除状态

  const handleSentenceSelect = useCallback(async (sentenceIndex, sentenceText, sentenceData) => {
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
      
      // 🔧 关键修复：更新 currentContext，确保 ChatView 能正确检测到句子选择
      // 归一化句子数据，防止 camelCase / snake_case 混用
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
      
      // 设置 selectionContext，只包含句子信息，不包含 token
      setCurrentContext({
        sentence: normalizedSentence,
        tokens: [], // 句子选择时，没有 token
        tokenIndices: [],
        selectedTexts: []
      })
      
      console.log('✅ [ArticleChatView] Sentence selection state updated:')
      console.log('  - hasSelectedSentence:', true)
      console.log('  - quotedText:', sentenceText)
      console.log('  - currentContext:', {
        sentence: normalizedSentence,
        tokens: [],
        tokenIndices: [],
        selectedTexts: []
      })
      
      // 🔧 发送句子上下文到后端session state（统一字段为后端期望的 snake_case）
      // 🔧 关键：如果正在处理，不更新 session state，避免覆盖正在使用的句子
      if (isProcessing) {
        console.log('⚠️ [ArticleChatView] 正在处理中，跳过更新 session state，避免覆盖正在使用的句子')
        return
      }
      
      try {
        // 使用上面已经归一化的句子数据
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
  }, [articleId, hasSelectedToken, selectedTokens, isProcessing])

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
        handleUploadComplete(articleId, pendingContent?.language)
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

  const handleUploadComplete = (articleId = null, uploadLanguage = null) => {
    console.log('✅ [ArticleChatView] handleUploadComplete 被调用，articleId:', articleId, 'uploadLanguage:', uploadLanguage)
    if (articleId) {
      // 🔧 如果有 articleId，保存它并让进度条完成动画后再跳转
      setUploadedArticleId(articleId)
      setUploadedArticleLanguage(uploadLanguage || null)
      // 🔧 确保进度条可见，否则不会触发跳转回调（某些路径下 onUploadStart 可能未开启进度条）
      setShowUploadProgress(true)
      // 不立即调用 onUploadComplete，让进度条完成动画
      // 进度条会在动画完成后调用 onComplete 回调
    } else {
      // 如果没有 articleId，立即完成
      setUploadComplete(true)
      setShowUploadProgress(false)
      if (onUploadComplete) {
        onUploadComplete(articleId, uploadLanguage)
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
      onUploadComplete(articleId || uploadedArticleId, uploadedArticleLanguage)
    }
  }

  // 🔧 全局 tooltip 状态管理：当前激活的 vocab notation tooltip
  // 格式：{ articleId, sentenceId, tokenId } 或 null
  // 目的：即使 TokenSpan 重挂载，tooltip 状态也不会丢失
  const [activeVocabNotation, setActiveVocabNotation] = useState(null)

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
      
      // 🔧 全局 tooltip 状态管理
      activeVocabNotation,
      setActiveVocabNotation,
      
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
    activeVocabNotation,  // 🔧 添加 activeVocabNotation 到依赖
    isTokenAsked,
    getNotationContent,
    setNotationContent,
    vocabNotations,  // 🔧 依赖整个数组，确保内容变化时也能触发更新
    grammarNotations  // 🔧 依赖整个数组，确保内容变化时也能触发更新
  ])

  // 🔧 新增：处理 AI 详细解释请求（内部组件，可以使用 useChatEvent）
  const ArticleChatViewInner = () => {
    const { sendMessageToChat } = useChatEvent()
    const { token: userToken } = useUser()
    const [userInfo, setUserInfo] = useState(null)
    
    // 🔧 获取用户信息
    useEffect(() => {
      const fetchUserInfo = async () => {
        if (!userToken) {
          setUserInfo(null)
          return
        }
        
        try {
          const info = await authService.getCurrentUser(userToken)
          setUserInfo(info)
        } catch (err) {
          console.error('获取用户信息失败:', err)
          setUserInfo(null)
        }
      }
      
      fetchUserInfo()
      // 定期刷新用户信息（每30秒）
      const interval = setInterval(fetchUserInfo, 30000)
      return () => clearInterval(interval)
    }, [userToken])
    
    const handleAskAI = useCallback(async (token, sentenceIndex) => {
      if (!token || sentenceIndex == null) {
        return
      }
      
      if (isProcessing) {
        return
      }
      
      // 🔧 检查token是否不足（只在当前没有main assistant流程时判断）
      if (userInfo) {
        const insufficient = isTokenInsufficient(userInfo.token_balance, userInfo.role)
        if (insufficient) {
          console.log(`⚠️ [ArticleChatView] Token不足，无法使用AI详细解释功能`)
          return
        }
      } else if (userToken) {
        // 如果userInfo还未加载，尝试获取
        try {
          const info = await authService.getCurrentUser(userToken)
          setUserInfo(info)
          const insufficient = isTokenInsufficient(info?.token_balance, info?.role)
          if (insufficient) {
            console.log(`⚠️ [ArticleChatView] Token不足，无法使用AI详细解释功能`)
            return
          }
        } catch (err) {
          console.error('获取用户信息失败:', err)
        }
      }
      
      try {
        // 1. 获取文章数据以构建 context
        const articleData = await apiService.getArticleById(articleId)
        const sentences = articleData?.data?.sentences || []
        const sentence = sentences[sentenceIndex]
        
        if (!sentence) {
          return
        }
        
        // 2. 构建 context
        const tokenText = typeof token === 'string' ? token : (token?.token_body ?? token?.token ?? '')
        
        // 从句子中找到对应的 token 对象（确保有正确的字段）
        const sentenceTokens = sentence.tokens || []
        const tokenIndex = sentenceTokens.findIndex(t => {
          const tId = typeof t === 'string' ? t : (t?.token_body ?? t?.token ?? '')
          return tId === tokenText
        })
        
        if (tokenIndex === -1) {
          return
        }
        
        // 获取 token 对象，确保有正确的字段
        const tokenObj = typeof sentenceTokens[tokenIndex] === 'string' 
          ? { token_body: sentenceTokens[tokenIndex], sentence_token_id: tokenIndex + 1 }
          : sentenceTokens[tokenIndex]
        
        // 确保 token 对象有必要的字段
        if (!tokenObj.token_body) {
          tokenObj.token_body = tokenText
        }
        if (!tokenObj.sentence_token_id && tokenIndex !== -1) {
          tokenObj.sentence_token_id = tokenIndex + 1
        }
        
        const context = {
          sentence: {
            text_id: articleId,
            sentence_id: sentenceIndex + 1,
            sentence_body: sentenceTokens.map(t => typeof t === 'string' ? t : t.token_body).join(' ') || '',
            tokens: sentenceTokens
          },
          tokens: [tokenObj],
          tokenIndices: [tokenIndex],
          selectedTexts: [tokenText]
        }
        
        // 3. 选择 token（这会更新 session state）
        await handleTokenSelect(tokenText, new Set([tokenText]), [tokenText], context)
        
        // 4. 等待 session state 更新完成（给更多时间确保后端已更新）
        await new Promise(resolve => setTimeout(resolve, 300))
        
        // 5. 更新 currentContext 以确保 ChatView 使用最新的 context
        setCurrentContext(context)
        
        // 6. 发送消息"这个词是什么意思?"，同时传递 context
        sendMessageToChat('这个词是什么意思?', tokenText, context)
      } catch (error) {
        // 静默处理错误
      }
    }, [articleId, isProcessing, handleTokenSelect, setCurrentContext, sendMessageToChat, userInfo, userToken])
    
    // 🔧 包装handleAskAI，传递token不足状态给TokenSpan
    const wrappedHandleAskAI = useCallback(async (token, sentenceIndex) => {
      // 检查token是否不足
      if (userInfo) {
        const insufficient = isTokenInsufficient(userInfo.token_balance, userInfo.role)
        if (insufficient) {
          return
        }
      }
      return handleAskAI(token, sentenceIndex)
    }, [handleAskAI, userInfo])
    
    // 🔧 计算token是否不足（用于禁用AI详细解释按钮）
    const isTokenInsufficientForAI = useMemo(() => {
      if (!userInfo) return false
      return isTokenInsufficient(userInfo.token_balance, userInfo.role)
    }, [userInfo])
    
    return (
      <>
        {/* 临时 Debug：vocab notation hover / tooltip / example 加载链路（可复制） */}
        <VocabNotationDebugPanel />
        <div className="h-full flex flex-col">
          {/* Main Content - allow overlays to extend beyond article view */}
          <div className={`flex gap-8 flex-1 p-4 overflow-hidden min-h-0 ${isUploadMode ? 'justify-center' : ''}`}>
            {isUploadMode ? (
              <div className="w-1/2 flex justify-center">
                {showUploadProgress ? (
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
                    onBack={onBack}
                  />
                )}
              </div>
            ) : (
              <div className="flex-1 flex flex-col min-h-0 relative">
                {/* Buttons above article view */}
                <div className="flex items-center justify-between mb-2 px-1">
                  {/* Back Button */}
                  <button
                    onClick={onBack}
                    className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-900 transition-colors bg-white rounded-md shadow-sm border border-gray-200 hover:bg-gray-50"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    <span>{t('Back to Articles')}</span>
                  </button>
                  {/* Right side buttons container */}
                  <div className="flex items-center gap-3">
                    {/* Auto Translation Toggle Switch */}
                    <label 
                      className="flex items-center gap-2 cursor-pointer"
                      onClick={(e) => {
                        e.stopPropagation()
                      }}
                      onMouseDown={(e) => {
                        e.stopPropagation()
                      }}
                    >
                      <span className="text-sm font-medium text-gray-700">{t('自动翻译')}</span>
                      <div className="relative inline-flex items-center">
                        <input
                          type="checkbox"
                          checked={autoTranslationEnabled}
                          onChange={(e) => {
                            e.stopPropagation()
                            setAutoTranslationEnabled(e.target.checked)
                          }}
                          className="sr-only"
                        />
                        <div
                          className={`w-11 h-6 rounded-full transition-colors duration-200 ease-in-out ${
                            autoTranslationEnabled ? '' : 'bg-gray-300'
                          }`}
                          style={autoTranslationEnabled ? {
                            backgroundColor: colors.primary[500]
                          } : {}}
                        >
                          <div
                            className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-200 ease-in-out ${
                              autoTranslationEnabled ? 'translate-x-5' : 'translate-x-0'
                            }`}
                          />
                        </div>
                      </div>
                    </label>
                    {/* Read Aloud Button - will be rendered by ArticleViewer */}
                    <div 
                      id="read-aloud-button-container" 
                      key="read-aloud-button-container"
                      className="flex items-center"
                      style={{ minWidth: '120px', minHeight: '40px' }}
                    ></div>
                  </div>
                </div>
                {/* Article View */}
                <ArticleCanvas onClearQuote={handleClearQuote}>
                  <ArticleViewer 
                    key={`article-viewer-${articleId}`}
                    articleId={articleId} 
                    onTokenSelect={handleTokenSelect}
                    isTokenAsked={isTokenAsked}
                    markAsAsked={markAsAsked}
                    getNotationContent={getNotationContent}
                    setNotationContent={setNotationContent}
                    onSentenceSelect={handleSentenceSelect}
                    targetSentenceId={targetSentenceId}
                    onTargetSentenceScrolled={handleTargetSentenceScrolled}
                    onAskAI={handleAskAI}
                    autoTranslationEnabled={autoTranslationEnabled}
                  />
                </ArticleCanvas>
              </div>
            )}
            {/* 上传模式下不显示 ChatView */}
            {!isUploadMode && (
              <ChatView 
                key={`chatview-${articleId}`}  // 🔧 添加稳定的 key，防止不必要的重新挂载
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
                // 🔧 传递 isProcessing 状态和更新函数
                isProcessing={isProcessing}
                onProcessingChange={setIsProcessing}
              />
            )}
          </div>
        </div>
        
        {/* 翻译调试面板 - 已隐藏 */}
        {/* <TranslationDebugPanel /> */}
        
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
      </>
    )
  }

  // 🔧 错误边界：捕获渲染错误
  try {
    return (
      <TranslationDebugProvider>
        <ChatEventProvider>
          <NotationContext.Provider value={notationContextValue}>
            <SelectionProvider>
              <ArticleChatViewInner />
            </SelectionProvider>
          </NotationContext.Provider>
        </ChatEventProvider>
      </TranslationDebugProvider>
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



