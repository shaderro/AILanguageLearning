/**
 * UserContext - 全局用户状态管理
 * 
 * 功能：
 * - 管理登录状态
 * - 提供用户信息（userId, token）
 * - 提供登录/注册/退出方法
 * - 自动从 localStorage 恢复登录状态
 * - 游客模式和数据迁移
 */
import { createContext, useContext, useState, useEffect, useRef } from 'react'
import authService from '../modules/auth/services/authService'
import guestDataManager from '../utils/guestDataManager'

const UserContext = createContext(null)

// 将后端错误（可能是 string / object / array）规范化成可渲染的字符串，避免 React 渲染 object 报错
function normalizeApiError(error) {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string' && detail.trim()) return detail
  if (typeof error?.message === 'string' && error.message.trim()) return error.message

  // FastAPI 422: detail 通常是 [{loc, msg, type}, ...]
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((item) => {
        const loc = Array.isArray(item?.loc) ? item.loc.join('.') : ''
        const msg = item?.msg || ''
        return [loc, msg].filter(Boolean).join(': ')
      })
      .filter(Boolean)

    if (msgs.length) return msgs.join(' | ')
  }

  if (detail && typeof detail === 'object') {
    try {
      return JSON.stringify(detail)
    } catch {
      return '请求失败（错误详情无法解析）'
    }
  }

  return '请求失败'
}

