import { ArticlePreviewCard } from '../../../components/features/article/ArticlePreviewCard'

const ArticleList = ({ 
  articles = [], 
  onArticleSelect,
  onArticleEdit,
  onArticleDelete,
  className = ""
}) => {
  if (articles.length === 0) {
    return (
      <div className={`text-center py-12 ${className}`}>
        <div className="text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <p className="text-lg font-medium">No articles available</p>
          <p className="text-sm">Check back later for new content.</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}>
      {articles.map((article) => (
        <ArticlePreviewCard
          key={article.id}
          title={article.title}
          wordCount={article.wordCount}
          noteCount={article.noteCount}
          preview={article.preview}
          processingStatus={article.processingStatus}
          width="100%"
          height="auto"
          onRead={() => onArticleSelect?.(article.id)}
          onEdit={
            onArticleEdit
              ? () => onArticleEdit(article.id, article.title)
              : undefined
          }
          onDelete={
            onArticleDelete
              ? () => onArticleDelete(article.id, article.title)
              : undefined
          }
        />
      ))}
    </div>
  )
}

export default ArticleList 