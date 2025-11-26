/**
 * 忘记密码模态框
 * 用户输入邮箱或用户ID，生成重置链接
 */
import { useState } from 'react'
import { authService } from '../services/authService'
import { useTranslate } from '../../../i18n/useTranslate'

const ForgotPasswordModal = ({ isOpen, onClose, onSwitchToLogin }) => {
  const [email, setEmail] = useState('')
  const [userId, setUserId] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const t = useTranslate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    // 验证：至少提供 email 或 user_id 之一
    if (!email && !userId) {
      setError(t('请提供邮箱或用户ID'))
      return
    }

    setIsLoading(true)

    try {
      const userIdInt = userId ? parseInt(userId) : null
      console.log('🔐 [ForgotPassword] 请求重置链接:', { email: email || null, userId: userIdInt })
      
      const result = await authService.forgotPassword(email || null, userIdInt)
      
      if (result.success && result.reset_link) {
        console.log('✅ [ForgotPassword] 重置链接生成成功，直接跳转')
        // 开发模式：直接跳转到重置密码页面，不显示链接
        window.location.href = result.reset_link
      } else {
        setError(result.message || t('生成重置链接失败'))
        setIsLoading(false)
      }
    } catch (error) {
      console.error('❌ [ForgotPassword] 生成重置链接失败:', error)
      setError(error.response?.data?.detail || error.message || t('生成重置链接失败，请重试'))
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    setEmail('')
    setUserId('')
    setError('')
    onClose()
  }

  if (!isOpen) return null

  // 输入表单
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        {/* 标题 */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">{t('忘记密码')}</h2>
          <p className="text-sm text-gray-600 mt-1">{t('请输入您的邮箱或用户ID以生成重置链接')}</p>
        </div>

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 邮箱 */}
          <div>
            <label htmlFor="forgot-email" className="block text-sm font-medium text-gray-700 mb-1">
              {t('邮箱')} <span className="text-gray-400 text-xs">{t('(可选)')}</span>
            </label>
            <input
              type="email"
              id="forgot-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={t('请输入邮箱（可选）')}
            />
          </div>

          {/* 用户ID */}
          <div>
            <label htmlFor="forgot-userId" className="block text-sm font-medium text-gray-700 mb-1">
              {t('用户 ID')} <span className="text-gray-400 text-xs">{t('(可选)')}</span>
            </label>
            <input
              type="number"
              id="forgot-userId"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={t('请输入用户ID（可选）')}
            />
            <p className="text-xs text-gray-500 mt-1">
              {t('💡 提示：至少提供邮箱或用户ID之一')}
            </p>
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
              disabled={isLoading}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {isLoading ? t('生成中...') : t('生成重置链接')}
            </button>

            <button
              type="button"
              onClick={handleClose}
              className="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors font-medium"
            >
              {t('取消')}
            </button>
          </div>
        </form>

        {/* 登录提示 */}
        <div className="mt-6 text-center border-t border-gray-200 pt-4">
          <p className="text-sm text-gray-600">
            {t('想起密码了？')}{' '}
            <button
              onClick={() => {
                handleClose()
                onSwitchToLogin()
              }}
              className="text-blue-500 hover:text-blue-600 font-medium"
            >
              {t('返回登录')}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default ForgotPasswordModal

