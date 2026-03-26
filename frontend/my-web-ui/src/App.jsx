import { useState, useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import WordDemo from './modules/word-demo/WordDemo'
import GrammarDemo from './modules/grammar-demo/GrammarDemo'
import GrammarReviewSandbox from './modules/grammar-demo/GrammarReviewSandbox'
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
import { LanguageProvider, useLanguage, languageNameToCode } from './contexts/LanguageContext'
import { UiLanguageProvider, useUiLanguage } from './contexts/UiLanguageContext'
import { authService } from './modules/auth/services/authService'
import { useUIText } from './i18n/useUIText'
import UIDemoPage from './pages/UIDemo'
import TestTranslationAPI from './pages/TestDictionaryAPI'
import LandingPage from './pages/LandingPage'
import OnboardingLanguage from './pages/OnboardingLanguage'
import OnboardingReadingIntro from './pages/OnboardingReadingIntro'
import PrivacyPolicyAndTerms from './pages/PrivacyPolicyAndTerms'
import { colors } from './design-tokens'

function AppContent() {
  const queryClient = useQueryClient()
  const t = useUIText()
  const { uiLanguage, setUiLanguage } = useUiLanguage()
  
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
  const [showPPTermsPage, setShowPPTermsPage] = useState(false)
  const [showHeaderLanguageMenu, setShowHeaderLanguageMenu] = useState(false)
  const [showHeaderAddLanguages, setShowHeaderAddLanguages] = useState(false)
  const headerLanguageRef = useRef(null)
  
  // 从 UserContext 获取用户信息和方法
  const { 
    userId: currentUserId,
    email: currentUserEmail, // 🔧 添加 email
    password: currentUserPassword,
    isAuthenticated,
    userInfo,
    login,
    register,
    logout,
    pendingGuestId,
    showMigrationDialog,
    setShowMigrationDialog
  } = useUser()
  
  // 从 LanguageContext 获取语言选择
  const { selectedLanguage, setSelectedLanguage } = useLanguage()
  // 内容语言候选（UI 展示用，内部仍兼容“英语/德语”等旧值）
  const ALL_LANGUAGES = ['中文', '英文', '西班牙语', '法语', '日语', '韩语', '德文', '阿拉伯语', '俄语']

  const getHeaderLanguageStorageKey = () => {
    const id = currentUserId || 'guest'
    return `content_languages_chosen_${id}`
  }

  const resolveHeaderLanguages = () => {
    const fallback = selectedLanguage ? [selectedLanguage] : ['德文']
    if (typeof window === 'undefined') {
      return fallback
    }
    try {
      const key = getHeaderLanguageStorageKey()
      const raw = window.localStorage.getItem(key)
      if (!raw) return fallback
      const parsed = JSON.parse(raw)
      if (!Array.isArray(parsed)) return fallback
      const valid = parsed.filter((lang) => ALL_LANGUAGES.includes(lang))
      return Array.from(new Set([...valid, ...fallback]))
    } catch {
      return fallback
    }
  }

  const headerLanguages = resolveHeaderLanguages()

  // 点击窗口其它位置时，自动关闭“正在学习”下拉
  useEffect(() => {
    if (!showHeaderLanguageMenu) return
    const handleClickOutside = (event) => {
      if (!headerLanguageRef.current) return
      if (!headerLanguageRef.current.contains(event.target)) {
        setShowHeaderLanguageMenu(false)
        setShowHeaderAddLanguages(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('touchstart', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('touchstart', handleClickOutside)
    }
  }, [showHeaderLanguageMenu])

  // 登录后从全局 userInfo 初始化 UI 语言和内容语言（跨设备）
  useEffect(() => {
    if (!isAuthenticated || !currentUserId || !userInfo) return

    try {
      const info = userInfo

      // UI 语言
      if (info.ui_language) {
        setUiLanguage(info.ui_language)
      }

      // 内容语言：使用 codes -> 中文名称
      const codeToName = {
        zh: '中文',
        en: '英文',
        de: '德文',
        es: '西班牙语',
        fr: '法语',
        ja: '日语',
        ko: '韩语',
        ar: '阿拉伯语',
        ru: '俄语',
      }

      if (info.content_language && codeToName[info.content_language]) {
        setSelectedLanguage(codeToName[info.content_language])
      } else if (Array.isArray(info.languages_list) && info.languages_list.length > 0) {
        const first = info.languages_list[0]
        if (codeToName[first]) {
          setSelectedLanguage(codeToName[first])
        }
      }

      // 同步 per-user 本地 languages_list 缓存
      if (Array.isArray(info.languages_list) && info.languages_list.length > 0 && typeof window !== 'undefined') {
        const names = info.languages_list
          .map((code) => codeToName[code])
          .filter(Boolean)
        if (names.length > 0) {
          const key = getHeaderLanguageStorageKey()
          try {
            window.localStorage.setItem(key, JSON.stringify(names))
          } catch {
            // ignore
          }
        }
      }
    } catch (e) {
      console.warn('⚠️ [App] 初始化用户语言偏好失败:', e)
    }
  }, [isAuthenticated, currentUserId, userInfo])

  // 处理登出 - 使用 UserContext
  const handleLogout = () => {
    logout()
    console.log('👋 [App] 已登出，数据将自动清空')
    // 🔧 退出后直接回到未登录 Landing 页面
    setShowProfilePage(false)
    navigateToLanding()
  }

  const navButton = (id, label) => {
    const isActive = currentPage === id
    return (
      <button
        onClick={() => {
          setCurrentPage(id)
          // 🔧 修复问题1：当点击语法按钮时，清除URL中的grammarId参数
          if (id === 'grammarDemo') {
            const params = new URLSearchParams(window.location.search)
            params.delete('grammarId')
            const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`
            window.history.replaceState({}, '', newUrl)
          }
        }}
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

  // 如果显示 PP & Terms 页面
  if (showPPTermsPage) {
    return (
      <PrivacyPolicyAndTerms
        onBack={() => setShowPPTermsPage(false)}
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
                {navButton('wordDemo', t('词汇'))}
                {navButton('grammarDemo', t('语法'))}
                {navButton('article', t('阅读'))}
              </div>
            </div>

            {/* 右侧：语言显示和登录/用户信息 */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              {/* “正在学习”只在已登录时显示 */}
              {isAuthenticated && (
                <div
                  ref={headerLanguageRef}
                  className="relative flex items-center space-x-1 sm:space-x-2"
                >
                  <span className="text-xs sm:text-sm font-medium text-gray-700 hidden sm:block whitespace-nowrap">
                    {t('正在学习')}
                  </span>
                  <button
                    type="button"
                    onClick={() =>
                      setShowHeaderLanguageMenu((prev) => {
                        const next = !prev
                        if (!next) {
                          setShowHeaderAddLanguages(false)
                        }
                        return next
                      })
                    }
                    className="inline-flex items-center px-2 py-1.5 sm:px-3 border border-gray-300 rounded-md text-xs sm:text-sm bg-white text-gray-900 focus:outline-none focus:ring-2 focus:border-transparent"
                    style={{ '--tw-ring-color': colors.primary[300] }}
                  >
                    <span className="mr-1">
                      {selectedLanguage ? (t(selectedLanguage) || selectedLanguage) : t('请选择')}
                    </span>
                    <svg
                      className="w-3 h-3 text-gray-500"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {showHeaderLanguageMenu && (
                    <div className="absolute right-0 top-full mt-2 w-44 bg-white border border-gray-200 rounded-md shadow-lg z-20">
                      {/* 已添加的语言列表（可直接切换） */}
                      {headerLanguages.map((lang) => {
                        const isActiveLang = lang === selectedLanguage
                        return (
                          <button
                            key={lang}
                            type="button"
                            onClick={() => {
                              setSelectedLanguage(lang)
                              setShowHeaderLanguageMenu(false)
                              setShowHeaderAddLanguages(false)
                            }}
                            className={[
                              'w-full flex items-center justify-between px-3 py-2 text-xs sm:text-sm',
                              isActiveLang ? 'bg-green-50 text-green-800' : 'text-gray-700 hover:bg-gray-50',
                            ].join(' ')}
                          >
                            <span>{t(lang) || lang}</span>
                            {isActiveLang && (
                              <svg
                                className="w-4 h-4 text-green-600"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            )}
                          </button>
                        )
                      })}
                      <div className="my-1 border-t border-gray-100" />
                      {/* 添加新语言：在此处展开可选语言 */}
                      <button
                        type="button"
                        onClick={() => {
                          setShowHeaderAddLanguages((prev) => !prev)
                        }}
                        className="w-full flex items-center justify-between px-3 py-2 text-xs sm:text-sm text-gray-700 hover:bg-gray-50"
                      >
                        <span>{t('添加')}</span>
                        <span className="text-lg leading-none">+</span>
                      </button>
                      {showHeaderAddLanguages && (
                        <div className="border-t border-gray-100">
                          {ALL_LANGUAGES.filter((lang) => !headerLanguages.includes(lang)).length === 0 ? (
                            <div className="px-3 py-2 text-xs text-gray-400 text-center">
                              {t('已添加全部语言') || '已添加全部语言'}
                            </div>
                          ) : (
                            ALL_LANGUAGES.filter((lang) => !headerLanguages.includes(lang)).map((lang) => (
                              <button
                                key={lang}
                                type="button"
                                onClick={async () => {
                                  const updated = Array.from(new Set([...headerLanguages, lang]))
                                  if (typeof window !== 'undefined') {
                                    try {
                                      const key = getHeaderLanguageStorageKey()
                                      window.localStorage.setItem(
                                        key,
                                        JSON.stringify(updated),
                                      )
                                    } catch {
                                      // ignore
                                    }
                                  }
                                  setSelectedLanguage(lang)
                                  setShowHeaderLanguageMenu(false)
                                  setShowHeaderAddLanguages(false)

                                  // 同步到后端偏好：将上边栏语言转换为代码列表，触发预置文章导入
                                  try {
                                    const languageCodes = updated.map((name) => languageNameToCode(name))
                                    await authService.updatePreferences({
                                      languages_list: languageCodes,
                                    })
                                  } catch (e) {
                                    console.warn('⚠️ [App] 同步 header 语言到后端失败:', e)
                                  }
                                }}
                                className="w-full px-3 py-2 text-left text-xs sm:text-sm text-gray-700 hover:bg-gray-50"
                              >
                                {t(lang) || lang}
                              </button>
                            ))
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
              
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
                    email={currentUserEmail} // 🔧 传递 email
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
        onOpenPPTerms={() => {
          setShowRegisterModal(false)
          setShowPPTermsPage(true)
        }}
        onStartOnboarding={() => {
          setShowRegisterModal(false)
          setIsUploadMode(false)
          setSelectedArticleId(null)
          setCurrentPage('onboardingLanguage')
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

          {currentPage === 'onboardingLanguage' && (
            <OnboardingLanguage
              onContinue={() => {
                setCurrentPage('onboardingReading')
              }}
            />
          )}

          {currentPage === 'onboardingReading' && (
            <OnboardingReadingIntro
              onStartReading={(articleId) => {
                setIsUploadMode(false)
                if (articleId) {
                  setSelectedArticleId(articleId)
                } else {
                  setSelectedArticleId(null)
                }
                setCurrentPage('article')
              }}
              onUploadOwn={() => {
                setIsUploadMode(true)
                setSelectedArticleId('upload')
                setCurrentPage('article')
              }}
            />
          )}

          {currentPage === 'wordDemo' && <WordDemo />}

          {currentPage === 'grammarDemo' && <GrammarDemo />}
          {currentPage === 'grammarReviewSandbox' && <GrammarReviewSandbox />}

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
          {currentPage === 'testTranslationAPI' && <TestTranslationAPI />}
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


