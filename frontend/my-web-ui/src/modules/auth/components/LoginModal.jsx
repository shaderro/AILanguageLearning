/**
 * 登录模态框
 * 显示登录表单
 */
import { useState } from 'react'
import authService from '../services/authService'

const LoginModal = ({ isOpen, onClose, onSwitchToRegister, onLoginSuccess }) => {
  const [userId, setUserId] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      // 调用真实 API
      const userIdInt = parseInt(userId)
      console.log('🔐 [Login] Attempting login:', { 
        userId: userIdInt, 
        passwordLength: password.length 
      })
      
      const result = await authService.login(userIdInt, password)
      
      console.log('✅ [Login] Login successful:', result)
      
      // 保存认证信息到 localStorage
      authService.saveAuth(result.user_id, result.access_token)
      
      // 保存密码映射（仅用于开发调试）
      authService.savePasswordMapping(result.user_id, password)
      
      // 通知父组件登录成功
      if (onLoginSuccess) {
        onLoginSuccess(result.user_id, result.access_token, password)
      }
      
      // 关闭模态框
      onClose()
      
      // 清空表单
      setUserId('')
      setPassword('')
    } catch (error) {
      console.error('❌ [Login] Login failed:', error)
      console.error('❌ [Login] Error details:', {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      })
      
      const errorMessage = error.response?.data?.detail || error.message || '登录失败，请检查用户ID和密码'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        {/* 标题 */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">登录</h2>
          <p className="text-sm text-gray-600 mt-1">欢迎回来！请登录您的账号</p>
        </div>

        {/* 登录表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 用户ID */}
          <div>
            <label htmlFor="userId" className="block text-sm font-medium text-gray-700 mb-1">
              用户 ID
            </label>
            <input
              type="number"
              id="userId"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="请输入您的用户ID"
              required
            />
          </div>

          {/* 密码 */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              密码
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="请输入密码"
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

          {/* 按钮组 */}
          <div className="flex flex-col space-y-3 pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
            >
              {isLoading ? '登录中...' : '登录'}
            </button>

            <button
              type="button"
              onClick={onClose}
              className="w-full bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors font-medium"
            >
              取消
            </button>
          </div>
        </form>

        {/* 注册提示 */}
        <div className="mt-6 text-center border-t border-gray-200 pt-4">
          <p className="text-sm text-gray-600">
            还没有账号？{' '}
            <button
              onClick={onSwitchToRegister}
              className="text-blue-500 hover:text-blue-600 font-medium"
            >
              立即注册
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginModal

