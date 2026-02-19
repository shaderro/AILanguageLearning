/**
 * 登录模态框
 * 显示登录表单
 */
import { useState } from 'react'
import { useUser } from '../../../contexts/UserContext'
import { useTranslate } from '../../../i18n/useTranslate'
import { BaseModal, BaseInput, BaseButton } from '../../../components/base'

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
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title={t('登录')}
      subtitle={t('欢迎回来！请登录您的账号')}
      size="sm"
      closeOnOverlay={false}
      closeOnEscape={false}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <BaseInput
          label={
            <span>
              {t('邮箱')} <span className="text-xs text-gray-400">{t('(推荐)')}</span>
            </span>
          }
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t('请输入邮箱')}
          helperText={t('💡 提示：推荐使用邮箱登录')}
        />

        <BaseInput
          label={
            <span>
              {t('用户 ID')} <span className="text-xs text-orange-500 font-medium">{t('(仅内部测试用)')}</span>
            </span>
          }
          type="number"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder={t('请输入用户ID（仅内部测试用）')}
          helperText={t('⚠️ 仅用于测试用户（无邮箱账号），普通用户请使用邮箱登录')}
        />

        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">{t('密码')}</span>
            {onSwitchToForgotPassword && (
              <button
                type="button"
                onClick={onSwitchToForgotPassword}
                className="text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                {t('忘记密码？')}
              </button>
            )}
          </div>
          <BaseInput
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('请输入密码')}
            required
            minLength={6}
          />
        </div>

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="flex flex-col space-y-3 pt-2">
          <BaseButton type="submit" loading={isLoading} fullWidth>
            {isLoading ? t('登录中...') : t('登录')}
          </BaseButton>
          <BaseButton type="button" variant="secondary" onClick={onClose} fullWidth>
            {t('取消')}
          </BaseButton>
        </div>
      </form>

      <div className="mt-6 border-t border-gray-200 pt-4 text-center">
        <p className="text-sm text-gray-600">
          {t('还没有账号？')}{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="text-primary-600 hover:text-primary-700"
          >
            {t('立即注册')}
          </button>
        </p>
      </div>
    </BaseModal>
  )
}

export default LoginModal

