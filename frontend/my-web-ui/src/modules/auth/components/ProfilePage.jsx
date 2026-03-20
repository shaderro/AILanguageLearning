/**
 * 个人中心页面
 * 包含账号信息、设置、安全与隐私等
 */
import { useState, useEffect, useRef } from 'react'
import { authService } from '../services/authService'
import { useUser } from '../../../contexts/UserContext'
import { useLanguage, languageNameToCode } from '../../../contexts/LanguageContext'
import { useUiLanguage } from '../../../contexts/UiLanguageContext'
import ChangePasswordModal from './ChangePasswordModal'

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
    changePasswordAlert: '修改密码功能待实现',
    tokensManagement: 'Token 管理',
    currentPoints: '当前积分',
    inviteCode: '邀请码',
    enterInviteCode: '请输入邀请码',
    internalTestingOnly: '(仅内部测试用)',
    redeem: '兑换',
    redeeming: '兑换中...',
    redeemSuccess: '兑换成功',
    redeemError: '兑换失败',
    invalidCode: '邀请码无效、已使用或已过期'
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
    changePasswordAlert: 'Password change feature is under construction',
    tokensManagement: 'Tokens Management',
    currentPoints: 'Current Points',
    inviteCode: 'Invite Code',
    enterInviteCode: 'Enter invite code',
    internalTestingOnly: '(Internal testing only)',
    redeem: 'Redeem',
    redeeming: 'Redeeming...',
    redeemSuccess: 'Redeem successful',
    redeemError: 'Redeem failed',
    invalidCode: 'Invalid, used, or expired invite code'
  }
}

import { convertTokensToPoints } from '../../../utils/tokenUtils'

// 内容语言候选（UI 展示用，内部仍兼容“英语/德语”等旧值）
const ALL_LANGUAGES = ['中文', '英文', '西班牙语', '法语', '日语', '韩语', '德文', '阿拉伯语', '俄语']

const getLanguageStorageKey = (userId) => {
  const id = userId || 'guest'
  return `content_languages_chosen_${id}`
}

