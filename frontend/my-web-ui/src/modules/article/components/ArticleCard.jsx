import { useUIText } from '../../../i18n/useUIText'

const ArticleCard = ({ 
  id,
  title, 
  description, 
  language, 
  difficulty, 
  wordCount, 
  estimatedTime, 
  category,
  tags = [],
  processingStatus = 'completed', // 处理状态：processing/completed/failed
  onSelect,
  onEdit,
  onDelete,
  className = ""
}) => {
  const t = useUIText()
  const isProcessing = processingStatus === 'processing'
  const isFailed = processingStatus === 'failed'
  const getLanguageColor = (language) => {
    switch (language) {
      case '中文':
        return 'bg-red-100 text-red-800'
      case '英文':
        return 'bg-blue-100 text-blue-800'
      case '德文':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'beginner':
        return 'bg-green-100 text-green-800'
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800'
      case 'advanced':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getCategoryColor = (category) => {
    switch (category?.toLowerCase()) {
      case 'programming':
        return 'bg-blue-100 text-blue-800'
      case 'technology':
        return 'bg-purple-100 text-purple-800'
      case 'science':
        return 'bg-indigo-100 text-indigo-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div 
      className={`
        bg-white rounded-lg border border-gray-200 transition-all duration-300 
        relative
        ${isProcessing || isFailed ? 'opacity-75 cursor-not-allowed' : 'cursor-pointer transform hover:scale-105'}
        ${className}
      `}
      onClick={() => {
        if (!isProcessing && !isFailed) {
          onSelect(id)
        }
      }}
    >
      {/* 语言标签 - 绝对定位在左上角 */}
      {language && (
        <div className="absolute top-3 left-3 z-10">
          <span className={`px-2 py-1 rounded-full text-xs font-medium shadow-sm ${getLanguageColor(language)}`}>
            {language}
          </span>
        </div>
      )}
      
      {/* 操作按钮 - 绝对定位在右上角 */}
      <div className="absolute top-3 right-3 z-10 flex items-center space-x-2">
        {/* 处理状态标签 */}
        {isProcessing && (
          <span className="px-2 py-1 rounded-full text-xs font-medium shadow-sm bg-yellow-100 text-yellow-800 flex items-center">
            <svg className="w-3 h-3 mr-1 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {t('处理中...')}
          </span>
        )}
        {isFailed && (
          <span className="px-2 py-1 rounded-full text-xs font-medium shadow-sm bg-red-100 text-red-800">
            {t('处理失败')}
          </span>
        )}
        
        {/* 编辑和删除按钮 - 只在非处理状态时显示 */}
        {!isProcessing && !isFailed && (
          <>
            {onEdit && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(id, title);
                }}
                className="p-1.5 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 transition-colors"
                title={t('编辑文章名称')}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
            )}
            {onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(id, title);
                }}
                className="p-1.5 rounded-full bg-red-100 text-red-600 hover:bg-red-200 transition-colors"
                title={t('删除文章')}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </>
        )}
      </div>
      
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-xl font-semibold text-gray-900 line-clamp-2 flex-1 pr-2">
            {title}
          </h3>
          <div className="flex space-x-2 flex-shrink-0 ml-2">
            {/* 难度标签 - 可选显示 */}
            {difficulty && difficulty !== 'N/A' && (
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(difficulty)}`}>
                {difficulty}
              </span>
            )}
            {/* 分类标签 */}
            {category && (
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(category)}`}>
                {category}
              </span>
            )}
          </div>
        </div>
        
        <p className="text-gray-600 text-sm leading-relaxed line-clamp-3">
          {description}
        </p>
      </div>

      {/* Stats */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              {wordCount.toLocaleString()} words
            </div>
            <div className="flex items-center">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {estimatedTime}
            </div>
          </div>
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {tags.slice(0, 3).map((tag, index) => (
              <span 
                key={index}
                className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-md"
              >
                {tag}
              </span>
            ))}
            {tags.length > 3 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-md">
                +{tags.length - 3} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Action Button */}
      <div className="px-6 pb-6">
        <button 
          className={`w-full py-2 px-4 rounded-md transition-colors font-medium ${
            isProcessing || isFailed
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
          disabled={isProcessing || isFailed}
        >
          {isProcessing ? t('处理中...') : isFailed ? t('处理失败') : t('Start Reading')}
        </button>
      </div>
    </div>
  )
}

export default ArticleCard 