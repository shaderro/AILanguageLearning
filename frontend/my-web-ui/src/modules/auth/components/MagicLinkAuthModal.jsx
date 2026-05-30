/**
 * Magic Link 单页登录：仅邮箱 → 发链 → 成功提示（60s 内不可重复发送）
 */
import { useCallback, useEffect, useState } from 'react'
import { BaseModal, BaseInput, BaseButton } from '../../../components/base'
import { useTranslate } from '../../../i18n/useTranslate'
import { useUser } from '../../../contexts/UserContext'
import { authService } from '../services/authService'
import {
  getMagicLinkSendState,
  setMagicLinkSendState,
  clearMagicLinkSendState,
  isEmailInCooldown,
  MAGIC_LINK_COOLDOWN_SECONDS,
} from '../utils/magicLinkCooldown'
import { getLastMagicLinkEmail, setLastMagicLinkEmail } from '../utils/magicLinkRemember'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const MagicLinkAuthModal = ({ isOpen, onClose }) => {
  const t = useTranslate()
  const { isAuthenticated } = useUser()
  const [email, setEmail] = useState('')
  const [phase, setPhase] = useState('form') // form | success
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState('')
  const [cooldownSeconds, setCooldownSeconds] = useState(0)

  const applyPendingState = useCallback(() => {
    const pending = getMagicLinkSendState()
    if (!pending) return false
    setEmail(pending.email)
    setPhase('success')
    setCooldownSeconds(pending.remainingSeconds)
    setError('')
    return true
  }, [])

  useEffect(() => {
    if (!isOpen) return
    if (isAuthenticated) {
      onClose?.()
      return
    }
    if (applyPendingState()) return
    const remembered = getLastMagicLinkEmail()
    if (remembered) {
      setEmail(remembered)
    }
  }, [isOpen, isAuthenticated, applyPendingState, onClose])

  useEffect(() => {
    if (!isOpen || isAuthenticated || cooldownSeconds <= 0) return undefined
    const timer = window.setInterval(() => {
      const pending = getMagicLinkSendState()
      if (!pending) {
        setCooldownSeconds(0)
        return
      }
      setCooldownSeconds(pending.remainingSeconds)
    }, 1000)
    return () => window.clearInterval(timer)
  }, [isOpen, cooldownSeconds])

  const handleClose = () => {
    onClose?.()
  }

  const enterSuccessPhase = (trimmedEmail, retryAfterSeconds) => {
    const seconds = Math.max(
      1,
      Number(retryAfterSeconds) || MAGIC_LINK_COOLDOWN_SECONDS,
    )
    setLastMagicLinkEmail(trimmedEmail)
    setMagicLinkSendState(trimmedEmail, seconds)
    setEmail(trimmedEmail)
    setPhase('success')
    setCooldownSeconds(seconds)
    setError('')
  }

  const handleSendLink = async (e) => {
    e?.preventDefault()
    setError('')
    const trimmed = email.trim()
    if (!trimmed || !EMAIL_RE.test(trimmed)) {
      setError(t('请输入有效的邮箱地址'))
      return
    }

    if (isEmailInCooldown(trimmed)) {
      enterSuccessPhase(trimmed, getMagicLinkSendState()?.remainingSeconds)
      return
    }

    setIsSending(true)
    try {
      const data = await authService.requestMagicLink(trimmed)
      const retryAfter = Number(data?.retry_after_seconds) || MAGIC_LINK_COOLDOWN_SECONDS
      enterSuccessPhase(trimmed, retryAfter)
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(
        typeof detail === 'string'
          ? t(detail) || detail
          : t('无法发送登录链接，请稍后重试。'),
      )
    } finally {
      setIsSending(false)
    }
  }

  const handleResend = async () => {
    if (cooldownSeconds > 0 || isSending) return
    const trimmed = email.trim()
    if (!trimmed || !EMAIL_RE.test(trimmed)) return
    await handleSendLink()
  }

  const canResend = cooldownSeconds <= 0 && !isSending

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={handleClose}
      size="sm"
      closeOnOverlay={!isSending}
      closeOnEscape={!isSending}
      className="shadow-2xl shadow-gray-900/5"
    >
      <div className="py-2 sm:py-4">
        {phase === 'form' ? (
          <>
            <div className="text-center mb-8">
              <h2 className="text-2xl font-semibold tracking-tight text-gray-900">
                {t('继续使用 LinkText')}
              </h2>
              <p className="mt-2 text-sm text-gray-500 leading-relaxed">
                {t('输入邮箱，我们将发送登录链接。')}
              </p>
            </div>

            <form onSubmit={handleSendLink} className="space-y-4">
              <BaseInput
                type="email"
                name="email"
                autoComplete="email"
                placeholder={t('请输入邮箱')}
                value={email}
                onChange={(ev) => setEmail(ev.target.value)}
                disabled={isSending}
                inputClassName="rounded-xl border-gray-200/80 hover:border-gray-300 focus:border-gray-400 transition-colors"
              />

              {error && (
                <p
                  className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2"
                  role="alert"
                >
                  {error}
                </p>
              )}

              <BaseButton
                type="submit"
                fullWidth
                loading={isSending}
                disabled={isSending}
                className="rounded-xl h-11 font-medium shadow-sm hover:shadow-md transition-shadow"
              >
                {isSending ? t('发送中…') : t('发送登录链接')}
              </BaseButton>
            </form>

            <p className="mt-6 text-center text-xs text-gray-400 leading-relaxed">
              {t('新用户将自动创建账号。')}
            </p>
          </>
        ) : (
          <div className="text-center py-2">
            <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 text-gray-700">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.75}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold tracking-tight text-gray-900">
              {t('请查收邮件')}
            </h2>
            <p className="mt-2 text-sm text-gray-600 leading-relaxed">
              {t('我们已向以下邮箱发送安全登录链接：')}
            </p>
            <p className="mt-1 text-sm font-medium text-gray-900 break-all">{email}</p>
            <p className="mt-3 text-xs text-gray-400 leading-relaxed">
              {t('若未收到，请检查垃圾邮件或推广文件夹。')}
            </p>
            {cooldownSeconds > 0 && (
              <p className="mt-4 text-xs text-gray-500">
                {t('你可以在 {n} 秒后重新请求链接').replace('{n}', String(cooldownSeconds))}
              </p>
            )}
            <div className="mt-8 space-y-3">
              <BaseButton
                type="button"
                variant="secondary"
                fullWidth
                className="rounded-xl h-11 font-medium"
                disabled={!canResend}
                loading={isSending}
                onClick={handleResend}
              >
                {cooldownSeconds > 0
                  ? t('{n} 秒后可重新发送').replace('{n}', String(cooldownSeconds))
                  : t('重新发送链接')}
              </BaseButton>
              <BaseButton
                type="button"
                fullWidth
                className="rounded-xl h-11 font-medium"
                onClick={handleClose}
              >
                {t('完成')}
              </BaseButton>
              <button
                type="button"
                className="w-full text-xs text-gray-500 hover:text-gray-700 underline-offset-2 hover:underline"
                onClick={() => {
                  clearMagicLinkSendState()
                  setPhase('form')
                  setCooldownSeconds(0)
                  setError('')
                }}
              >
                {t('使用其他邮箱')}
              </button>
            </div>
          </div>
        )}
      </div>
    </BaseModal>
  )
}

export default MagicLinkAuthModal