const ProfilePage = ({ onClose, onLogout }) => {
  const { userId, email, token } = useUser() // 🔧 添加 email
  const { selectedLanguage, setSelectedLanguage } = useLanguage()
  const { uiLanguage, setUiLanguage } = useUiLanguage()
  const [userInfo, setUserInfo] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [isRedeeming, setIsRedeeming] = useState(false)
  const [redeemMessage, setRedeemMessage] = useState('')
  const [isChangePasswordModalOpen, setIsChangePasswordModalOpen] = useState(false)
  const [showLanguageMenu, setShowLanguageMenu] = useState(false)
  const syncTimeoutRef = useRef(null)
  const lastPayloadRef = useRef(null)
  const [chosenLanguages, setChosenLanguages] = useState(() => {
    const initial = selectedLanguage ? [selectedLanguage] : ['德文']
    if (typeof window === 'undefined') {
      return initial
    }
    try {
      const key = getLanguageStorageKey(userId)
      const raw = window.localStorage.getItem(key)
      if (!raw) return initial
      const parsed = JSON.parse(raw)
      if (!Array.isArray(parsed)) return initial
      const valid = parsed.filter((lang) => ALL_LANGUAGES.includes(lang))
      return Array.from(new Set([...initial, ...valid]))
    } catch {
      return initial
    }
  })
  const t = profileTexts[uiLanguage] || profileTexts.zh

  // 持久化已选择语言列表（按用户维度）
  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      const key = getLanguageStorageKey(userId)
      window.localStorage.setItem(key, JSON.stringify(chosenLanguages))
    } catch {
      // ignore
    }
  }, [chosenLanguages, userId])

  // 同步语言偏好到后端（UI 语言 + 内容语言 + 已添加列表）
  useEffect(() => {
    if (!token || !userId) return

    const languagesCodes = chosenLanguages.map((name) => languageNameToCode(name))
    const currentCode = selectedLanguage ? languageNameToCode(selectedLanguage) : null
    const payload = {
      ui_language: uiLanguage,
      content_language: currentCode,
      languages_list: languagesCodes,
    }

    const canonical = JSON.stringify(payload)

    // 如果与上次成功同步的内容一致，则不再发送
    if (lastPayloadRef.current && lastPayloadRef.current === canonical) {
      return
    }

    // 节流：清除上一个未触发的定时器
    if (syncTimeoutRef.current) {
      clearTimeout(syncTimeoutRef.current)
    }

    syncTimeoutRef.current = setTimeout(async () => {
      try {
        await authService.updatePreferences(payload)
        lastPayloadRef.current = canonical
        if (typeof window !== 'undefined') {
          try {
            localStorage.removeItem(`prefs_dirty_${userId}`)
          } catch {
            // ignore
          }
        }
      } catch (e) {
        console.warn('⚠️ [ProfilePage] 同步语言偏好到后端失败:', e)
        if (typeof window !== 'undefined') {
          try {
            localStorage.setItem(`prefs_dirty_${userId}`, '1')
          } catch {
            // ignore
          }
        }
      }
    }, 500)

    return () => {
      if (syncTimeoutRef.current) {
        clearTimeout(syncTimeoutRef.current)
        syncTimeoutRef.current = null
      }
    }
  }, [chosenLanguages, selectedLanguage, uiLanguage, token, userId])

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
    setIsChangePasswordModalOpen(true)
  }

  const handleRedeemInviteCode = async () => {
    if (!inviteCode.trim()) {
      setRedeemMessage(t.invalidCode)
      return
    }

    setIsRedeeming(true)
    setRedeemMessage('')

    try {
      const result = await authService.redeemInviteCode(inviteCode.trim())
      if (result.success) {
        setRedeemMessage(t.redeemSuccess + `: ${result.message || ''}`)
        setInviteCode('')
        // 刷新用户信息以更新 token 余额
        const updatedInfo = await authService.getCurrentUser(token)
        setUserInfo(updatedInfo)
      } else {
        setRedeemMessage(t.redeemError + ': ' + (result.message || t.invalidCode))
      }
    } catch (err) {
      console.error('兑换邀请码失败:', err)
      const errorMsg = err.response?.data?.detail || err.message || t.invalidCode
      setRedeemMessage(t.redeemError + ': ' + errorMsg)
    } finally {
      setIsRedeeming(false)
    }
  }

  const getLanguageLabel = (lang) => {
    if (uiLanguage === 'en') {
      if (lang === '中文') return 'Chinese'
      if (lang === '英文') return 'English'
      if (lang === '英语') return 'English'
      if (lang === '德文') return 'German'
      if (lang === '德语') return 'German'
      if (lang === '西班牙语') return 'Spanish'
      if (lang === '法语') return 'French'
      if (lang === '日语') return 'Japanese'
      if (lang === '韩语') return 'Korean'
      if (lang === '阿拉伯语') return 'Arabic'
      if (lang === '俄语') return 'Russian'
    }
    return lang
  }

  const handleSelectLanguage = (lang) => {
    setSelectedLanguage(lang)
    if (!chosenLanguages.includes(lang)) {
      setChosenLanguages((prev) => [...prev, lang])
    }
    setShowLanguageMenu(false)
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

              {/* 用户ID（仅测试账号显示） */}
              {!email && userId && (
                <div className="flex items-center justify-between py-2 border-b border-gray-100">
                  <div>
                    <label className="text-sm font-medium text-gray-500">
                      {t.userId} <span className="text-xs text-orange-500">{t.internalTestingOnly}</span>
                    </label>
                    <p className="text-sm text-gray-900 mt-1">{userId}</p>
                  </div>
                  <span className="text-xs text-gray-400">{t.displayOnly}</span>
                </div>
              )}

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
                <div className="flex items-center gap-2">
                  {/* 已选择语言列表 */}
                  <div className="flex items-center gap-2">
                    {chosenLanguages.map((lang) => {
                      const isActive = lang === selectedLanguage
                      return (
                        <button
                          key={lang}
                          type="button"
                          onClick={() => handleSelectLanguage(lang)}
                          className={[
                            'px-3 py-1 rounded-full text-xs font-medium border transition-colors',
                            isActive
                              ? 'bg-green-100 text-green-800 border-green-300'
                              : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200',
                          ].join(' ')}
                        >
                          {getLanguageLabel(lang)}
                        </button>
                      )
                    })}
                  </div>

                  {/* 添加其它语言 */}
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setShowLanguageMenu((prev) => !prev)}
                      className="w-8 h-8 inline-flex items-center justify-center rounded-full border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 text-lg leading-none"
                    >
                      +
                    </button>
                    {showLanguageMenu && (
                      <div className="absolute right-0 mt-2 w-32 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                        {ALL_LANGUAGES.filter((lang) => !chosenLanguages.includes(lang)).length === 0 ? (
                          <div className="px-3 py-2 text-xs text-gray-400 text-center">
                            {uiLanguage === 'en' ? 'All added' : '已添加全部语言'}
                          </div>
                        ) : (
                          ALL_LANGUAGES.filter((lang) => !chosenLanguages.includes(lang)).map((lang) => (
                            <button
                              key={lang}
                              type="button"
                              onClick={() => handleSelectLanguage(lang)}
                              className="w-full px-3 py-2 text-left text-xs hover:bg-gray-50"
                            >
                              {getLanguageLabel(lang)}
                            </button>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                </div>
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

          {/* Token 管理 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t.tokensManagement}</h2>
            <div className="space-y-4">
              {/* 当前积分 */}
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <div>
                  <label className="text-sm font-medium text-gray-500">{t.currentPoints}</label>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {convertTokensToPoints(userInfo?.token_balance)}
                  </p>
                </div>
                <span className="text-xs text-gray-400">{t.displayOnly}</span>
              </div>

              {/* 邀请码兑换 */}
              <div className="pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t.inviteCode}
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={inviteCode}
                    onChange={(e) => {
                      setInviteCode(e.target.value)
                      setRedeemMessage('')
                    }}
                    placeholder={t.enterInviteCode}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={isRedeeming}
                  />
                  <button
                    onClick={handleRedeemInviteCode}
                    disabled={isRedeeming || !inviteCode.trim()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                  >
                    {isRedeeming ? t.redeeming : t.redeem}
                  </button>
                </div>
                {redeemMessage && (
                  <p className={`mt-2 text-sm ${redeemMessage.includes(t.redeemSuccess) ? 'text-green-600' : 'text-red-600'}`}>
                    {redeemMessage}
                  </p>
                )}
              </div>
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

      {/* 修改密码模态框 */}
      <ChangePasswordModal
        isOpen={isChangePasswordModalOpen}
        onClose={() => setIsChangePasswordModalOpen(false)}
        userId={userId}
        userEmail={email || userInfo?.email} // 🔧 优先使用 UserContext 的 email
      />
    </div>
  )
}

export default ProfilePage

