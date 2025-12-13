/**
 * 个人中心页面
 * 包含账号信息、设置、安全与隐私等
 */
import { useState, useEffect } from 'react'
import { authService } from '../services/authService'
import { useUser } from '../../../contexts/UserContext'
import { useLanguage } from '../../../contexts/LanguageContext'
import { useUiLanguage } from '../../../contexts/UiLanguageContext'

const profileTexts = {
  zh: {
    title: '个人中心与设置',
    accountInfo: '账号信息',
    email: '邮箱',
    userId: '用户 ID',
    password: '密码',
    resetPassword: '重置密码',
    displayOnly: '仅展示',
    notSet: '未设置',
    maskedPassword: '••••••••',
    settings: '设置',
    uiLanguageLabel: '界面语言',
    uiLanguageDesc: '仅影响 App UI 文案',
    dataLanguageLabel: '内容语言筛选',
    dataLanguageDesc: '控制文章/词汇语言过滤',
    notificationLabel: '通知设置',
    notificationDesc: '未来版本',
    placeholder: '占位',
    themeLabel: '主题',
    security: '安全与隐私',
    changePassword: '修改密码',
    membership: '会员中心',
    membershipDesc: '未来版本',
    about: '关于',
    help: '帮助与反馈',
    privacy: '隐私政策',
    terms: '服务条款',
    logout: '退出登录',
    logoutConfirm: '确定要退出登录吗？',
    loading: '加载中...',
    notLoggedIn: '未登录',
    fetchError: '获取用户信息失败',
    changePasswordAlert: '修改密码功能待实现'
  },
  en: {
    title: 'Profile & Settings',
    accountInfo: 'Account Information',
    email: 'Email',
    userId: 'User ID',
    password: 'Password',
    resetPassword: 'Reset Password',
    displayOnly: 'Display only',
    notSet: 'Not set',
    maskedPassword: '••••••••',
    settings: 'Settings',
    uiLanguageLabel: 'UI Language',
    uiLanguageDesc: 'Affects interface copy only',
    dataLanguageLabel: 'Content Language Filter',
    dataLanguageDesc: 'Filters articles/vocabulary by language',
    notificationLabel: 'Notifications',
    notificationDesc: 'Coming soon',
    placeholder: 'Placeholder',
    themeLabel: 'Theme',
    security: 'Security & Privacy',
    changePassword: 'Change Password',
    membership: 'Membership',
    membershipDesc: 'Coming soon',
    about: 'About',
    help: 'Help & Feedback',
    privacy: 'Privacy Policy',
    terms: 'Terms of Service',
    logout: 'Sign Out',
    logoutConfirm: 'Are you sure you want to sign out?',
    loading: 'Loading...',
    notLoggedIn: 'Not signed in',
    fetchError: 'Failed to load profile',
    changePasswordAlert: 'Password change feature is under construction'
  }
}

