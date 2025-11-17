import ArticleList from './components/ArticleList'
import { useArticles } from '../../hooks/useApi'
import { useUser } from '../../contexts/UserContext'
import { useLanguage } from '../../contexts/LanguageContext'

const ArticleSelection = ({ onArticleSelect, onUploadNew }) => {
  const { userId, isGuest } = useUser()
  const { selectedLanguage } = useLanguage()
  // 使用API获取文章数据 - 传入 userId、isGuest 和 language（后端过滤或本地过滤）
  const { data, isLoading, isError, error } = useArticles(userId, selectedLanguage, isGuest)
  
  // 处理游客模式和登录模式的数据格式
  let summaries = []
  if (isGuest) {
    // 游客模式：data.data 是文章数组
    summaries = Array.isArray(data?.data) ? data.data : []
  } else {
    // 登录模式：data.data.texts 是文章数组，或者 data.data 本身就是数组
    const responseData = data?.data
    if (Array.isArray(responseData)) {
      summaries = responseData
    } else if (responseData?.texts && Array.isArray(responseData.texts)) {
      summaries = responseData.texts
    } else {
      summaries = []
    }
  }
  
  // 将后端摘要映射为列表卡片需要的结构
  // 注意：language过滤已经在API层面完成（登录模式）或本地完成（游客模式），这里只需要映射数据
  const mappedArticles = summaries.map((s) => {
    // 处理游客模式和登录模式的数据格式
    const textId = s.text_id || s.article_id || s.id
    const textTitle = s.text_title || s.title || `Article ${textId}`
    const totalSentences = s.total_sentences || s.sentence_count || 0
    const totalTokens = s.total_tokens || s.wordCount || 0
    const language = s.language || null
    
    return {
      id: textId,
      title: textTitle,
      description: `Sentences: ${totalSentences} • Tokens: ${totalTokens}`,
      language: language, // 从后端获取语言字段，null表示未设置
      difficulty: 'N/A',
      wordCount: totalTokens,
      estimatedTime: `${Math.max(1, Math.ceil((totalSentences || 1) / 5))} min`,
      category: 'Article',
      tags: []
    }
  })

  // 文章已经在后端过滤，直接使用mappedArticles
  const filteredArticles = mappedArticles

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

  return (
    <div className="h-full bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col">
      {/* Main Content - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                Choose an Article
              </h1>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Select an article to start reading and chatting with our AI assistant. 
                {selectedLanguage !== 'all' && (
                  <span className="block mt-2 text-blue-600 font-medium">
                    当前筛选：{selectedLanguage}
                  </span>
                )}
              </p>
            </div>

            {/* Loading / Error */}
            {isLoading && (
              <div className="text-center text-gray-600 py-8">Loading articles...</div>
            )}
            {isError && (
              <div className="text-center text-red-600 py-8">{String(error)}</div>
            )}

            {/* Article Count */}
            <div className="mb-6">
              <p className="text-gray-600">
                {selectedLanguage === 'all' 
                  ? `Showing ${filteredArticles.length} articles`
                  : `Showing ${filteredArticles.length} articles (${selectedLanguage})`
                }
              </p>
            </div>

            {/* Article List */}
            <ArticleList 
              articles={filteredArticles}
              onArticleSelect={handleArticleSelect}
            />
            
            {/* Bottom padding for fixed button */}
            <div className="pb-24"></div>
          </div>
        </div>
      </div>

      {/* Upload New Button - Fixed Position */}
      <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
        <button
          onClick={handleUploadNew}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-full shadow-lg transition-all duration-300 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-blue-300"
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
            <span className="font-medium">Upload New</span>
          </div>
        </button>
      </div>
    </div>
  )
}

export default ArticleSelection 