export function UserProvider({ children }) {
  const [userId, setUserId] = useState(null)
  const [token, setToken] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true) // 初始化加载状态
  const [password, setPassword] = useState(null) // 仅用于 debug
  const [isGuest, setIsGuest] = useState(false) // 是否为游客模式
  const [pendingGuestId, setPendingGuestId] = useState(null) // 待迁移的游客ID
  const [showMigrationDialog, setShowMigrationDialog] = useState(false) // 是否显示迁移对话框
  const isInitializedRef = useRef(false) // 🔧 使用 ref 标记是否已经初始化，避免重复初始化

  // 初始化：从 localStorage 恢复登录状态或创建游客ID
  useEffect(() => {
    // 🔧 如果已经初始化过，直接返回，避免重复初始化
    if (isInitializedRef.current) {
      console.log('⚠️ [UserContext] 已经初始化，跳过重复初始化')
      return
    }
    
    const initAuth = async () => {
      const { userId: savedUserId, token: savedToken } = authService.getAuth()
      
      if (savedUserId && savedToken) {
        console.log('🔍 [UserContext] 检测到已保存的登录信息')
        
        try {
          // 验证 token 是否有效（添加超时处理，增加超时时间避免预处理过程中被登出）
          const user = await Promise.race([
            authService.getCurrentUser(savedToken),
            new Promise((_, reject) => 
              setTimeout(() => reject(new Error('验证超时')), 120000) // 增加到2分钟
            )
          ])
          console.log('✅ [UserContext] Token 有效，自动登录:', user)
          
          // 🔧 确保状态更新是同步的，避免在更新过程中被其他逻辑干扰
          setUserId(parseInt(savedUserId))
          setToken(savedToken)
          setIsAuthenticated(true)
          setIsGuest(false)
          isInitializedRef.current = true
          
          // 🔧 确保状态已设置完成
          console.log('✅ [UserContext] 登录状态已设置，userId:', savedUserId)
        } catch (error) {
          console.log('⚠️ [UserContext] Token 验证失败:', error.message || error)
          // 🔧 修改逻辑：如果是网络错误或超时，不切换模式，保持登录状态
          // 只有在明确的认证错误（401）且不是网络问题时，才考虑切换
          const isNetworkError = error.message?.includes('网络') || 
                                 error.message?.includes('timeout') || 
                                 error.message?.includes('超时') ||
                                 error.message?.includes('Network Error') ||
                                 !error.response
          
          if (isNetworkError) {
            // 网络错误：保持登录状态，不清除信息
            console.log('⚠️ [UserContext] 网络错误，保持登录状态（不清除 localStorage）')
            setUserId(parseInt(savedUserId))
            setToken(savedToken)
            setIsAuthenticated(true)
            setIsGuest(false)
            isInitializedRef.current = true
          } else {
            // 认证错误：切换到游客模式，但不清除 localStorage
            console.log('⚠️ [UserContext] Token 验证失败，保持登录信息但切换到游客模式（不清除 localStorage）')
            createGuestUser()
            isInitializedRef.current = true
          }
        }
      } else {
        // 没有登录信息，创建游客模式
        createGuestUser()
        isInitializedRef.current = true
      }
      
      setIsLoading(false)
    }
    
    // 创建游客用户
    const createGuestUser = () => {
      // 检查是否已有游客ID
      let guestId = localStorage.getItem('guest_user_id')
      
      if (!guestId) {
        // 生成新的游客ID
        guestId = 'guest_' + Math.random().toString(36).substring(2, 10)
        localStorage.setItem('guest_user_id', guestId)
        console.log('👤 [UserContext] 创建游客ID:', guestId)
      } else {
        console.log('👤 [UserContext] 使用已有游客ID:', guestId)
      }
      
      setUserId(guestId)
      setToken(null)
      setIsAuthenticated(false)
      setIsGuest(true)
    }
    
    initAuth()
  }, [])

  /**
   * 登录
   */
  const login = async (inputUserId, inputPassword, inputEmail = null) => {
    try {
      console.log('🔐 [UserContext] 登录中...', { userId: inputUserId, email: inputEmail })
      
      const result = await authService.login(inputUserId, inputPassword, inputEmail)
      
      console.log('✅ [UserContext] 登录成功:', result)
      
      // 保存到 localStorage
      authService.saveAuth(result.user_id, result.access_token)
      authService.savePasswordMapping(result.user_id, inputPassword)
      
      // 检查游客是否有数据需要迁移
      const previousGuestId = isGuest ? userId : null
      
      // 更新状态（从游客模式切换到登录模式）
      setUserId(result.user_id)
      setToken(result.access_token)
      setPassword(inputPassword)
      setIsAuthenticated(true)
      setIsGuest(false)  // 不再是游客
      
      // 如果从游客模式登录且有数据，显示迁移对话框
      if (previousGuestId && guestDataManager.hasGuestData(previousGuestId)) {
        console.log('📦 [UserContext] 检测到游客数据，准备迁移')
        setPendingGuestId(previousGuestId)
        setShowMigrationDialog(true)
      }
      
      return { success: true, userId: result.user_id, token: result.access_token }
    } catch (error) {
      console.error('❌ [UserContext] 登录请求失败:', error)
      
      // 🔧 修复：如果超时但localStorage中已有token，说明登录实际上已经成功
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        console.log('⏱️ [UserContext] 登录请求超时，检查localStorage中是否有token...')
        const savedAuth = authService.getAuth()
        if (savedAuth.token && savedAuth.userId) {
          console.log('✅ [UserContext] 检测到localStorage中已有token，登录实际上已成功')
          console.log('🔍 [UserContext] 恢复登录状态:', { userId: savedAuth.userId })
          
          // 恢复登录状态
          const previousGuestId = isGuest ? userId : null
          setUserId(savedAuth.userId)
          setToken(savedAuth.token)
          setPassword(inputPassword)
          setIsAuthenticated(true)
          setIsGuest(false)
          
          // 如果从游客模式登录且有数据，显示迁移对话框
          if (previousGuestId && guestDataManager.hasGuestData(previousGuestId)) {
            console.log('📦 [UserContext] 检测到游客数据，准备迁移')
            setPendingGuestId(previousGuestId)
            setShowMigrationDialog(true)
          }
          
          return { success: true, userId: savedAuth.userId, token: savedAuth.token }
        }
      }
      
      return {
        success: false,
        error: normalizeApiError(error) || '登录失败',
      }
    }
  }

  /**
   * 注册
   */
  const register = async (inputPassword, inputEmail) => {
    try {
      console.log('📝 [UserContext] 注册中...', { email: inputEmail })
      
      const result = await authService.register(inputPassword, inputEmail)
      
      console.log('✅ [UserContext] 注册成功:', result)
      
      // 保存到 localStorage
      authService.saveAuth(result.user_id, result.access_token)
      authService.savePasswordMapping(result.user_id, inputPassword)
      
      // 检查游客是否有数据需要迁移
      const previousGuestId = isGuest ? userId : null
      
      // 更新状态（从游客模式切换到登录模式）
      setUserId(result.user_id)
      setToken(result.access_token)
      setPassword(inputPassword)
      setIsAuthenticated(true)
      setIsGuest(false)  // 不再是游客
      
      // 如果从游客模式注册且有数据，显示迁移对话框
      if (previousGuestId && guestDataManager.hasGuestData(previousGuestId)) {
        console.log('📦 [UserContext] 检测到游客数据，准备迁移')
        setPendingGuestId(previousGuestId)
        setShowMigrationDialog(true)
      }
      
      return { 
        success: true, 
        userId: result.user_id, 
        token: result.access_token,
        emailUnique: result.email_unique,
        emailCheckMessage: result.email_check_message
      }
    } catch (error) {
      console.error('❌ [UserContext] 注册失败:', error)
      return { 
        success: false, 
        error: normalizeApiError(error) || '注册失败',
      }
    }
  }

  /**
   * 退出登录（切换回游客模式）
   */
  const logout = () => {
    console.log('👋 [UserContext] 退出登录')
    
    // 清除登录信息
    authService.clearAuth()
    
    // 切换回游客模式
    let guestId = localStorage.getItem('guest_user_id')
    if (!guestId) {
      guestId = 'guest_' + Math.random().toString(36).substring(2, 10)
      localStorage.setItem('guest_user_id', guestId)
    }
    
    console.log('👤 [UserContext] 切换到游客模式:', guestId)
    
    setUserId(guestId)
    setToken(null)
    setPassword(null)
    setIsAuthenticated(false)
    setIsGuest(true)
  }

  const value = {
    userId,
    token,
    password, // 仅用于 debug
    isAuthenticated,
    isGuest,  // 是否为游客模式
    isLoading,
    login,
    register,
    logout,
    // 数据迁移相关
    pendingGuestId,
    showMigrationDialog,
    setShowMigrationDialog
  }

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  )
}

/**
 * Hook: 使用用户上下文
 */
export function useUser() {
  const context = useContext(UserContext)
  
  if (!context) {
    throw new Error('useUser must be used within UserProvider')
  }
  
  return context
}

export default UserContext

