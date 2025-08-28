import { useState } from 'react'
import WordDemo from './modules/word-demo/WordDemo'
import GrammarDemo from './modules/grammar-demo/GrammarDemo'
import ArticleSelection from './modules/article/ArticleSelection'
import ArticleChatView from './modules/article/ArticleChatView'
import Navigation from './modules/shared/components/Navigation'
import { ApiDemo } from './components/ApiDemo'

function App() {
  const [currentPage, setCurrentPage] = useState('apiDemo') // 'apiDemo', 'wordDemo', 'grammarDemo', or 'article'
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [isUploadMode, setIsUploadMode] = useState(false)

  const handlePageChange = (pageId) => {
    if (pageId === 'article') {
      // 如果当前在文章聊天页面，点击Article会返回文章选择页面
      setSelectedArticle(null)
    }
    setCurrentPage(pageId)
  }

  const handleArticleSelect = (articleId) => {
    setSelectedArticle(articleId)
  }

  const handleUploadNew = () => {
    setIsUploadMode(true)
  }

  const handleBackFromUpload = () => {
    setIsUploadMode(false)
  }

  const handleUploadComplete = () => {
    setIsUploadMode(false)
    setSelectedArticle('uploaded-article') // 设置一个虚拟的文章ID
  }

  return (
    <div className="min-h-screen">
      {/* Navigation Bar */}
      <Navigation 
        currentPage={currentPage} 
        onPageChange={handlePageChange} 
      />

      {/* Page Content */}
      <div className="h-[calc(100vh-4rem)]">
        {currentPage === 'apiDemo' ? (
          <ApiDemo />
        ) : currentPage === 'wordDemo' ? (
          <WordDemo />
        ) : currentPage === 'grammarDemo' ? (
          <GrammarDemo />
        ) : currentPage === 'article' ? (
          selectedArticle ? (
            <div className="h-full bg-gray-100 p-8">
              <ArticleChatView 
                articleId={selectedArticle} 
                onBack={() => setSelectedArticle(null)}
              />
            </div>
          ) : isUploadMode ? (
            <div className="h-full bg-gray-100 p-8">
              <ArticleChatView 
                articleId="upload-mode" 
                onBack={handleBackFromUpload}
                isUploadMode={true}
                onUploadComplete={handleUploadComplete}
              />
            </div>
          ) : (
            <ArticleSelection onArticleSelect={handleArticleSelect} onUploadNew={handleUploadNew} />
          )
        ) : null}
      </div>
    </div>
  )
}

export default App
