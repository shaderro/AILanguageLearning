/**
 * 认证服务
 * 处理所有认证相关的 API 调用
 */
import axios from 'axios'

// 从环境变量获取 API 基础 URL，默认使用 localhost:8000（本地开发）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const authApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 增加到 30 秒，避免刷新后验证 token 时超时
  headers: {
    'Content-Type': 'application/json',
  },
})

export const authService = {
  /**
   * 用户注册
   * @param {string} password - 密码（至少6位）
   * @param {string} email - 邮箱
   * @returns {Promise<{access_token: string, user_id: number, email_unique: boolean, email_check_message: string}>}
   */
  register: async (password, email) => {
    const response = await authApi.post('/api/auth/register', { password, email })
    return response.data
  },

  /**
   * 检查邮箱唯一性（用于debug UI）
   * @param {string} email - 要检查的邮箱
   * @returns {Promise<{unique: boolean, message: string}>}
   */
  checkEmailUnique: async (email) => {
    const response = await authApi.get('/api/auth/check-email', {
      params: { email }
    })
    return response.data
  },

  /**
   * 用户登录
   * @param {number} userId - 用户ID（可选）
   * @param {string} password - 密码
   * @param {string} email - 邮箱（可选）
   * @returns {Promise<{access_token: string, user_id: number}>}
   */
  login: async (userId, password, email = null) => {
    const requestBody = { password }
    if (userId) {
      requestBody.user_id = userId
    }
    if (email) {
      requestBody.email = email
    }
    const response = await authApi.post('/api/auth/login', requestBody)
    return response.data
  },

  /**
   * 获取当前用户信息
   * @param {string} token - JWT token
   * @returns {Promise<{user_id: number, email: string, created_at: string}>}
   */
  getCurrentUser: async (token) => {
    const response = await authApi.get('/api/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    return response.data
  },

  /**
   * 本地存储：保存认证信息
   */
  saveAuth: (userId, token) => {
    localStorage.setItem('user_id', userId)
    localStorage.setItem('access_token', token)
  },

  /**
   * 本地存储：获取认证信息
   */
  getAuth: () => {
    const userId = localStorage.getItem('user_id')
    const token = localStorage.getItem('access_token')
    return { userId, token }
  },

  /**
   * 本地存储：清除认证信息
   */
  clearAuth: () => {
    localStorage.removeItem('user_id')
    localStorage.removeItem('access_token')
  },

  /**
   * 检查是否已登录
   */
  isAuthenticated: () => {
    const { token } = authService.getAuth()
    return !!token
  },

  /**
   * 获取所有用户信息（仅用于开发调试）
   * ⚠️ 仅开发环境使用
   */
  getAllUsersDebug: async () => {
    try {
      const response = await authApi.get('/api/auth/debug/all-users')
      console.log('🔍 [authService] getAllUsersDebug response:', response)
      return response.data
    } catch (error) {
      console.error('❌ [authService] getAllUsersDebug error:', error)
      throw error
    }
  },

  /**
   * 本地存储：保存用户密码映射（仅用于开发调试）
   * 格式：{ user_id: password }
   */
  savePasswordMapping: (userId, password) => {
    try {
      const mapping = JSON.parse(localStorage.getItem('debug_password_mapping') || '{}')
      mapping[userId] = password
      localStorage.setItem('debug_password_mapping', JSON.stringify(mapping))
    } catch (e) {
      console.error('Failed to save password mapping:', e)
    }
  },

  /**
   * 本地存储：获取密码映射
   */
  getPasswordMapping: () => {
    try {
      return JSON.parse(localStorage.getItem('debug_password_mapping') || '{}')
    } catch (e) {
      return {}
    }
  },

  /**
   * 忘记密码 - 生成重置链接
   * @param {string} email - 邮箱（可选）
   * @param {number} userId - 用户ID（可选）
   * @returns {Promise<{success: boolean, reset_link: string, message: string, token?: string}>}
   */
  forgotPassword: async (email = null, userId = null) => {
    const response = await authApi.post('/api/auth/forgot-password', {
      email,
      user_id: userId
    })
    return response.data
  },

  /**
   * 重置密码
   * @param {string} token - 密码重置 token
   * @param {string} newPassword - 新密码
   * @returns {Promise<{success: boolean, message: string}>}
   */
  resetPassword: async (token, newPassword) => {
    const response = await authApi.post('/api/auth/reset-password', {
      token,
      new_password: newPassword
    })
    return response.data
  },
}

export default authService


