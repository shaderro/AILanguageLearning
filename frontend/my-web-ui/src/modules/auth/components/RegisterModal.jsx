/**
 * 注册模态框
 * 显示注册表单
 */
import { useState, useEffect } from 'react'
import { useUser } from '../../../contexts/UserContext'
import { authService } from '../services/authService'
import { useTranslate } from '../../../i18n/useTranslate'
import { BaseModal, BaseInput, BaseButton, BaseBadge } from '../../../components/base'

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

  if (registeredUserId) {
    return (
      <BaseModal
        isOpen={isOpen}
        onClose={handleCloseSuccess}
        title={t('注册成功！')}
        subtitle={t('您的账号已创建')}
        size="sm"
      >
        <div className="space-y-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
              <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-sm text-gray-600">{t('请记住您的用户 ID（登录时需要）')}</p>
            <BaseBadge variant="primary" size="lg">
              {t('用户 ID:')} {registeredUserId}
            </BaseBadge>
          </div>

          <div className="flex flex-col space-y-3">
            <BaseButton onClick={handleCloseSuccess} fullWidth>
              {t('开始使用')}
            </BaseButton>
            <BaseButton
              variant="secondary"
              fullWidth
              onClick={() => {
                handleCloseSuccess()
                onSwitchToLogin()
              }}
            >
              {t('前往登录')}
            </BaseButton>
          </div>

          <p className="text-center text-xs text-gray-500">
            {t('💡 提示：已自动登录，点击"开始使用"即可体验')}
          </p>
        </div>
      </BaseModal>
    )
  }

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title={t('注册')}
      subtitle={t('创建新账号开始学习')}
      size="sm"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <BaseInput
          label={
            <span>
              {t('邮箱')} <span className="text-red-500">＊</span>
            </span>
          }
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t('请输入邮箱地址')}
          required
          error={
            emailUnique === false
              ? t('❌ 邮箱已被使用（开发阶段仍可注册）')
              : undefined
          }
          helperText={
            email && email.trim() !== ''
              ? isCheckingEmail
                ? t('检查中...')
                : emailUnique === true
                  ? t('✅ 邮箱可用')
                  : emailCheckMessage || undefined
              : undefined
          }
        />

        <BaseInput
          label={t('密码')}
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder={t('请输入密码（至少6位）')}
          required
          minLength={6}
          helperText={t('密码长度至少为6位')}
        />

        <BaseInput
          label={t('确认密码')}
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder={t('请再次输入密码')}
          required
          minLength={6}
        />

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="rounded-md border border-yellow-200 bg-yellow-50 p-3">
          <p className="text-xs text-gray-600">
            {t('💡 注册成功后，系统会自动分配一个用户 ID，请记住它用于登录。')}
          </p>
        </div>

        <div className="flex flex-col space-y-3 pt-2">
          <BaseButton type="submit" loading={isLoading} fullWidth>
            {isLoading ? t('注册中...') : t('注册')}
          </BaseButton>
          <BaseButton type="button" variant="secondary" onClick={onClose} fullWidth>
            {t('取消')}
          </BaseButton>
        </div>
      </form>

      <div className="mt-6 border-t border-gray-200 pt-4 text-center">
        <p className="text-sm text-gray-600">
          {t('已有账号？')}{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-primary-600 hover:text-primary-700"
          >
            {t('立即登录')}
          </button>
        </p>
      </div>
    </BaseModal>
  )
}

export default RegisterModal

