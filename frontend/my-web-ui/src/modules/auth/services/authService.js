/**
 * 认证服务
 * 处理所有认证相关的 API 调用
 */
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const authApi = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const authService = {
  /**
   * 用户注册
   * @param {string} password - 密码（至少6位）
   * @returns {Promise<{access_token: string, user_id: number}>}
   */
  register: async (password) => {
    const response = await authApi.post('/api/auth/register', { password })
    return response.data
  },

  /**
   * 用户登录
   * @param {number} userId - 用户ID
   * @param {string} password - 密码
   * @returns {Promise<{access_token: string, user_id: number}>}
   */
  login: async (userId, password) => {
    const response = await authApi.post('/api/auth/login', {
      user_id: userId,
      password: password,
    })
    return response.data
  },

  /**
   * 获取当前用户信息
   * @param {string} token - JWT token
   * @returns {Promise<{user_id: number, created_at: string}>}
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
}

export default authService


