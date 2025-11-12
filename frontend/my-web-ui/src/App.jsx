import { useState } from 'react'
import { ApiDemo } from './components/ApiDemo'
import WordDemo from './modules/word-demo/WordDemo'
import GrammarDemo from './modules/grammar-demo/GrammarDemo'
import ArticleSelection from './modules/article/ArticleSelection'
import ArticleChatView from './modules/article/ArticleChatView'
import LoginButton from './modules/auth/components/LoginButton'
import LoginModal from './modules/auth/components/LoginModal'
import RegisterModal from './modules/auth/components/RegisterModal'
import UserAvatar from './modules/auth/components/UserAvatar'
import UserDebugButton from './modules/auth/components/UserDebugButton'
import DataMigrationModal from './components/DataMigrationModal'
import { UserProvider, useUser } from './contexts/UserContext'

function AppContent() {
  const [currentPage, setCurrentPage] = useState('article')
  const [selectedArticleId, setSelectedArticleId] = useState(null)
  const [isUploadMode, setIsUploadMode] = useState(false)
  
  // 模态框状态
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showRegisterModal, setShowRegisterModal] = useState(false)
  
  // 从 UserContext 获取用户信息和方法
  const { 
    userId: currentUserId,
    password: currentUserPassword,
    isAuthenticated,
    login,
    register,
    logout,
    pendingGuestId,
    showMigrationDialog,
    setShowMigrationDialog
  } = useUser()

  // 处理登出 - 使用 UserContext
  const handleLogout = () => {
    logout()
    console.log('👋 [App] 已登出，数据将自动清空')
    // 不需要刷新页面，组件会自动响应 isAuthenticated 变化
  }

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
            {/* 左侧：Logo 和导航 */}
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

            {/* 右侧：登录/用户信息 */}
            <div className="flex items-center space-x-3">
              {isAuthenticated ? (
                <>
                  {/* Debug 按钮（仅开发环境） */}
                  <UserDebugButton 
                    userId={currentUserId} 
                    password={currentUserPassword}
                  />
                  
                  {/* 用户头像 */}
                  <UserAvatar userId={currentUserId} onLogout={handleLogout} />
                </>
              ) : (
                <LoginButton onClick={() => setShowLoginModal(true)} />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 登录模态框 */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onSwitchToRegister={() => {
          setShowLoginModal(false)
          setShowRegisterModal(true)
        }}
      />

      {/* 注册模态框 */}
      <RegisterModal
        isOpen={showRegisterModal}
        onClose={() => setShowRegisterModal(false)}
        onSwitchToLogin={() => {
          setShowRegisterModal(false)
          setShowLoginModal(true)
        }}
      />

      {/* 数据迁移模态框 */}
      <DataMigrationModal
        isOpen={showMigrationDialog}
        onClose={() => setShowMigrationDialog(false)}
        guestId={pendingGuestId}
        onMigrationComplete={(count) => {
          console.log(`✅ [App] 数据迁移完成，共 ${count} 条`)
          setShowMigrationDialog(false)
        }}
      />

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

// 使用 UserProvider 包装 AppContent
function App() {
  return (
    <UserProvider>
      <AppContent />
    </UserProvider>
  )
}

export default App


