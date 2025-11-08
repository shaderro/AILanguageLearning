import { useState, useEffect } from 'react'
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
import authService from './modules/auth/services/authService'

function App() {
  const [currentPage, setCurrentPage] = useState('article')
  const [selectedArticleId, setSelectedArticleId] = useState(null)
  const [isUploadMode, setIsUploadMode] = useState(false)
  
  // 认证状态（先用简单的 state，后续可以改为 Context）
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [currentUserId, setCurrentUserId] = useState(null)
  const [currentUserPassword, setCurrentUserPassword] = useState(null) // 仅开发调试用
  
  // 模态框状态
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showRegisterModal, setShowRegisterModal] = useState(false)

  // 自动登录：页面加载时检查 localStorage
  useEffect(() => {
    const { userId, token } = authService.getAuth()
    
    if (userId && token) {
      console.log('🔍 [App] 检测到已保存的登录信息，尝试自动登录...')
      
      // 验证 token 是否有效
      authService.getCurrentUser(token)
        .then((user) => {
          console.log('✅ [App] 自动登录成功:', user)
          setIsAuthenticated(true)
          setCurrentUserId(parseInt(userId))
        })
        .catch((error) => {
          console.log('⚠️ [App] 自动登录失败，token可能已过期:', error)
          authService.clearAuth()
        })
    }
  }, [])

  // 处理登录
  const handleLogin = (userId, token, password) => {
    setIsAuthenticated(true)
    setCurrentUserId(userId)
    setCurrentUserPassword(password) // 保存密码仅用于 debug
    setShowLoginModal(false)
    console.log('✅ [App] 登录成功:', { userId, token: token.substring(0, 20) + '...' })
  }

  // 处理注册
  const handleRegister = (userId, token, password) => {
    setIsAuthenticated(true)
    setCurrentUserId(userId)
    setCurrentUserPassword(password) // 保存密码仅用于 debug
    setShowRegisterModal(false)
    console.log('✅ [App] 注册成功:', { userId, token: token.substring(0, 20) + '...' })
  }

  // 处理登出
  const handleLogout = () => {
    authService.clearAuth()
    setIsAuthenticated(false)
    setCurrentUserId(null)
    setCurrentUserPassword(null)
    console.log('👋 [App] 已登出')
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
        onLoginSuccess={handleLogin}
      />

      {/* 注册模态框 */}
      <RegisterModal
        isOpen={showRegisterModal}
        onClose={() => setShowRegisterModal(false)}
        onSwitchToLogin={() => {
          setShowRegisterModal(false)
          setShowLoginModal(true)
        }}
        onRegisterSuccess={handleRegister}
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

export default App


