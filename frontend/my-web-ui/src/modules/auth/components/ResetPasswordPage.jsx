/**
 * 重置密码页面
 * 从 URL 参数获取 token，用户输入新密码
 */
import { useState, useEffect } from 'react'
import { authService } from '../services/authService'
import { useTranslate } from '../../../i18n/useTranslate'

const ResetPasswordPage = ({ onBackToLogin }) => {
  const [token, setToken] = useState('')
  const [email, setEmail] = useState('')
  const [userId, setUserId] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [testMode, setTestMode] = useState(false) // 测试模式：无需token，直接输入user_id/email
  const t = useTranslate()

  // 从 URL 参数获取 token
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const tokenFromUrl = params.get('token')
    const testModeParam = params.get('test') === 'true' // 支持 ?test=true 参数启用测试模式
    
    if (testModeParam) {
      setTestMode(true)
    } else if (tokenFromUrl) {
      setToken(tokenFromUrl)
      setTestMode(false)
    } else {
      // 如果没有token也没有test参数，默认启用测试模式
      setTestMode(true)
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // 验证密码
    if (newPassword.length < 6) {
      setError(t('密码长度至少为6位'))
      return
    }

    if (newPassword !== confirmPassword) {
      setError(t('两次输入的密码不一致'))
      return
    }

    // 测试模式：需要 user_id 或 email
    if (testMode) {
      if (!email && !userId) {
        setError(t('请提供邮箱或用户ID'))
        return
      }
    } else {
      // 正常模式：需要 token
      if (!token) {
        setError(t('缺少重置 token'))
        return
      }
    }

    setIsLoading(true)

    try {
      console.log('🔐 [ResetPassword] 重置密码中...', { testMode, email, userId })
      
      let result
      if (testMode) {
        // 测试模式：直接重置密码
        const userIdInt = userId ? parseInt(userId) : null
        result = await authService.resetPasswordDirect(email || null, userIdInt, newPassword)
      } else {
        // 正常模式：使用 token
        result = await authService.resetPassword(token, newPassword)
      }
      
      if (result.success) {
        console.log('✅ [ResetPassword] 密码重置成功')
        setSuccess(true)
        // 3秒后跳转到登录页面
        setTimeout(() => {
          if (onBackToLogin) {
            onBackToLogin()
          } else {
            window.location.href = '/'
          }
        }, 3000)
      } else {
        setError(result.message || t('重置密码失败'))
      }
    } catch (error) {
      console.error('❌ [ResetPassword] 重置密码失败:', error)
      setError(error.response?.data?.detail || error.message || t('重置密码失败，请重试'))
    } finally {
      setIsLoading(false)
    }
  }

  // 成功页面
  if (success) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
          {/* 成功图标 */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('密码重置成功！')}</h2>
            <p className="text-gray-600 mb-4">{t('请使用新密码登录')}</p>
            <p className="text-sm text-gray-500">{t('3秒后自动跳转到登录页面...')}</p>
          </div>

          <button
            onClick={() => {
              if (onBackToLogin) {
                onBackToLogin()
              } else {
                window.location.href = '/'
              }
            }}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors font-medium"
          >
            {t('立即前往登录')}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
        {/* 标题 */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">{t('重置密码')}</h2>
          <p className="text-sm text-gray-600 mt-1">
            {testMode ? t('测试模式：请输入用户信息和新密码') : t('请输入您的新密码')}
          </p>
          {testMode && (
            <p className="text-xs text-yellow-600 mt-1 bg-yellow-50 px-2 py-1 rounded">
              ⚠️ {t('测试模式：无需token，直接输入用户ID或邮箱')}
            </p>
          )}
        </div>

        {/* 测试模式切换按钮 */}
        <div className="mb-4">
          <button
            type="button"
            onClick={() => setTestMode(!testMode)}
            className="text-xs text-blue-600 hover:text-blue-800 underline"
          >
            {testMode ? t('切换到正常模式（使用token）') : t('切换到测试模式（无需token）')}
          </button>
        </div>

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 测试模式：显示 user_id 和 email 输入框 */}
          {testMode && (
            <>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  {t('邮箱')} ({t('可选')})
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={t('请输入邮箱')}
                />
              </div>

              <div>
                <label htmlFor="user-id" className="block text-sm font-medium text-gray-700 mb-1">
                  {t('用户ID')} ({t('可选')})
                </label>
                <input
                  type="number"
                  id="user-id"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder={t('请输入用户ID')}
                />
                <p className="text-xs text-gray-500 mt-1">{t('至少需要提供邮箱或用户ID之一')}</p>
              </div>
            </>
          )}
          {/* 新密码 */}
          <div>
            <label htmlFor="new-password" className="block text-sm font-medium text-gray-700 mb-1">
              {t('新密码')}
            </label>
            <input
              type="password"
              id="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={t('请输入新密码（至少6位）')}
              required
              minLength={6}
            />
            <p className="text-xs text-gray-500 mt-1">{t('密码长度至少为6位')}</p>
          </div>

          {/* 确认密码 */}
          <div>
            <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700 mb-1">
              {t('确认密码')}
            </label>
            <input
              type="password"
              id="confirm-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={t('请再次输入新密码')}
              required
              minLength={6}
            />
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          {/* 按钮组 */}
          <div className="flex flex-col space-y-3 pt-2">
            <button
              type="submit"
              disabled={isLoading || (!testMode && !token) || (testMode && !email && !userId)}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {isLoading ? t('重置中...') : t('重置密码')}
            </button>

            <button
              type="button"
              onClick={() => {
                if (onBackToLogin) {
                  onBackToLogin()
                } else {
                  window.location.href = '/'
                }
              }}
              className="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors font-medium"
            >
              {t('返回登录')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ResetPasswordPage

