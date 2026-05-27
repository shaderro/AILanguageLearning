/**
 * Magic Link 单页登录：仅邮箱 → 发链 → 成功提示（60s 内不可重复发送）
 */
import { useCallback, useEffect, useState } from 'react'
import { BaseModal, BaseInput, BaseButton } from '../../../components/base'
import { authService } from '../services/authService'
import {
  getMagicLinkSendState,
  setMagicLinkSendState,
  clearMagicLinkSendState,
  isEmailInCooldown,
  MAGIC_LINK_COOLDOWN_SECONDS,
} from '../utils/magicLinkCooldown'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const MagicLinkAuthModal = ({ isOpen, onClose }) => {
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
    applyPendingState()
  }, [isOpen, applyPendingState])

  useEffect(() => {
    if (!isOpen || cooldownSeconds <= 0) return undefined
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
      setError('Please enter a valid email address.')
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
          ? detail
          : 'Could not send the sign-in link. Please try again.',
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
                Continue to LinkText
              </h2>
              <p className="mt-2 text-sm text-gray-500 leading-relaxed">
                Enter your email to receive a sign-in link.
              </p>
            </div>

            <form onSubmit={handleSendLink} className="space-y-4">
              <BaseInput
                type="email"
                name="email"
                autoComplete="email"
                placeholder="you@company.com"
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
                {isSending ? 'Sending...' : 'Send Link'}
              </BaseButton>
            </form>

            <p className="mt-6 text-center text-xs text-gray-400 leading-relaxed">
              New users will automatically create an account.
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
              Check your email
            </h2>
            <p className="mt-2 text-sm text-gray-600 leading-relaxed">
              We sent a secure sign-in link to
            </p>
            <p className="mt-1 text-sm font-medium text-gray-900 break-all">{email}</p>
            <p className="mt-3 text-xs text-gray-400 leading-relaxed">
              Check spam/promotions if you don&apos;t see it.
            </p>
            {cooldownSeconds > 0 && (
              <p className="mt-4 text-xs text-gray-500">
                You can request another link in {cooldownSeconds}s.
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
                  ? `Resend available in ${cooldownSeconds}s`
                  : 'Resend link'}
              </BaseButton>
              <BaseButton
                type="button"
                fullWidth
                className="rounded-xl h-11 font-medium"
                onClick={handleClose}
              >
                Done
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
                Use a different email
              </button>
            </div>
          </div>
        )}
      </div>
    </BaseModal>
  )
}

export default MagicLinkAuthModal
