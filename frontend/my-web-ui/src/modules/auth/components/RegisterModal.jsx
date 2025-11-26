/**
 * 注册模态框
 * 显示注册表单
 */
import { useState, useEffect } from 'react'
import { useUser } from '../../../contexts/UserContext'
import { authService } from '../services/authService'
import { useTranslate } from '../../../i18n/useTranslate'

const RegisterModal = ({ isOpen, onClose, onSwitchToLogin }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [registeredUserId, setRegisteredUserId] = useState(null)
  const [emailUnique, setEmailUnique] = useState(null) // null: 未检查, true: 唯一, false: 不唯一
  const [emailCheckMessage, setEmailCheckMessage] = useState('')
  const [isCheckingEmail, setIsCheckingEmail] = useState(false)
  const t = useTranslate()
  
  // 从 UserContext 获取注册方法
  const { register } = useUser()

  // 检查邮箱唯一性（debounce）
  useEffect(() => {
    if (!email || email.trim() === '') {
      setEmailUnique(null)
      setEmailCheckMessage('')
      return
    }

    // 简单的邮箱格式验证
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      setEmailUnique(null)
      setEmailCheckMessage('')
      return
    }

    const timer = setTimeout(async () => {
      setIsCheckingEmail(true)
      try {
        const result = await authService.checkEmailUnique(email)
        setEmailUnique(result.unique)
        setEmailCheckMessage(result.message)
      } catch (error) {
        console.error('检查邮箱唯一性失败:', error)
        setEmailUnique(null)
        setEmailCheckMessage(t('检查失败') || '检查失败')
      } finally {
        setIsCheckingEmail(false)
      }
    }, 500) // 500ms debounce

    return () => clearTimeout(timer)
  }, [email])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // 验证邮箱
    if (!email || email.trim() === '') {
      setError(t('请输入邮箱地址'))
      return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      setError(t('请输入有效的邮箱地址'))
      return
    }

    // 验证密码
    if (password.length < 6) {
      setError(t('密码长度至少为6位'))
      return
    }

    if (password !== confirmPassword) {
      setError(t('两次输入的密码不一致'))
      return
    }

    setIsLoading(true)

    try {
      console.log('📝 [Register] Attempting registration', { email })
      
      // 使用 UserContext 的 register 方法
      const result = await register(password, email)
      
      if (result.success) {
        console.log('✅ [Register] Registration successful')
        
        // 显示成功页面（会显示用户ID）
        setRegisteredUserId(result.userId)
      } else {
        setError(result.error)
      }
    } catch (error) {
      console.error('❌ [Register] Registration failed:', error)
      setError(t('注册失败，请重试'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleCloseSuccess = () => {
    // 关闭成功页面
    setRegisteredUserId(null)
    setEmail('')
    setPassword('')
    setConfirmPassword('')
    setEmailUnique(null)
    setEmailCheckMessage('')
    onClose()
    
    // 可选：由于已经自动保存了 token，可以直接通知父组件更新登录状态
    // 这样用户注册后就直接处于登录状态，无需再次登录
  }

  if (!isOpen) return null

  // 注册成功页面
  if (registeredUserId) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
          {/* 成功图标 */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('注册成功！')}</h2>
            <p className="text-gray-600 mb-4">{t('您的账号已创建')}</p>
          </div>

          {/* 用户ID显示 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-600 mb-2">{t('请记住您的用户 ID（登录时需要）')}</p>
            <div className="flex items-center justify-center space-x-2">
              <span className="text-sm text-gray-500">{t('用户 ID:')}</span>
              <span className="text-2xl font-bold text-blue-600">{registeredUserId}</span>
            </div>
          </div>

          {/* 按钮 */}
          <div className="flex flex-col space-y-3">
            <button
              onClick={handleCloseSuccess}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors font-medium"
            >
              {t('开始使用')}
            </button>
            <button
              onClick={() => {
                handleCloseSuccess()
                onSwitchToLogin()
              }}
              className="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors font-medium"
            >
              {t('前往登录')}
            </button>
          </div>
          
          <div className="mt-4 text-center">
            <p className="text-xs text-gray-500">{t('💡 提示：已自动登录，点击"开始使用"即可体验')}</p>
          </div>
        </div>
      </div>
    )
  }

  // 注册表单
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        {/* 标题 */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">{t('注册')}</h2>
          <p className="text-sm text-gray-600 mt-1">{t('创建新账号开始学习')}</p>
        </div>

        {/* 注册表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 邮箱 */}
          <div>
            <label htmlFor="reg-email" className="block text-sm font-medium text-gray-700 mb-1">
              {t('邮箱')} <span className="text-red-500">＊</span>
            </label>
            <input
              type="email"
              id="reg-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                emailUnique === false ? 'border-red-300' : 
                emailUnique === true ? 'border-green-300' : 
                'border-gray-300'
              }`}
              placeholder={t('请输入邮箱地址')}
              required
            />
            {/* Debug UI: 邮箱唯一性检查结果 */}
            {email && email.trim() !== '' && (
              <div className="mt-1">
                {isCheckingEmail ? (
                  <p className="text-xs text-gray-500">{t('检查中...')}</p>
                ) : emailUnique === true ? (
                  <p className="text-xs text-green-600">{t('✅ 邮箱可用')}</p>
                ) : emailUnique === false ? (
                  <p className="text-xs text-red-600">{t('❌ 邮箱已被使用（开发阶段仍可注册）')}</p>
                ) : emailCheckMessage ? (
                  <p className="text-xs text-gray-500">{emailCheckMessage}</p>
                ) : null}
              </div>
            )}
          </div>

          {/* 密码 */}
          <div>
            <label htmlFor="reg-password" className="block text-sm font-medium text-gray-700 mb-1">
              {t('密码')}
            </label>
            <input
              type="password"
              id="reg-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={t('请输入密码（至少6位）')}
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
              placeholder={t('请再次输入密码')}
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

          {/* 提示信息 */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
            <p className="text-xs text-gray-600">{t('💡 注册成功后，系统会自动分配一个用户 ID，请记住它用于登录。')}</p>
          </div>

          {/* 按钮组 */}
          <div className="flex flex-col space-y-3 pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {isLoading ? t('注册中...') : t('注册')}
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

        {/* 登录提示 */}
        <div className="mt-6 text-center border-t border-gray-200 pt-4">
          <p className="text-sm text-gray-600">
            {t('已有账号？')}{' '}
            <button
              onClick={onSwitchToLogin}
              className="text-blue-500 hover:text-blue-600 font-medium"
            >
              {t('立即登录')}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default RegisterModal

