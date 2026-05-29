/**
 * Magic link 回调：/auth/callback?token=...
 */
import { useEffect, useRef, useState } from 'react'
import { useTranslate } from '../../../i18n/useTranslate'
import { authService } from '../services/authService'
import { markPendingWelcomeCredits } from '../../../utils/creditsUtils'
import { clearMagicLinkSendState } from '../utils/magicLinkCooldown'

const AuthCallbackPage = () => {
  const t = useTranslate()
  const [phase, setPhase] = useState('loading') // loading | ok | error
  const [errorDetail, setErrorDetail] = useState(null) // 'missing_token' | string (API detail)
  const verifyStarted = useRef(false)

  useEffect(() => {
    const run = async () => {
      if (verifyStarted.current) return
      verifyStarted.current = true

      const params = new URLSearchParams(window.location.search)
      let token = params.get('token')
      if (token) {
        try {
          token = decodeURIComponent(token.trim())
        } catch {
          token = token.trim()
        }
      }
      if (!token) {
        setPhase('error')
        setErrorDetail('missing_token')
        return
      }
      try {
        const data = await authService.verifyMagicLink(token)
        authService.saveAuth(String(data.user_id), data.session_token)
        clearMagicLinkSendState()
        if (data.is_new_user) {
          markPendingWelcomeCredits()
        }
        setPhase('ok')
        window.setTimeout(() => {
          window.location.href = '/'
        }, 800)
      } catch (err) {
        const detail = err?.response?.data?.detail
        setPhase('error')
        setErrorDetail(typeof detail === 'string' ? detail : 'fallback')
      }
    }
    run()
  }, [])

  const message = (() => {
    if (phase === 'loading') return t('正在验证登录链接…')
    if (phase === 'ok') return t('登录成功，正在跳转…')
    if (errorDetail === 'missing_token') return t('链接无效：缺少 token 参数')
    if (typeof errorDetail === 'string' && errorDetail !== 'fallback') {
      return t(errorDetail) || errorDetail
    }
    return t('链接无效或已过期，请重新获取登录邮件')
  })()

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full rounded-lg border border-gray-200 bg-white p-8 shadow-sm text-center">
        <h1 className="text-lg font-semibold text-gray-900 mb-2">{t('邮箱登录')}</h1>
        <p
          className={
            phase === 'error'
              ? 'text-sm text-red-600'
              : phase === 'ok'
                ? 'text-sm text-green-700'
                : 'text-sm text-gray-600'
          }
        >
          {message}
        </p>
        {phase === 'error' && (
          <a href="/" className="mt-6 inline-block text-sm text-primary-600 hover:underline">
            {t('返回首页')}
          </a>
        )}
      </div>
    </div>
  )
}

export default AuthCallbackPage
