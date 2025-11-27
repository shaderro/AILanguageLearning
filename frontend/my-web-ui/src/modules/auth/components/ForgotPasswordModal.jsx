/**
 * 忘记密码模态框
 * 用户输入邮箱或用户ID，生成重置链接
 */
import { useState } from 'react'
import { authService } from '../services/authService'
import { useTranslate } from '../../../i18n/useTranslate'
import { BaseModal, BaseInput, BaseButton } from '../../../components/base'

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

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('忘记密码')}
      subtitle={t('请输入您的邮箱或用户ID以生成重置链接')}
      size="sm"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <BaseInput
          label={
            <span>
              {t('邮箱')} <span className="text-xs text-gray-400">{t('(可选)')}</span>
            </span>
          }
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t('请输入邮箱（可选）')}
        />

        <BaseInput
          label={
            <span>
              {t('用户 ID')} <span className="text-xs text-gray-400">{t('(可选)')}</span>
            </span>
          }
          type="number"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder={t('请输入用户ID（可选）')}
          helperText={t('💡 提示：至少提供邮箱或用户ID之一')}
        />

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="flex flex-col space-y-3 pt-2">
          <BaseButton type="submit" loading={isLoading} fullWidth>
            {isLoading ? t('生成中...') : t('生成重置链接')}
          </BaseButton>
          <BaseButton type="button" variant="secondary" onClick={handleClose} fullWidth>
            {t('取消')}
          </BaseButton>
        </div>
      </form>

      <div className="mt-6 border-t border-gray-200 pt-4 text-center">
        <p className="text-sm text-gray-600">
          {t('想起密码了？')}{' '}
          <button
            type="button"
            onClick={() => {
              handleClose()
              onSwitchToLogin()
            }}
            className="text-primary-600 hover:text-primary-700"
          >
            {t('返回登录')}
          </button>
        </p>
      </div>
    </BaseModal>
  )
}

export default ForgotPasswordModal

