import { useState } from 'react'
import ArticleList from './components/ArticleList'
import FilterBar from '../shared/components/FilterBar'

const ArticleSelection = ({ onArticleSelect, onUploadNew }) => {
  // 示例文章数据
  const [articles] = useState([
    {
      id: 'react-basics',
      title: 'React 基础教程',
      description: '学习 React 的核心概念和基本用法，包括组件、状态管理、生命周期等基础知识。适合初学者入门学习。',
      difficulty: 'Beginner',
      wordCount: 1500,
      estimatedTime: '15 min',
      category: 'Programming',
      tags: ['React', 'JavaScript', 'Frontend', 'Components']
    },
    {
      id: 'fastapi-intro',
      title: 'FastAPI 入门指南',
      description: '快速构建高性能的 Python Web API，学习现代 Python 后端开发的最佳实践。',
      difficulty: 'Intermediate',
      wordCount: 2000,
      estimatedTime: '20 min',
      category: 'Programming',
      tags: ['Python', 'FastAPI', 'Backend', 'API']
    },
    {
      id: 'ai-fundamentals',
      title: '人工智能基础',
      description: '探索人工智能的基本概念，包括机器学习、深度学习、神经网络等核心技术的介绍。',
      difficulty: 'Advanced',
      wordCount: 2500,
      estimatedTime: '25 min',
      category: 'Technology',
      tags: ['AI', 'Machine Learning', 'Deep Learning', 'Neural Networks']
    },
    {
      id: 'web-security',
      title: 'Web 安全基础',
      description: '了解 Web 应用安全的基本概念，学习如何保护你的应用免受常见的安全威胁。',
      difficulty: 'Intermediate',
      wordCount: 1800,
      estimatedTime: '18 min',
      category: 'Technology',
      tags: ['Security', 'Web', 'Authentication', 'Encryption']
    },
    {
      id: 'data-science-intro',
      title: '数据科学入门',
      description: '数据科学的基础知识，包括数据收集、清洗、分析和可视化的完整流程。',
      difficulty: 'Beginner',
      wordCount: 2200,
      estimatedTime: '22 min',
      category: 'Science',
      tags: ['Data Science', 'Python', 'Statistics', 'Visualization']
    },
    {
      id: 'blockchain-basics',
      title: '区块链技术基础',
      description: '深入了解区块链技术的原理和应用，包括比特币、以太坊等主流区块链平台。',
      difficulty: 'Advanced',
      wordCount: 2800,
      estimatedTime: '28 min',
      category: 'Technology',
      tags: ['Blockchain', 'Cryptocurrency', 'Bitcoin', 'Ethereum']
    }
  ])

  const [filteredArticles, setFilteredArticles] = useState(articles)

  const handleFilterChange = (filterId, value) => {
    console.log('Filter changed:', filterId, value)
    
    // 简单的筛选逻辑
    let filtered = [...articles]
    
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

          {/* Article Count */}
          <div className="mb-6">
            <p className="text-gray-600">
              Showing {filteredArticles.length} of {articles.length} articles
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