/**
 * 注册模态框
 * 显示注册表单
 */
import { useState, useEffect } from 'react'
import { useUser } from '../../../contexts/UserContext'
import { authService } from '../services/authService'
import { useTranslate } from '../../../i18n/useTranslate'
import { BaseModal, BaseInput, BaseButton, BaseBadge } from '../../../components/base'

const RegisterModal = ({ isOpen, onClose, onSwitchToLogin, onOpenPPTerms, onStartOnboarding }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [emailUnique, setEmailUnique] = useState(null) // null: 未检查, true: 唯一, false: 不唯一
  const [emailCheckMessage, setEmailCheckMessage] = useState('')
  const [isCheckingEmail, setIsCheckingEmail] = useState(false)
  const [agreed, setAgreed] = useState(false) // 是否勾选隐私政策与服务条款
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

        // 清空表单
        setEmail('')
        setPassword('')
        setConfirmPassword('')
        setEmailUnique(null)
        setEmailCheckMessage('')

        // 直接进入首次使用流程（选择语言页面）
        if (onStartOnboarding) {
          onStartOnboarding()
        } else {
          onClose()
        }
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

  if (!isOpen) return null

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onClose}
      title={t('注册')}
      subtitle={t('创建新账号开始学习')}
      size="sm"
      closeOnOverlay={false}
      closeOnEscape={false}
    >
      <form onSubmit={handleSubmit} className="space-y-3">
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
              ? t('❌ 该邮箱已被注册，请使用其他邮箱或直接登录')
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

        <div className="rounded-md border border-yellow-200 bg-yellow-50 p-2">
          <p className="text-xs text-gray-600">
            {t('💡 注册成功后，系统会自动分配一个用户 ID，请记住它用于登录。')}
          </p>
        </div>

        {/* 同意条款 */}
        <div className="text-xs text-gray-600 flex items-center justify-center gap-2">
          <label className="inline-flex items-center gap-1 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="h-3 w-3 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <span>{t('我同意')}</span>
          </label>
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              if (onOpenPPTerms) {
                onOpenPPTerms()
              }
            }}
            className="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-700 bg-transparent border border-gray-300 rounded-md hover:bg-gray-50 hover:text-gray-900 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary-500"
          >
            {t('隐私政策与服务条款')}
          </button>
        </div>

        <div className="flex flex-col space-y-2 pt-1">
          <BaseButton type="submit" loading={isLoading} fullWidth disabled={!agreed}>
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

