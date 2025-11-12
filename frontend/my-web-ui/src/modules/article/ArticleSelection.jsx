import { useState } from 'react'
import ArticleList from './components/ArticleList'
import FilterBar from '../shared/components/FilterBar'
import { useArticles } from '../../hooks/useApi'
import { useUser } from '../../contexts/UserContext'

const ArticleSelection = ({ onArticleSelect, onUploadNew }) => {
  const { userId } = useUser()
  const { data, isLoading, isError, error } = useArticles(userId)
  const summaries = Array.isArray(data?.data) ? data.data : []
  // 将后端摘要映射为列表卡片需要的结构
  const mappedArticles = summaries.map((s) => ({
    id: s.text_id,
    title: s.text_title || `Article ${s.text_id}`,
    description: `Sentences: ${s.total_sentences} • Tokens: ${s.total_tokens} • Selectable: ${s.text_tokens}`,
    difficulty: 'N/A',
    wordCount: s.total_tokens || 0,
    estimatedTime: `${Math.max(1, Math.ceil((s.total_sentences || 1) / 5))} min`,
    category: 'Article',
    tags: []
  }))

  const [filteredArticles, setFilteredArticles] = useState(mappedArticles)

  // 同步远端变化
  if (filteredArticles !== mappedArticles && summaries.length > 0 && filteredArticles.length === 0) {
    // 初次加载后填充一次
    // 注：保持简单，避免引入 useEffect 以最少改动接入
    setFilteredArticles(mappedArticles)
  }

  const handleFilterChange = (filterId, value) => {
    console.log('Filter changed:', filterId, value)
    
    // 简单的筛选逻辑
    let filtered = [...mappedArticles]
    
    if (filterId === 'category' && value !== 'all') {
      filtered = filtered.filter(article => 
        article.category.toLowerCase() === value.toLowerCase()
      )
    }
    
    if (filterId === 'difficulty' && value !== 'all') {
      filtered = filtered.filter(article => 
        article.difficulty.toLowerCase() === value.toLowerCase()
      )
    }
    
    if (filterId === 'status' && value !== 'all') {
      // 这里可以根据实际需求实现状态筛选
      // 目前保持所有文章
    }
    
    setFilteredArticles(filtered)
  }

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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Filter Bar */}
      <FilterBar onFilterChange={handleFilterChange} />
      
      {/* Main Content */}
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Choose an Article
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Select an article to start reading and chatting with our AI assistant. 
              Each article covers different topics and difficulty levels.
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
              Showing {filteredArticles.length} of {mappedArticles.length} articles
            </p>
          </div>

          {/* Article List */}
          <ArticleList 
            articles={filteredArticles}
            onArticleSelect={handleArticleSelect}
          />
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