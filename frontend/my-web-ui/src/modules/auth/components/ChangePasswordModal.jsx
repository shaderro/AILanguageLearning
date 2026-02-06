/**
 * 修改密码模态框
 * 已登录用户修改密码（测试阶段，无需输入当前密码）
 */
import { useState } from 'react'
import { authService } from '../services/authService'
import { useTranslate } from '../../../i18n/useTranslate'
import { BaseModal, BaseInput, BaseButton } from '../../../components/base'

const ChangePasswordModal = ({ isOpen, onClose, userId, userEmail }) => {
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const t = useTranslate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    // 验证密码
    if (newPassword.length < 6) {
      setError(t('密码长度至少为6位'))
      return
    }

    if (newPassword !== confirmPassword) {
      setError(t('两次输入的密码不一致'))
      return
    }

    // 验证用户ID
    if (!userId) {
      setError(t('用户ID不存在，请重新登录'))
      return
    }

    setIsLoading(true)

    try {
      console.log('🔐 [ChangePassword] 修改密码中...', { userId, userEmail })
      
      // 使用测试模式的直接重置密码方法
      const result = await authService.resetPasswordDirect(userEmail || null, userId, newPassword)
      
      if (result.success) {
        console.log('✅ [ChangePassword] 密码修改成功')
        setSuccess(true)
        // 清空表单
        setNewPassword('')
        setConfirmPassword('')
        // 2秒后关闭模态框
        setTimeout(() => {
          setSuccess(false)
          onClose()
        }, 2000)
      } else {
        setError(result.message || t('修改密码失败'))
      }
    } catch (error) {
      console.error('❌ [ChangePassword] 修改密码失败:', error)
      setError(error.response?.data?.detail || error.message || t('修改密码失败，请重试'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleClose = () => {
    setNewPassword('')
    setConfirmPassword('')
    setError('')
    setSuccess(false)
    onClose()
  }

  if (!isOpen) return null

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('修改密码')}
      subtitle={t('请输入您的新密码（测试阶段，无需输入当前密码）')}
      size="sm"
    >
      {success ? (
        <div className="text-center py-4">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{t('密码修改成功！')}</h3>
          <p className="text-sm text-gray-600">{t('请使用新密码登录')}</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <BaseInput
            label={t('新密码')}
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder={t('请输入新密码（至少6位）')}
            required
            minLength={6}
            helperText={t('密码长度至少为6位')}
          />

          <BaseInput
            label={t('确认密码')}
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder={t('请再次输入新密码')}
            required
            minLength={6}
          />

          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex flex-col space-y-3 pt-2">
            <BaseButton type="submit" loading={isLoading} fullWidth>
              {isLoading ? t('修改中...') : t('确认修改')}
            </BaseButton>
            <BaseButton type="button" variant="secondary" onClick={handleClose} fullWidth>
              {t('取消')}
            </BaseButton>
          </div>
        </form>
      )}
    </BaseModal>
  )
}

export default ChangePasswordModal
