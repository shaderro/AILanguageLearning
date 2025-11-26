/**
 * 重置密码页面
 * 从 URL 参数获取 token，用户输入新密码
 */
import { useState, useEffect } from 'react'
import { authService } from '../services/authService'
import { useTranslate } from '../../../i18n/useTranslate'

const ResetPasswordPage = ({ onBackToLogin }) => {
  const [token, setToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const t = useTranslate()

  // 从 URL 参数获取 token
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const tokenFromUrl = params.get('token')
    if (tokenFromUrl) {
      setToken(tokenFromUrl)
    } else {
      setError(t('缺少重置 token，请使用有效的重置链接'))
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

    if (!token) {
      setError(t('缺少重置 token'))
      return
    }

    setIsLoading(true)

    try {
      console.log('🔐 [ResetPassword] 重置密码中...')
      
      const result = await authService.resetPassword(token, newPassword)
      
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
          <p className="text-sm text-gray-600 mt-1">{t('请输入您的新密码')}</p>
        </div>

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
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
              disabled={isLoading || !token}
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