const ProfilePage = ({ onClose, onLogout }) => {
  const { userId, token } = useUser()
  const { selectedLanguage, setSelectedLanguage } = useLanguage()
  const { uiLanguage, setUiLanguage } = useUiLanguage()
  const [userInfo, setUserInfo] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const t = profileTexts[uiLanguage] || profileTexts.zh

  // 获取用户信息
  useEffect(() => {
    const fetchUserInfo = async () => {
      if (!token) {
        setError(t.notLoggedIn)
        setIsLoading(false)
        return
      }

      try {
        const info = await authService.getCurrentUser(token)
        setUserInfo(info)
      } catch (err) {
        console.error('获取用户信息失败:', err)
        setError(t.fetchError)
      } finally {
        setIsLoading(false)
      }
    }

    fetchUserInfo()
  }, [token, t.fetchError, t.notLoggedIn])

  const handleChangePassword = () => {
    // TODO: 打开修改密码对话框或跳转到修改密码页面
    alert(t.changePasswordAlert)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-gray-600">{t.loading}</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-red-600">{error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* 顶部导航栏 */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">{t.title}</h1>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* 账号信息 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t.accountInfo}</h2>
            <div className="space-y-4">
              {/* 邮箱 */}
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <div>
                  <label className="text-sm font-medium text-gray-500">{t.email}</label>
                  <p className="text-sm text-gray-900 mt-1">
                    {userInfo?.email || t.notSet}
                  </p>
                </div>
                <span className="text-xs text-gray-400">{t.displayOnly}</span>
              </div>

              {/* 用户ID */}
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <div>
                  <label className="text-sm font-medium text-gray-500">{t.userId}</label>
                  <p className="text-sm text-gray-900 mt-1">{userId}</p>
                </div>
                <span className="text-xs text-gray-400">{t.displayOnly}</span>
              </div>

              {/* 密码 */}
              <div className="flex items-center justify-between py-2">
                <div>
                  <label className="text-sm font-medium text-gray-500">{t.password}</label>
                  <p className="text-sm text-gray-900 mt-1">{t.maskedPassword}</p>
                </div>
                <button
                  onClick={handleChangePassword}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  {t.resetPassword}
                </button>
              </div>
            </div>
          </div>

          {/* 设置 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t.settings}</h2>
            <div className="space-y-4">
              {/* UI Language */}
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <div>
                  <label className="text-sm font-medium text-gray-500">{t.uiLanguageLabel}</label>
                  <p className="text-xs text-gray-400 mt-1">{t.uiLanguageDesc}</p>
                </div>
                <select
                  value={uiLanguage}
                  onChange={(e) => setUiLanguage(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="zh">中文 (ZH)</option>
                  <option value="en">English (EN)</option>
                </select>
              </div>

              {/* Content language */}
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <div>
                  <label className="text-sm font-medium text-gray-500">{t.dataLanguageLabel}</label>
                  <p className="text-xs text-gray-400 mt-1">{t.dataLanguageDesc}</p>
                </div>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="中文">{uiLanguage === 'en' ? 'Chinese' : '中文'}</option>
                  <option value="英文">{uiLanguage === 'en' ? 'English' : '英文'}</option>
                  <option value="德文">{uiLanguage === 'en' ? 'German' : '德文'}</option>
                </select>
              </div>

              {/* Notifications */}
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <div>
                  <label className="text-sm font-medium text-gray-500">{t.notificationLabel}</label>
                  <p className="text-xs text-gray-400 mt-1">{t.notificationDesc}</p>
                </div>
                <span className="text-xs text-gray-400">{t.placeholder}</span>
              </div>

              {/* Theme */}
              <div className="flex items-center justify-between py-2">
                <div>
                  <label className="text-sm font-medium text-gray-500">{t.themeLabel}</label>
                  <p className="text-xs text-gray-400 mt-1">{t.notificationDesc}</p>
                </div>
                <span className="text-xs text-gray-400">{t.placeholder}</span>
              </div>
            </div>
          </div>

          {/* 安全与隐私 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t.security}</h2>
            <div className="space-y-4">
              <button
                onClick={handleChangePassword}
                className="w-full text-left px-4 py-3 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    <span className="text-sm font-medium text-gray-700">{t.changePassword}</span>
                  </div>
                  <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            </div>
          </div>

          {/* 会员中心 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t.membership}</h2>
            <p className="text-sm text-gray-400">{t.membershipDesc}</p>
          </div>

          {/* 关于 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t.about}</h2>
            <div className="space-y-3">
              <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md transition-colors">
                {t.help}
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md transition-colors">
                {t.privacy}
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md transition-colors">
                {t.terms}
              </button>
            </div>
          </div>

          {/* 退出登录 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <button
              onClick={() => {
                if (window.confirm(t.logoutConfirm)) {
                  onLogout()
                  onClose()
                }
              }}
              className="w-full px-4 py-3 bg-red-50 text-red-600 rounded-md hover:bg-red-100 transition-colors font-medium"
            >
              {t.logout}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProfilePage

