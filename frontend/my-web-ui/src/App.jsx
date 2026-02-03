import { useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import WordDemo from './modules/word-demo/WordDemo'
import GrammarDemo from './modules/grammar-demo/GrammarDemo'
import ArticleSelection from './modules/article/ArticleSelection'
import ArticleChatView from './modules/article/ArticleChatView'
import LoginButton from './modules/auth/components/LoginButton'
import LoginModal from './modules/auth/components/LoginModal'
import RegisterModal from './modules/auth/components/RegisterModal'
import ForgotPasswordModal from './modules/auth/components/ForgotPasswordModal'
import ResetPasswordPage from './modules/auth/components/ResetPasswordPage'
import UserAvatar from './modules/auth/components/UserAvatar'
import ProfilePage from './modules/auth/components/ProfilePage'
import UserDebugButton from './modules/auth/components/UserDebugButton'
import DataMigrationModal from './components/DataMigrationModal'
import { UserProvider, useUser } from './contexts/UserContext'
import { LanguageProvider, useLanguage } from './contexts/LanguageContext'
import { UiLanguageProvider } from './contexts/UiLanguageContext'
import { useUIText } from './i18n/useUIText'
import UIDemoPage from './pages/UIDemo'
import LandingPage from './pages/LandingPage'
import { colors } from './design-tokens'

function AppContent() {
  const queryClient = useQueryClient()
  const t = useUIText()
  
  // 🔧 检查是否在重置密码页面
  const isResetPasswordPage = window.location.pathname === '/reset-password'
  
  // 🔧 从 URL 参数初始化页面状态
  const getInitialStateFromURL = () => {
    const params = new URLSearchParams(window.location.search)
    const page = params.get('page') || 'landing'
    const articleId = params.get('articleId')
    return { page, articleId }
  }

  const initialState = getInitialStateFromURL()
  const [currentPage, setCurrentPage] = useState(initialState.page)
  const [selectedArticleId, setSelectedArticleId] = useState(initialState.articleId)
  const [isUploadMode, setIsUploadMode] = useState(false)

  const navigateToLanding = () => {
    setIsUploadMode(false)
    setSelectedArticleId(null)
    setCurrentPage('landing')
  }

  const handleLandingArticleSelect = (articleId) => {
    if (!articleId) {
      return
    }
    setIsUploadMode(false)
    setSelectedArticleId(articleId)
    setCurrentPage('article')
  }

  const handleLandingViewAll = () => {
    setIsUploadMode(false)
    setSelectedArticleId(null)
    setCurrentPage('article')
  }

  const handleStartVocabReview = () => {
    setCurrentPage('wordDemo')
  }

  const handleStartGrammarReview = () => {
    setCurrentPage('grammarDemo')
  }
  
  // 🔧 监听 URL 参数变化（用于新标签页打开）
  useEffect(() => {
    const handlePopState = () => {
      const state = getInitialStateFromURL()
      setCurrentPage(state.page)
      if (state.articleId) {
        setSelectedArticleId(state.articleId)
      }
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  // 🔧 当页面或 articleId 变化时，更新 URL（但不刷新页面）
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (currentPage) {
      params.set('page', currentPage)
    } else {
      params.delete('page')
    }
    if (selectedArticleId) {
      params.set('articleId', selectedArticleId)
    } else {
      params.delete('articleId')
    }
    const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`
    if (window.location.href !== window.location.origin + newUrl) {
      window.history.replaceState({}, '', newUrl)
    }
  }, [currentPage, selectedArticleId])
  
  // 模态框状态
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [showRegisterModal, setShowRegisterModal] = useState(false)
  const [showForgotPasswordModal, setShowForgotPasswordModal] = useState(false)
  const [showProfilePage, setShowProfilePage] = useState(false)
  
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
  
  // 从 LanguageContext 获取语言选择
  const { selectedLanguage, setSelectedLanguage } = useLanguage()

  // 处理登出 - 使用 UserContext
  const handleLogout = () => {
    logout()
    console.log('👋 [App] 已登出，数据将自动清空')
    // 不需要刷新页面，组件会自动响应 isAuthenticated 变化
  }

  const navButton = (id, label) => {
    const isActive = currentPage === id
    return (
      <button
        onClick={() => setCurrentPage(id)}
        className="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
        style={{
          borderColor: isActive ? colors.primary[600] : 'transparent',
          color: isActive ? colors.semantic?.text?.primary ?? '#111827' : colors.semantic?.text?.secondary ?? '#6b7280',
        }}
      >
        {label}
      </button>
    )
  }

  // 如果是重置密码页面，直接显示重置密码组件（Provider 已在 App 外层）
  if (isResetPasswordPage) {
    return (
      <ResetPasswordPage 
        onBackToLogin={() => {
          window.location.href = '/'
        }}
      />
    )
  }

  // 如果显示个人中心页面
  if (showProfilePage) {
    return (
      <ProfilePage
        onClose={() => setShowProfilePage(false)}
        onLogout={handleLogout}
      />
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 overflow-auto">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* 左侧：Logo 和导航 */}
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <button
                  type="button"
                  onClick={navigateToLanding}
                  className="text-xl font-bold text-gray-900 focus:outline-none focus-visible:ring-2 rounded"
                  style={{ '--tw-ring-color': colors.primary[300] }}
                >
                  {t('语言学习应用')}
                </button>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navButton('wordDemo', t('单词演示'))}
                {navButton('grammarDemo', t('语法演示'))}
                {navButton('article', t('文章'))}
              </div>
            </div>

            {/* 右侧：语言切换和登录/用户信息 */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              {/* 语言切换下拉选项 - 全局显示 */}
              <div className="flex items-center space-x-1 sm:space-x-2">
                <label htmlFor="language-select" className="text-xs sm:text-sm font-medium text-gray-700 hidden sm:block whitespace-nowrap">
                  {t('正在学习')}
                </label>
                <select
                  id="language-select"
                  value={!isAuthenticated || !selectedLanguage ? '' : selectedLanguage}
                  onChange={(e) => {
                    if (e.target.value) {
                      setSelectedLanguage(e.target.value)
                    }
                  }}
                  className="px-2 py-1.5 sm:px-3 border border-gray-300 rounded-md text-xs sm:text-sm focus:outline-none focus:ring-2 focus:border-transparent bg-white text-gray-900"
                  style={{ '--tw-ring-color': colors.primary[300] }}
                >
                  {(!isAuthenticated || !selectedLanguage) && (
                    <option value="" disabled hidden>{t('请选择')}</option>
                  )}
                  <option value="中文">{t('中文')}</option>
                  <option value="英文">{t('英文')}</option>
                  <option value="德文">{t('德文')}</option>
                </select>
              </div>
              
              {isAuthenticated ? (
                <>
                  {/* Debug 按钮（仅开发环境）- 已隐藏 */}
                  {/* <UserDebugButton 
                    userId={currentUserId} 
                    password={currentUserPassword}
                  /> */}
                  
                  {/* 用户头像 */}
                  <UserAvatar 
                    userId={currentUserId} 
                    onLogout={handleLogout}
                    onOpenProfile={() => setShowProfilePage(true)}
                  />
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
        onSwitchToForgotPassword={() => {
          setShowLoginModal(false)
          setShowForgotPasswordModal(true)
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

      {/* 忘记密码模态框 */}
      <ForgotPasswordModal
        isOpen={showForgotPasswordModal}
        onClose={() => setShowForgotPasswordModal(false)}
        onSwitchToLogin={() => {
          setShowForgotPasswordModal(false)
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
        currentPage === 'article' ? 'h-[calc(100vh-64px)]' : 'min-h-[calc(100vh-64px)]'
      }`}>
        <div className={`px-4 sm:px-0 ${currentPage === 'article' ? 'h-full' : ''}`}>
          {/* Pages */}
          {currentPage === 'landing' && (
            <div className="bg-white rounded-lg border border-gray-200">
              <LandingPage
                onArticleSelect={handleLandingArticleSelect}
                onNavigateToArticles={handleLandingViewAll}
                onStartVocabReview={handleStartVocabReview}
                onStartGrammarReview={handleStartGrammarReview}
                onRegister={() => setShowRegisterModal(true)}
              />
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
                  console.log('🔙 [App] 返回文章列表')
                  // 🔧 确保状态更新顺序正确，避免空白页
                  setIsUploadMode(false)
                  setSelectedArticleId(null)
                  // 🔧 确保 ArticleSelection 组件能正确渲染
                  queryClient.invalidateQueries({ 
                    predicate: (query) => {
                      const key = query.queryKey
                      return key && key[0] === 'articles'
                    }
                  })
                }}
                onUploadComplete={(articleId, uploadLanguage) => {
                  // 🔧 上传完成后，直接跳转到新文章（不再先返回列表）
                  console.log('🔄 [App] 上传完成，准备跳转到新文章，articleId:', articleId, 'uploadLanguage:', uploadLanguage)
                  
                  if (articleId) {
                    // 🔧 若上传语言与上边栏语言不同，自动覆盖上边栏语言（用户体验：上传什么语言就看什么语言）
                    if (uploadLanguage && uploadLanguage !== selectedLanguage) {
                      console.log('🌐 [App] 覆盖上边栏语言:', selectedLanguage, '->', uploadLanguage)
                      setSelectedLanguage(uploadLanguage)
                    }
                    // 🔧 直接跳转到新文章，不返回列表
                    setIsUploadMode(false)
                    // 🔧 先刷新文章列表（在后台），然后立即跳转
                    // 注意：invalidateQueries 只是标记查询为过期，不会阻塞跳转
                    queryClient.invalidateQueries({ 
                      predicate: (query) => {
                        const key = query.queryKey
                        return key && key[0] === 'articles'
                      }
                    })
                    // 直接设置文章ID，跳转到新文章（ArticleChatView 会根据 articleId 加载文章）
                    console.log('✅ [App] 跳转到新文章:', articleId)
                    setSelectedArticleId(articleId)
                  } else {
                    // 如果没有文章ID，返回文章列表
                    setSelectedArticleId(null)
                    setIsUploadMode(false)
                    // 刷新文章列表
                    queryClient.invalidateQueries({ 
                      predicate: (query) => {
                        const key = query.queryKey
                        return key && key[0] === 'articles'
                      }
                    })
                  }
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

          {currentPage === 'UIDemo' && <UIDemoPage />}
        </div>
      </div>
    </div>
  )
}

// 使用 UserProvider 和 LanguageProvider 包装 AppContent
function App() {
  return (
    <UserProvider>
      <LanguageProvider>
        <UiLanguageProvider>
          <AppContent />
        </UiLanguageProvider>
      </LanguageProvider>
    </UserProvider>
  )
}

export default App


