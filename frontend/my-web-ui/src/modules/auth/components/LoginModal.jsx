/**
 * 登录模态框
 * 显示登录表单
 */
import { useState } from 'react'
import { useUser } from '../../../contexts/UserContext'
import { useTranslate } from '../../../i18n/useTranslate'

const LoginModal = ({ isOpen, onClose, onSwitchToRegister, onSwitchToForgotPassword }) => {
  const [userId, setUserId] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const t = useTranslate()
  
  // 从 UserContext 获取登录方法
  const { login } = useUser()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    // 验证：至少提供 user_id 或 email 之一
    if (!userId && !email) {
      setError(t('请提供用户ID或邮箱'))
      return
    }

    setIsLoading(true)

    try {
      const userIdInt = userId ? parseInt(userId) : null
      console.log('🔐 [Login] Attempting login:', { 
        userId: userIdInt, 
        email: email || null,
        passwordLength: password.length 
      })
      
      // 使用 UserContext 的 login 方法
      const result = await login(userIdInt, password, email || null)
      
      if (result.success) {
        console.log('✅ [Login] Login successful')
        
        // 关闭模态框
        onClose()
        
        // 清空表单
        setUserId('')
        setEmail('')
        setPassword('')
      } else {
        // 显示错误
        setError(result.error)
      }
    } catch (error) {
      console.error('❌ [Login] Login failed:', error)
      setError(t('登录失败，请重试'))
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        {/* 标题 */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">{t('登录')}</h2>
          <p className="text-sm text-gray-600 mt-1">{t('欢迎回来！请登录您的账号')}</p>
        </div>

        {/* 登录表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 用户ID */}
          <div>
            <label htmlFor="userId" className="block text-sm font-medium text-gray-700 mb-1">
              {t('用户 ID')} <span className="text-gray-400 text-xs">{t('(可选)')}</span>
            </label>
            <input
              type="number"
              id="userId"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={t('请输入您的用户ID（可选）')}
            />
          </div>

          {/* 邮箱 */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              {t('邮箱')} <span className="text-gray-400 text-xs">{t('(可选)')}</span>
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={t('请输入邮箱（可选，已注册用户可留空）')}
            />
            <p className="text-xs text-gray-500 mt-1">
              {t('💡 提示：至少提供用户ID或邮箱之一')}
            </p>
          </div>

          {/* 密码 */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                {t('密码')}
              </label>
              {onSwitchToForgotPassword && (
                <button
                  type="button"
                  onClick={onSwitchToForgotPassword}
                  className="text-sm text-blue-500 hover:text-blue-600 font-medium"
                >
                  {t('忘记密码？')}
                </button>
              )}
            </div>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={t('请输入密码')}
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
              disabled={isLoading}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {isLoading ? t('登录中...') : t('登录')}
            </button>

            <button
              type="button"
              onClick={onClose}
              className="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors font-medium"
            >
              {t('取消')}
            </button>
          </div>
        </form>

        {/* 注册提示 */}
        <div className="mt-6 text-center border-t border-gray-200 pt-4">
          <p className="text-sm text-gray-600">
            {t('还没有账号？')}{' '}
            <button
              onClick={onSwitchToRegister}
              className="text-blue-500 hover:text-blue-600 font-medium"
            >
              {t('立即注册')}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginModal

