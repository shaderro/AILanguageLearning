/**
 * Magic link 回调：/auth/callback?token=...
 * 调用 verify 后写入 localStorage 并跳转首页（与现有 UserContext 恢复逻辑兼容）
 */
import { useEffect, useState } from 'react'
import { authService } from '../services/authService'

const AuthCallbackPage = () => {
  const [status, setStatus] = useState('loading') // loading | ok | error
  const [message, setMessage] = useState('正在验证登录链接…')

  useEffect(() => {
    const run = async () => {
      const params = new URLSearchParams(window.location.search)
      const token = params.get('token')
      if (!token) {
        setStatus('error')
        setMessage('链接无效：缺少 token 参数')
        return
      }
      try {
        const data = await authService.verifyMagicLink(token)
        authService.saveAuth(String(data.user_id), data.session_token)
        setStatus('ok')
        setMessage('登录成功，正在跳转…')
        window.setTimeout(() => {
          window.location.href = '/'
        }, 800)
      } catch (err) {
        const detail = err?.response?.data?.detail
        setStatus('error')
        setMessage(typeof detail === 'string' ? detail : '链接无效或已过期，请重新获取登录邮件')
      }
    }
    run()
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full rounded-lg border border-gray-200 bg-white p-8 shadow-sm text-center">
        <h1 className="text-lg font-semibold text-gray-900 mb-2">邮箱登录</h1>
        <p
          className={
            status === 'error'
              ? 'text-sm text-red-600'
              : status === 'ok'
                ? 'text-sm text-green-700'
                : 'text-sm text-gray-600'
          }
        >
          {message}
        </p>
        {status === 'error' && (
          <a href="/" className="mt-6 inline-block text-sm text-primary-600 hover:underline">
            返回首页
          </a>
        )}
      </div>
    </div>
  )
}

export default AuthCallbackPage
