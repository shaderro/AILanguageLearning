import ArticleList from './components/ArticleList'
import { useArticles } from '../../hooks/useApi'
import { useUser } from '../../contexts/UserContext'
import { useLanguage, languageNameToCode } from '../../contexts/LanguageContext'
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { apiService } from '../../services/api'
import { useUIText } from '../../i18n/useUIText'
import {
  ensureArticlePreviewCacheLoaded,
  getCachedArticlePreview,
  hydrateArticlePreviewCache,
  fetchArticlePreview,
} from '../../utils/articlePreviewCache'

const ArticleSelection = ({ onArticleSelect, onUploadNew }) => {
  const { userId, isGuest } = useUser()
  const { selectedLanguage } = useLanguage()
  const queryClient = useQueryClient()
  const t = useUIText()
  
  // 编辑和删除相关状态
  const [editingArticle, setEditingArticle] = useState(null)
  const [editTitle, setEditTitle] = useState('')
  const [deletingArticle, setDeletingArticle] = useState(null)
  const [pendingDeletionIds, setPendingDeletionIds] = useState(() => new Set())
  const [isProcessing, setIsProcessing] = useState(false)
  
  // 🔧 调试日志
  useEffect(() => {
    console.log('📋 [ArticleSelection] 组件渲染，userId:', userId, 'isGuest:', isGuest, 'selectedLanguage:', selectedLanguage)
  }, [userId, isGuest, selectedLanguage])
  
  // 使用API获取文章数据 - 传入 userId、isGuest 和 language（后端过滤或本地过滤）
  const { data, isLoading, isError, error, refetch } = useArticles(userId, selectedLanguage, isGuest)
  
  // 🔧 调试日志：记录查询状态
  useEffect(() => {
    console.log('📋 [ArticleSelection] 查询状态:', { 
      isLoading, 
      isError, 
      hasData: !!data, 
      dataType: typeof data,
      userId,
      isGuest,
      selectedLanguage
    })
    if (isError) {
      console.error('❌ [ArticleSelection] 查询错误:', error)
    }
  }, [isLoading, isError, error, data, userId, isGuest, selectedLanguage])
  
  // 🔧 当 userId/selectedLanguage 变化时，自动刷新文章列表
  useEffect(() => {
    // 只在 userId 不为 null 时才刷新（游客模式 userId 也是数字）
    if (userId !== null && !isLoading) {
      console.log('🔄 [ArticleSelection] userId 或 selectedLanguage 变化，刷新文章列表')
      refetch()
    }
  }, [userId, selectedLanguage, refetch, isLoading])
  
  // 处理游客模式和登录模式的数据格式
  let summaries = []
  console.log('📋 [ArticleSelection] 原始 data:', data)
  
  if (isGuest) {
    // 游客模式：data.data 是文章数组
    summaries = Array.isArray(data?.data) ? data.data : []
    console.log('📋 [ArticleSelection] 游客模式，文章数量:', summaries.length)
  } else {
    // 登录模式：响应拦截器返回格式可能是：
    // 1. {data: [...], count: ...} - 来自 api.js 的映射（这是当前的情况）
    // 2. {texts: [...], count: ...} - 原始后端格式
    // 3. [...] - 直接是数组
    // 4. {data: {texts: [...], count: ...}} - 嵌套格式
    
    // 🔧 首先检查 data 本身是否是数组
    if (Array.isArray(data)) {
      summaries = data
      console.log('📋 [ArticleSelection] data 是数组，文章数量:', summaries.length)
    } else if (data && Array.isArray(data.data)) {
      // 格式：{data: [...], count: ...} - 这是响应拦截器返回的格式
      summaries = data.data
      console.log('📋 [ArticleSelection] 从 data.data 提取，文章数量:', summaries.length)
    } else if (data?.data && Array.isArray(data.data.texts)) {
      // 格式：{data: {texts: [...], count: ...}}
      summaries = data.data.texts
      console.log('📋 [ArticleSelection] 从 data.data.texts 提取，文章数量:', summaries.length)
    } else if (data && Array.isArray(data.texts)) {
      // 格式：{texts: [...], count: ...}
      summaries = data.texts
      console.log('📋 [ArticleSelection] 从 data.texts 提取，文章数量:', summaries.length)
    } else {
      summaries = []
      console.warn('⚠️ [ArticleSelection] 无法提取文章数据，data 格式:', data)
    }
  }
  
  const fallbackPreview = t('暂无摘要')

  ensureArticlePreviewCacheLoaded()

  // 将后端摘要映射为列表卡片需要的结构
  // 注意：language过滤已经在API层面完成（登录模式）或本地完成（游客模式），这里只需要映射数据
  console.log('📋 [ArticleSelection] summaries 数量:', summaries.length, '前3条:', summaries.slice(0, 3))
  const mappedArticles = summaries.map((s) => {
    // 处理游客模式和登录模式的数据格式
    const textId = s.text_id || s.article_id || s.id
    const textTitle = s.text_title || s.title || `Article ${textId}`
    const totalSentences = s.total_sentences || s.sentence_count || 0
    const totalTokens = s.total_tokens || s.wordCount || s.token_count || 0
    const language = s.language || null
    const processingStatus = s.processing_status || 'completed' // 处理状态：processing/completed/failed
    const noteCount =
      s.note_count ?? s.notes_count ?? s.total_notes ?? s.grammar_notes_count ?? s.vocab_notes_count ?? 0
    const previewText =
      s.preview_text ||
      s.preview ||
      s.summary ||
      s.description ||
      s.snippet ||
      s.first_sentence ||
      fallbackPreview
    const difficulty = s.difficulty || null
    
    return {
      id: textId,
      title: textTitle,
      description: processingStatus === 'processing' 
        ? t('处理中...') 
        : `Sentences: ${totalSentences} • Tokens: ${totalTokens}`,
      language: language, // 从后端获取语言字段，null表示未设置
      difficulty,
      wordCount: totalTokens,
      noteCount,
      preview: previewText,
      estimatedTime: `${Math.max(1, Math.ceil((totalSentences || 1) / 5))} min`,
      category: 'Article',
      tags: [],
      processingStatus: processingStatus // 添加处理状态
    }
  })

  // 文章过滤：后端应该已经过滤，但添加前端备用过滤以确保正确性
  const filteredArticles = useMemo(() => {
    if (!selectedLanguage || selectedLanguage === 'all') {
      return mappedArticles
    }
    
    // 前端备用过滤：如果后端过滤不生效，这里会再次过滤
    // 支持多种语言格式匹配（中文、英文、代码等）
    const languageVariants = [
      selectedLanguage, // 原始值（如 "英文"）
      languageNameToCode(selectedLanguage), // 语言代码（如 "en"）
      // 可能的其他格式
      selectedLanguage === '中文' ? 'Chinese' : null,
      selectedLanguage === '英文' ? 'English' : null,
      selectedLanguage === '英语' ? 'English' : null,
      selectedLanguage === '德文' ? 'German' : null,
      selectedLanguage === '德语' ? 'German' : null,
      selectedLanguage === '西班牙语' ? 'Spanish' : null,
      selectedLanguage === '法语' ? 'French' : null,
      selectedLanguage === '日语' ? 'Japanese' : null,
      selectedLanguage === '韩语' ? 'Korean' : null,
      selectedLanguage === '阿拉伯语' ? 'Arabic' : null,
      selectedLanguage === '俄语' ? 'Russian' : null,
    ].filter(Boolean)
    
    // 调试：检查文章语言分布
    const languageDistribution = {}
    mappedArticles.forEach(article => {
      const lang = article.language || '(null)'
      languageDistribution[lang] = (languageDistribution[lang] || 0) + 1
    })
    console.log(`🔍 [ArticleSelection] 文章语言分布:`, languageDistribution, `筛选语言: ${selectedLanguage}`)
    
    const filtered = mappedArticles.filter(article => {
      if (!article.language) {
        // 如果文章没有语言信息，根据配置决定是否显示
        // 默认不显示没有语言信息的文章
        return false
      }
      
      // 检查文章语言是否匹配任何变体
      const articleLang = String(article.language).toLowerCase()
      const matches = languageVariants.some(variant => 
        articleLang === String(variant).toLowerCase()
      )
      
      return matches
    })
    
    // 如果过滤后数量与原始数量相同，说明后端可能已经过滤了
    // 如果过滤后数量不同，说明后端过滤可能不生效，使用前端过滤结果
    if (filtered.length !== mappedArticles.length) {
      console.log(`🔍 [ArticleSelection] 前端过滤生效: ${mappedArticles.length} -> ${filtered.length} (语言: ${selectedLanguage})`)
    } else if (mappedArticles.length > 0) {
      console.log(`⚠️ [ArticleSelection] 前端过滤未生效: 所有 ${mappedArticles.length} 篇文章都匹配语言 ${selectedLanguage}`)
    }
    
    return filtered
  }, [mappedArticles, selectedLanguage])

  const [previewOverrides, setPreviewOverrides] = useState(() => {
    const initial = {}
    mappedArticles.forEach((article) => {
      const cachedPreview = getCachedArticlePreview(article.id)
      if (cachedPreview) {
        initial[article.id] = cachedPreview
      }
    })
    return initial
  })

  useEffect(() => {
    hydrateArticlePreviewCache(
      mappedArticles
        .filter((article) => article.preview && article.preview !== fallbackPreview)
        .map((article) => ({ id: article.id, preview: article.preview })),
    )

    setPreviewOverrides((prev) => {
      const next = { ...prev }
      let changed = false

      mappedArticles.forEach((article) => {
        const cachedPreview = getCachedArticlePreview(article.id)
        if (cachedPreview && next[article.id] !== cachedPreview) {
          next[article.id] = cachedPreview
          changed = true
        }
      })

      return changed ? next : prev
    })
  }, [mappedArticles, fallbackPreview])

  useEffect(() => {
    let cancelled = false
    const CONCURRENCY = 2
    let timeoutId = null
    const fetchMissingPreviews = async () => {
      const pending = filteredArticles.filter(
        (article) =>
          (!article.preview || article.preview === fallbackPreview) &&
          !getCachedArticlePreview(article.id),
      )
      if (pending.length === 0) {
        return
      }

      for (let i = 0; i < pending.length && !cancelled; i += CONCURRENCY) {
        const batch = pending.slice(i, i + CONCURRENCY)
        await Promise.all(
          batch.map(async (article) => {
            try {
              const firstSentence = await fetchArticlePreview(article.id)
              if (firstSentence && !cancelled) {
                setPreviewOverrides((prev) => {
                  if (prev[article.id] === firstSentence) {
                    return prev
                  }
                  return {
                    ...prev,
                    [article.id]: firstSentence,
                  }
                })
              }
            } catch (err) {
              console.warn('⚠️ [ArticleSelection] 获取文章首句失败:', article.id, err)
            }
          }),
        )
      }
    }

    timeoutId = window.setTimeout(fetchMissingPreviews, 250)

    return () => {
      cancelled = true
      if (timeoutId) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [filteredArticles, fallbackPreview])

  const enrichedArticles = useMemo(
    () =>
      filteredArticles.map((article) => ({
        ...article,
        preview: previewOverrides[article.id] ?? getCachedArticlePreview(article.id) ?? article.preview,
      })),
    [filteredArticles, previewOverrides],
  )
  const visibleArticles = useMemo(
    () => enrichedArticles.filter((article) => !pendingDeletionIds.has(article.id)),
    [enrichedArticles, pendingDeletionIds],
  )
  console.log('📋 [ArticleSelection] mappedArticles 数量:', mappedArticles.length, 'filteredArticles 数量:', filteredArticles.length)

  const handleArticleSelect = (articleId) => {
    console.log('Article selected:', articleId)
    onArticleSelect(articleId)
  }

  const handleUploadNew = () => {
    console.log('Upload new article clicked')
    if (onUploadNew) {
      onUploadNew()
    }
  }
  
  // 处理编辑文章
  const handleEdit = (articleId, currentTitle) => {
    setEditingArticle(articleId)
    setEditTitle(currentTitle)
  }
  
  // 保存编辑
  const handleSaveEdit = async (articleId = editingArticle) => {
    const nextTitle = editTitle.trim()
    if (!articleId || !nextTitle) {
      handleCancelEdit()
      return
    }
    
    setIsProcessing(true)
    try {
      console.log('🔄 [ArticleSelection] 开始更新文章:', articleId, '新名称:', nextTitle)
      const response = await apiService.updateArticle(articleId, { text_title: nextTitle })
      console.log('✅ [ArticleSelection] 文章名称已更新，响应:', response)
      // 刷新文章列表
      queryClient.invalidateQueries({ queryKey: ['articles'] })
      await refetch()
      console.log('✅ [ArticleSelection] 文章列表已刷新')
      setEditingArticle(null)
      setEditTitle('')
    } catch (error) {
      console.error('❌ [ArticleSelection] 更新文章名称失败:', error)
      console.error('❌ [ArticleSelection] 错误详情:', error.response?.data || error.message)
      alert(t('更新失败: {error}').replace('{error}', error.response?.data?.detail || error.message || '未知错误'))
    } finally {
      setIsProcessing(false)
    }
  }
  
  // 取消编辑
  const handleCancelEdit = () => {
    setEditingArticle(null)
    setEditTitle('')
  }
  
  // 处理删除文章
  const handleDelete = (articleId, articleTitle) => {
    setDeletingArticle({ id: articleId, title: articleTitle })
  }
  
  // 确认删除
  const handleConfirmDelete = async () => {
    if (!deletingArticle) {
      return
    }

    const articleToDelete = deletingArticle
    // 先更新UI：关闭弹窗并立刻从列表隐藏该文章，再异步删除后端数据
    setDeletingArticle(null)
    setPendingDeletionIds((prev) => {
      const next = new Set(prev)
      next.add(articleToDelete.id)
      return next
    })

    try {
      await apiService.deleteArticle(articleToDelete.id)
      console.log('✅ [ArticleSelection] 文章已删除')
      // 刷新文章列表
      queryClient.invalidateQueries({ queryKey: ['articles'] })
      refetch()
    } catch (error) {
      console.error('❌ [ArticleSelection] 删除文章失败:', error)
      // 删除失败时回滚UI，恢复该文章
      setPendingDeletionIds((prev) => {
        const next = new Set(prev)
        next.delete(articleToDelete.id)
        return next
      })
      alert(t('删除失败: {error}').replace('{error}', error.response?.data?.detail || error.message || '未知错误'))
    } finally {
      // 删除请求完成后，清理本地 pending 状态（成功时后端刷新后不会再出现）
      setPendingDeletionIds((prev) => {
        if (!prev.has(articleToDelete.id)) {
          return prev
        }
        const next = new Set(prev)
        next.delete(articleToDelete.id)
        return next
      })
    }
  }
  
  // 取消删除
  const handleCancelDelete = () => {
    setDeletingArticle(null)
  }

  return (
    <div className="bg-white">
      {/* Main Content */}
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
            <div className="text-center mb-4">
              <span className="block text-primary-600 font-medium">
                {t('当前筛选：')}{t(selectedLanguage) || selectedLanguage}
              </span>
            </div>

            {/* Loading / Error */}
            {isLoading && (
              <div className="text-center text-gray-600 py-8">{t('Loading articles...')}</div>
            )}
            {isError && (
              <div className="text-center text-red-600 py-8">
                <p>{t('Error loading articles:')} {String(error)}</p>
                <button 
                  onClick={() => refetch()} 
                  className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  {t('重试')}
                </button>
              </div>
            )}

            {/* 🔧 确保即使没有数据也显示内容，避免空白页 */}
            {!isLoading && !isError && (
              <>
                {/* Article Count */}
                <div className="mb-6">
                  <p className="text-gray-600">
                    {t('共显示 {count} 篇文章（{language}）')
                      .replace('{count}', visibleArticles.length)
                      .replace('{language}', t(selectedLanguage) || selectedLanguage)
                    }
                  </p>
                </div>

                {/* Article List */}
                {visibleArticles.length > 0 ? (
                  <ArticleList 
                    articles={visibleArticles}
                    onArticleSelect={handleArticleSelect}
                    onArticleEdit={handleEdit}
                    editingArticleId={editingArticle}
                    editingTitle={editTitle}
                    onEditingTitleChange={setEditTitle}
                    onArticleEditSave={handleSaveEdit}
                    onArticleEditCancel={handleCancelEdit}
                    isEditingBusy={isProcessing}
                    onArticleDelete={handleDelete}
                  />
                ) : (
                  <div className="text-center text-gray-500 py-12">
                    <p className="text-lg mb-2">{t('未找到文章')}</p>
                    <p className="text-sm">{t('请尝试上传新文章或调整筛选条件。')}</p>
                  </div>
                )}
              </>
            )}
            {/* 删除确认对话框 */}
            {deletingArticle && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                  <h2 className="text-xl font-bold mb-4 text-red-600">{t('确认删除')}</h2>
                  <p className="text-gray-700 mb-6">
                    {t('确定要删除文章')} <strong>"{deletingArticle.title}"</strong> {t('吗？此操作无法撤销。')}
                  </p>
                  <div className="flex justify-end space-x-3">
                    <button
                      onClick={handleCancelDelete}
                      disabled={isProcessing}
                      className="px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
                    >
                      {t('取消')}
                    </button>
                    <button
                      onClick={handleConfirmDelete}
                      disabled={isProcessing}
                      className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {t(isProcessing ? '删除中...' : '确认删除')}
                    </button>
                  </div>
                </div>
              </div>
            )}
            
            {/* Bottom padding for fixed button */}
            <div className="pb-24"></div>
          </div>
        </div>

      {/* Upload New Button - Fixed Position */}
      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
        <button
          onClick={handleUploadNew}
          className="bg-[#5BE2C2] hover:bg-[#44c5a7] text-white px-8 py-3 rounded-[40px] shadow-lg transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-[#a8f4e3]"
        >
          <div className="flex items-center space-x-2">
            <svg 
              className="w-5 h-5" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 4v16m8-8H4" 
              />
            </svg>
            <span className="font-semibold">{t('上传新文章')}</span>
          </div>
        </button>
      </div>
    </div>
  )
}

export default ArticleSelection 