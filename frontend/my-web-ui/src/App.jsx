import { useState } from 'react'
import { ApiDemo } from './components/ApiDemo'
import WordDemo from './modules/word-demo/WordDemo'
import GrammarDemo from './modules/grammar-demo/GrammarDemo'
import ArticleSelection from './modules/article/ArticleSelection'
import ArticleChatView from './modules/article/ArticleChatView'

function App() {
  const [currentPage, setCurrentPage] = useState('article')
  const [selectedArticleId, setSelectedArticleId] = useState(null)
  const [isUploadMode, setIsUploadMode] = useState(false)

  const navButton = (id, label) => (
    <button
      onClick={() => setCurrentPage(id)}
      className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
        currentPage === id
          ? 'border-blue-500 text-gray-900'
          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div className="min-h-screen bg-gray-100 overflow-auto">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-gray-900">Language Learning App</h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navButton('apiDemo', 'API Demo')}
                {navButton('wordDemo', 'Word Demo')}
                {navButton('grammarDemo', 'Grammar Demo')}
                {navButton('article', 'Article')}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className={`max-w-7xl mx-auto sm:px-6 lg:px-8 ${
        currentPage === 'article' ? 'h-[calc(100vh-64px)] overflow-hidden' : 'min-h-[calc(100vh-64px)]'
      }`}>
        <div className={`px-4 sm:px-0 ${currentPage === 'article' ? 'h-full' : ''}`}>
          {/* Pages */}
          {currentPage === 'apiDemo' && (
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <ApiDemo />
            </div>
          )}

          {currentPage === 'wordDemo' && <WordDemo />}

          {currentPage === 'grammarDemo' && <GrammarDemo />}

          {currentPage === 'article' && (
            selectedArticleId ? (
              <ArticleChatView
                articleId={selectedArticleId}
                isUploadMode={isUploadMode}
                onBack={() => {
                  setSelectedArticleId(null)
                  setIsUploadMode(false)
                }}
                onUploadComplete={() => {
                  setSelectedArticleId(null)
                  setIsUploadMode(false)
                }}
              />
            ) : (
              <ArticleSelection
                onArticleSelect={(id) => {
                  setSelectedArticleId(id)
                  setIsUploadMode(false)
                }}
                onUploadNew={() => {
                  setSelectedArticleId('upload')
                  setIsUploadMode(true)
                }}
              />
            )
          )}
        </div>
      </div>
    </div>
  )
}

export default App


