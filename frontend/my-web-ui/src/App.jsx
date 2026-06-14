import { useState, useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import WordDemo from './modules/word-demo/WordDemo'
import GrammarDemo from './modules/grammar-demo/GrammarDemo'
import GrammarReviewSandbox from './modules/grammar-demo/GrammarReviewSandbox'
import ArticleSelection from './modules/article/ArticleSelection'
import ArticleChatView from './modules/article/ArticleChatView'
import LoginButton from './modules/auth/components/LoginButton'
import MagicLinkAuthModal from './modules/auth/components/MagicLinkAuthModal'
import ResetPasswordPage from './modules/auth/components/ResetPasswordPage'
import AuthCallbackPage from './modules/auth/components/AuthCallbackPage'
import UserAvatar from './modules/auth/components/UserAvatar'
import ProfilePage from './modules/auth/components/ProfilePage'
import CreditsIndicator from './components/features/credits/CreditsIndicator'
import WelcomeCreditsBanner from './components/features/credits/WelcomeCreditsBanner'
import { shouldShowWelcomeCredits, dismissWelcomeCredits } from './utils/creditsUtils'
import { shouldShowOnboarding, completeOnboarding, userNeedsOnboarding } from './utils/onboardingUtils'
import {
  CONTENT_LANGUAGE_NAMES,
  LANGUAGE_CODE_TO_NAME,
  languageCodesToNames,
  resolveHeaderLanguages,
  readStoredHeaderLanguages,
  writeStoredHeaderLanguages,
} from './utils/headerLanguageStorage'
import UserDebugButton from './modules/auth/components/UserDebugButton'
import DataMigrationModal from './components/DataMigrationModal'
import { UserProvider, useUser } from './contexts/UserContext'
import { BillingProvider } from './contexts/BillingContext'
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
import ChatConcurrencySandbox from './pages/ChatConcurrencySandbox'
import ArticleUploadSandbox from './pages/ArticleUploadSandbox'
import ArticleViewSandbox from './pages/ArticleViewSandbox'
import FuriganaSandbox from './pages/FuriganaSandbox'
import ChineseZhuyinSandbox from './pages/ChineseZhuyinSandbox'
import { colors } from './design-tokens'
import { recordRecentArticle } from './utils/pageStateManager'
import BillingSandboxRoutes, { isBillingSandboxPath } from './sandbox/billing/BillingSandboxRoutes'
import UISandboxRoutes, { isUISandboxPath } from './sandbox/ui/UISandboxRoutes'

function AppContent() {
  const queryClient = useQueryClient()
  const t = useUIText()
  const { uiLanguage, setUiLanguage } = useUiLanguage()
  
  // 🔧 检查是否在重置密码页面
  const isResetPasswordPage = window.location.pathname === '/reset-password'
  const isAuthCallbackPage = window.location.pathname === '/auth/callback'
  
  // 🔧 从 URL 参数初始化页面状态
  const getInitialStateFromURL = () => {
    const params = new URLSearchParams(window.location.search)
    const page = params.get('page') || 'landing'
    const articleId = params.get('articleId')
    return { page, articleId }
  }

  const getLanguageFromURL = () => {
    const params = new URLSearchParams(window.location.search)
    return params.get('lang') || null
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

  useEffect(() => {
    if (currentPage !== 'article' || !selectedArticleId || selectedArticleId === 'upload') {
      return
    }
    recordRecentArticle(selectedArticleId)
  }, [currentPage, selectedArticleId])
  
  // 模态框状态
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [showProfilePage, setShowProfilePage] = useState(false)
  const [showPPTermsPage, setShowPPTermsPage] = useState(false)
  const [showHeaderLanguageMenu, setShowHeaderLanguageMenu] = useState(false)
  const [showHeaderAddLanguages, setShowHeaderAddLanguages] = useState(false)
  const [showInsightsMenu, setShowInsightsMenu] = useState(false)
  const [showWelcomeCredits, setShowWelcomeCredits] = useState(false)
  const [headerLanguagesList, setHeaderLanguagesList] = useState([])
  const headerLanguageRef = useRef(null)
  const insightsMenuRef = useRef(null)
  
  // 从 UserContext 获取用户信息和方法
  const { 
    userId: currentUserId,
    email: currentUserEmail, // 🔧 添加 email
    password: currentUserPassword,
    token,
    isAuthenticated,
    userInfo,
    login,
    register,
    logout,
    pendingGuestId,
    showMigrationDialog,
    setShowMigrationDialog,
    refreshUserInfo,
  } = useUser()

  useEffect(() => {
    if (!isAuthenticated || !currentUserId || !userInfo) {
      setShowWelcomeCredits(false)
      return
    }
    setShowWelcomeCredits(shouldShowWelcomeCredits(currentUserId))
  }, [isAuthenticated, currentUserId, userInfo])

  // Magic link 等新用户：若尚未设置内容语言，进入 onboarding
  useEffect(() => {
    if (!isAuthenticated || !currentUserId || !userInfo) return
    if (!shouldShowOnboarding(currentUserId, userInfo)) return
    if (currentPage === 'onboardingLanguage' || currentPage === 'onboardingReading') return
    setCurrentPage(
      userNeedsOnboarding(userInfo) ? 'onboardingLanguage' : 'onboardingReading',
    )
  }, [isAuthenticated, currentUserId, userInfo, currentPage])

  const handleDismissWelcomeCredits = () => {
    if (currentUserId) {
      dismissWelcomeCredits(currentUserId)
    }
    setShowWelcomeCredits(false)
  }
  
  // 从 LanguageContext 获取语言选择
  const { selectedLanguage, setSelectedLanguage } = useLanguage()
  const prevSelectedLanguageRef = useRef(selectedLanguage)
  const initializedUserLanguageRef = useRef(null)
  const suppressNextArticleResetRef = useRef(false)
  const initialUrlPageRef = useRef(initialState.page)
  const initialUrlArticleIdRef = useRef(initialState.articleId)
  const initialUrlLanguageRef = useRef(getLanguageFromURL())
  const hasCompletedDirectOpenArticleLanguageSyncRef = useRef(
    !(initialUrlPageRef.current === 'article' && initialUrlArticleIdRef.current && initialUrlLanguageRef.current)
  )
  const ALL_LANGUAGES = CONTENT_LANGUAGE_NAMES

  const getResolvedHeaderLanguages = () =>
    resolveHeaderLanguages({
      userId: currentUserId,
      isAuthenticated,
      userInfo,
      selectedLanguage,
      needsOnboarding: isAuthenticated && userNeedsOnboarding(userInfo),
    })

  const persistHeaderLanguages = (names) => {
    const valid = Array.from(
      new Set(names.filter((lang) => ALL_LANGUAGES.includes(lang))),
    )
    const next = valid.length > 0 ? valid : getResolvedHeaderLanguages()
    setHeaderLanguagesList(next)
    if (currentUserId != null) {
      writeStoredHeaderLanguages(currentUserId, next)
    }
    return next
  }

  const serverLanguagesKey = JSON.stringify(userInfo?.languages_list ?? [])

  // 登录后随服务端 languages_list 更新「正在学习」列表
  useEffect(() => {
    if (!isAuthenticated || !currentUserId || !userInfo) return
    const names = languageCodesToNames(userInfo.languages_list)
    if (names.length > 0) {
      setHeaderLanguagesList(names)
      writeStoredHeaderLanguages(currentUserId, names)
    } else if (userNeedsOnboarding(userInfo)) {
      setHeaderLanguagesList([])
    }
  }, [isAuthenticated, currentUserId, serverLanguagesKey])

  // 游客模式：按用户维度读取本地缓存
  useEffect(() => {
    if (isAuthenticated || currentUserId == null) return
    const stored = readStoredHeaderLanguages(currentUserId)
    if (stored?.length) {
      setHeaderLanguagesList(stored)
      return
    }
    setHeaderLanguagesList(selectedLanguage ? [selectedLanguage] : ['德文'])
  }, [currentUserId, isAuthenticated, selectedLanguage])

  const headerLanguages = headerLanguagesList

  const refreshLanguageContent = () => {
    if (!currentUserId) return
    queryClient.invalidateQueries({ queryKey: ['articles', currentUserId] })
    queryClient.invalidateQueries({ queryKey: ['vocab', currentUserId] })
    queryClient.invalidateQueries({ queryKey: ['grammar', currentUserId] })
  }

  const prevSelectedLanguageForRefreshRef = useRef(selectedLanguage)
  useEffect(() => {
    if (prevSelectedLanguageForRefreshRef.current === selectedLanguage) {
      return
    }
    prevSelectedLanguageForRefreshRef.current = selectedLanguage
    if (isAuthenticated && currentUserId) {
      refreshLanguageContent()
    }
  }, [selectedLanguage, isAuthenticated, currentUserId, queryClient])

  const applyHeaderLanguageSelection = async (lang, updatedHeaderLanguages = null) => {
    const updated = persistHeaderLanguages(updatedHeaderLanguages || headerLanguages)

    setShowHeaderLanguageMenu(false)
    setShowHeaderAddLanguages(false)

    if (isAuthenticated) {
      try {
        const languageCodes = updated.map((name) => languageNameToCode(name))
        await authService.updatePreferences({
          languages_list: languageCodes,
          content_language: languageNameToCode(lang),
        })
        if (token) {
          await refreshUserInfo(token, { force: true })
        }
      } catch (e) {
        console.warn('⚠️ [App] 同步 header 语言到后端失败:', e)
      }
    }

    setSelectedLanguage(lang)
    refreshLanguageContent()
  }

  /** 从「正在学习」列表移除语言，不删除该语言下的文章/词汇等数据 */
  const removeHeaderLanguage = async (langToRemove) => {
    if (headerLanguages.length <= 1) {
      return
    }

    const updated = headerLanguages.filter((lang) => lang !== langToRemove)
    persistHeaderLanguages(updated)

    let nextSelected = selectedLanguage
    if (selectedLanguage === langToRemove) {
      nextSelected = updated[0]
      setSelectedLanguage(nextSelected)
    }

    if (isAuthenticated) {
      try {
        await authService.updatePreferences({
          languages_list: updated.map((name) => languageNameToCode(name)),
          content_language: languageNameToCode(nextSelected),
        })
        if (token) {
          await refreshUserInfo(token, { force: true })
        }
      } catch (e) {
        console.warn('⚠️ [App] 从正在学习列表移除语言失败:', e)
      }
    }

    refreshLanguageContent()
  }

  const setSelectedLanguageWithoutArticleReset = (language) => {
    suppressNextArticleResetRef.current = true
    setSelectedLanguage(language)
  }

  useEffect(() => {
    const urlPage = initialUrlPageRef.current
    const urlArticleId = initialUrlArticleIdRef.current
    const urlLanguage = initialUrlLanguageRef.current
    if (urlPage !== 'article' || !urlArticleId || !urlLanguage) {
      hasCompletedDirectOpenArticleLanguageSyncRef.current = true
      return
    }

    if (selectedLanguage === urlLanguage) {
      prevSelectedLanguageRef.current = selectedLanguage
      hasCompletedDirectOpenArticleLanguageSyncRef.current = true
      return
    }

    prevSelectedLanguageRef.current = urlLanguage
    setSelectedLanguageWithoutArticleReset(urlLanguage)
  }, [selectedLanguage, setSelectedLanguage])

  useEffect(() => {
    const prevLanguage = prevSelectedLanguageRef.current
    if (prevLanguage === selectedLanguage) {
      return
    }
    prevSelectedLanguageRef.current = selectedLanguage

    if (suppressNextArticleResetRef.current) {
      suppressNextArticleResetRef.current = false
      return
    }

    const urlPage = initialUrlPageRef.current
    const urlArticleId = initialUrlArticleIdRef.current
    const urlLanguage = initialUrlLanguageRef.current
    if (
      urlPage === 'article' &&
      urlArticleId &&
      urlLanguage &&
      !hasCompletedDirectOpenArticleLanguageSyncRef.current
    ) {
      return
    }

    if (currentPage === 'article' && selectedArticleId) {
      setIsUploadMode(false)
      setSelectedArticleId(null)
    }
  }, [selectedLanguage, currentPage, selectedArticleId])

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

  useEffect(() => {
    if (!showInsightsMenu) return
    const handleClickOutside = (event) => {
      if (!insightsMenuRef.current) return
      if (!insightsMenuRef.current.contains(event.target)) {
        setShowInsightsMenu(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('touchstart', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('touchstart', handleClickOutside)
    }
  }, [showInsightsMenu])

  // 登录后从全局 userInfo 初始化 UI 语言和内容语言（跨设备）
  useEffect(() => {
    if (!isAuthenticated || !currentUserId || !userInfo) return
    if (initializedUserLanguageRef.current === currentUserId) return

    try {
      const info = userInfo

      // UI 语言
      if (info.ui_language) {
        setUiLanguage(info.ui_language)
      }

      if (info.content_language && LANGUAGE_CODE_TO_NAME[info.content_language]) {
        setSelectedLanguageWithoutArticleReset(LANGUAGE_CODE_TO_NAME[info.content_language])
      } else if (Array.isArray(info.languages_list) && info.languages_list.length > 0) {
        const first = info.languages_list[0]
        if (LANGUAGE_CODE_TO_NAME[first]) {
          setSelectedLanguageWithoutArticleReset(LANGUAGE_CODE_TO_NAME[first])
        }
      }

      const names = languageCodesToNames(info.languages_list)
      if (names.length > 0) {
        setHeaderLanguagesList(names)
        writeStoredHeaderLanguages(currentUserId, names)
      }
      initializedUserLanguageRef.current = currentUserId
    } catch (e) {
      console.warn('⚠️ [App] 初始化用户语言偏好失败:', e)
    }
  }, [isAuthenticated, currentUserId, userInfo])

  useEffect(() => {
    if (isAuthenticated) return
    initializedUserLanguageRef.current = null
  }, [isAuthenticated])

  // 处理登出 - 使用 UserContext
  const handleLogout = () => {
    logout()
    console.log('👋 [App] 已登出，数据将自动清空')
    // 🔧 退出后直接回到未登录 Landing 页面
    setShowProfilePage(false)
    navigateToLanding()
  }

  const navigateToPage = (id) => {
    setCurrentPage(id)
    const params = new URLSearchParams(window.location.search)
    if (id === 'wordDemo') {
      params.delete('vocabId')
    }
    if (id === 'grammarDemo') {
      params.delete('grammarId')
    }
    const newUrl = `${window.location.pathname}${params.toString() ? '?' + params.toString() : ''}`
    window.history.replaceState({}, '', newUrl)
    setShowInsightsMenu(false)
  }

  const navButton = (id, label) => {
    const isActive = currentPage === id
    return (
      <button
        onClick={() => navigateToPage(id)}
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

  const insightsSubLabel =
    currentPage === 'wordDemo'
      ? t('词汇')
      : currentPage === 'grammarDemo'
        ? t('语法')
        : ''

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

  if (isAuthCallbackPage) {
    return <AuthCallbackPage />
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
                  className="inline-flex items-center gap-2 text-xl font-bold leading-none text-gray-900 focus:outline-none focus-visible:ring-2 rounded"
                  style={{ '--tw-ring-color': colors.primary[300] }}
                >
                  <img
                    src="/linktext-header-ellipse.svg"
                    alt="LinkText"
                    className="h-8 w-8 shrink-0"
                  />
                  <span className="leading-none">{t('语言学习应用')}</span>
                </button>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:items-center sm:space-x-4">
                {navButton('article', t('阅读'))}
                <div className="h-5 w-px bg-gray-300" />
                <div ref={insightsMenuRef} className="relative flex items-center">
                  <button
                    type="button"
                    onClick={() => setShowInsightsMenu((prev) => !prev)}
                    className="inline-flex items-center gap-1 px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                    style={{
                      borderColor:
                        currentPage === 'wordDemo' || currentPage === 'grammarDemo'
                          ? colors.primary[600]
                          : 'transparent',
                      color:
                        currentPage === 'wordDemo' || currentPage === 'grammarDemo'
                          ? colors.semantic?.text?.primary ?? '#111827'
                          : colors.semantic?.text?.secondary ?? '#6b7280',
                    }}
                  >
                    <span key={uiLanguage}>{t('知识点')}</span>
                    {insightsSubLabel && (
                      <span className="ml-2 text-sm font-normal text-gray-900">
                        {insightsSubLabel}
                      </span>
                    )}
                    <svg
                      className={`h-4 w-4 transition-transform ${showInsightsMenu ? 'rotate-180' : ''}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {showInsightsMenu && (
                    <div className="absolute left-0 top-full mt-2 min-w-[160px] rounded-md border border-gray-200 bg-white py-1 shadow-lg z-20">
                      <button
                        type="button"
                        onClick={() => navigateToPage('wordDemo')}
                        className={`block w-full px-4 py-2 text-left text-sm ${
                          currentPage === 'wordDemo'
                            ? 'bg-green-50 text-green-800'
                            : 'text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {t('词汇')}
                      </button>
                      <button
                        type="button"
                        onClick={() => navigateToPage('grammarDemo')}
                        className={`block w-full px-4 py-2 text-left text-sm ${
                          currentPage === 'grammarDemo'
                            ? 'bg-green-50 text-green-800'
                            : 'text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {t('语法')}
                      </button>
                    </div>
                  )}
                </div>
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
                        const canRemove = headerLanguages.length > 1
                        return (
                          <div
                            key={lang}
                            className={[
                              'group flex items-center w-full',
                              isActiveLang ? 'bg-green-50' : 'hover:bg-gray-50',
                            ].join(' ')}
                          >
                            <button
                              type="button"
                              onClick={() => {
                                applyHeaderLanguageSelection(lang)
                              }}
                              className={[
                                'flex-1 flex items-center justify-between px-3 py-2 text-xs sm:text-sm text-left min-w-0',
                                isActiveLang ? 'text-green-800' : 'text-gray-700',
                              ].join(' ')}
                            >
                              <span className="truncate">{t(lang) || lang}</span>
                              {isActiveLang && (
                                <svg
                                  className="w-4 h-4 shrink-0 text-green-600 ml-2"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              )}
                            </button>
                            {canRemove && (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  removeHeaderLanguage(lang)
                                }}
                                className="group/remove shrink-0 mr-1 py-2 opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100"
                                aria-label={t('从正在学习中移除') || '从正在学习中移除'}
                                title={t('从正在学习中移除') || '从正在学习中移除'}
                              >
                                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-gray-200/90 transition-colors group-hover/remove:bg-red-500/25">
                                  <span
                                    className="block w-2 h-px bg-gray-400 rounded-full transition-all group-hover/remove:w-2.5 group-hover/remove:h-0.5 group-hover/remove:bg-red-500"
                                    aria-hidden
                                  />
                                </span>
                              </button>
                            )}
                          </div>
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
                                  await applyHeaderLanguageSelection(lang, updated)
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
                  <CreditsIndicator
                    tokenBalance={userInfo?.token_balance}
                    role={userInfo?.role}
                  />
                  <UserAvatar 
                    userId={currentUserId}
                    email={currentUserEmail}
                    onLogout={handleLogout}
                    onOpenProfile={() => setShowProfilePage(true)}
                  />
                </>
              ) : (
                <LoginButton key={uiLanguage} onClick={() => setShowAuthModal(true)} />
              )}
            </div>
          </div>
        </div>
      </div>

      <MagicLinkAuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />

      {showWelcomeCredits && (
        <WelcomeCreditsBanner onDismiss={handleDismissWelcomeCredits} />
      )}

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
                onContinue={() => setShowAuthModal(true)}
              />
            </div>
          )}

          {currentPage === 'onboardingLanguage' && (
            <OnboardingLanguage
              onContinue={async (selectedCode) => {
                const languageName = LANGUAGE_CODE_TO_NAME[selectedCode]
                if (languageName) {
                  persistHeaderLanguages([languageName])
                  setSelectedLanguageWithoutArticleReset(languageName)
                }
                if (token) {
                  try {
                    await refreshUserInfo(token, { force: true })
                  } catch {
                    // ignore
                  }
                }
                setCurrentPage('onboardingReading')
              }}
            />
          )}

          {currentPage === 'onboardingReading' && (
            <OnboardingReadingIntro
              onStartReading={(articleId) => {
                if (currentUserId) {
                  completeOnboarding(currentUserId)
                }
                setIsUploadMode(false)
                if (articleId) {
                  setSelectedArticleId(articleId)
                } else {
                  setSelectedArticleId(null)
                }
                setCurrentPage('article')
              }}
              onUploadOwn={() => {
                if (currentUserId) {
                  completeOnboarding(currentUserId)
                }
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
                      setSelectedLanguageWithoutArticleReset(uploadLanguage)
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
          {currentPage === 'chatConcurrencySandbox' && <ChatConcurrencySandbox />}

          {currentPage === 'articleUploadSandbox' && (
            <ArticleUploadSandbox
              onBack={() => {
                setCurrentPage('landing')
              }}
              onNavigateToArticle={(id) => {
                if (!id) return
                setIsUploadMode(false)
                setSelectedArticleId(id)
                setCurrentPage('article')
              }}
            />
          )}

          {currentPage === 'articleViewSandbox' && (
            <ArticleViewSandbox
              onBack={() => {
                setCurrentPage('landing')
              }}
            />
          )}

          {currentPage === 'furiganaSandbox' && (
            <FuriganaSandbox
              onBack={() => {
                setCurrentPage('landing')
              }}
            />
          )}

          {currentPage === 'chineseZhuyinSandbox' && (
            <ChineseZhuyinSandbox
              onBack={() => {
                setCurrentPage('landing')
              }}
            />
          )}
        </div>
      </div>
    </div>
  )
}

// 使用 UserProvider 和 LanguageProvider 包装 AppContent
function App() {
  if (typeof window !== 'undefined' && isBillingSandboxPath(window.location.pathname)) {
    return <BillingSandboxRoutes />
  }

  if (typeof window !== 'undefined' && isUISandboxPath(window.location.pathname)) {
    return <UISandboxRoutes />
  }

  return (
    <UserProvider>
      <LanguageProvider>
        <UiLanguageProvider>
          <BillingProvider>
            <AppContent />
          </BillingProvider>
        </UiLanguageProvider>
      </LanguageProvider>
    </UserProvider>
  )
}

export default App


