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
import { createContext, useContext, useState, useEffect } from 'react'
import authService from '../modules/auth/services/authService'
import guestDataManager from '../utils/guestDataManager'

const UserContext = createContext(null)

export function UserProvider({ children }) {
  const [userId, setUserId] = useState(null)
  const [token, setToken] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true) // 初始化加载状态
  const [password, setPassword] = useState(null) // 仅用于 debug
  const [isGuest, setIsGuest] = useState(false) // 是否为游客模式
  const [pendingGuestId, setPendingGuestId] = useState(null) // 待迁移的游客ID
  const [showMigrationDialog, setShowMigrationDialog] = useState(false) // 是否显示迁移对话框

  // 初始化：从 localStorage 恢复登录状态或创建游客ID
  useEffect(() => {
    const initAuth = async () => {
      const { userId: savedUserId, token: savedToken } = authService.getAuth()
      
      if (savedUserId && savedToken) {
        console.log('🔍 [UserContext] 检测到已保存的登录信息')
        
        try {
          // 验证 token 是否有效
          const user = await authService.getCurrentUser(savedToken)
          console.log('✅ [UserContext] Token 有效，自动登录:', user)
          
          setUserId(parseInt(savedUserId))
          setToken(savedToken)
          setIsAuthenticated(true)
          setIsGuest(false)
        } catch (error) {
          console.log('⚠️ [UserContext] Token 无效，清除登录信息')
          authService.clearAuth()
          // Token 无效，创建游客模式
          createGuestUser()
        }
      } else {
        // 没有登录信息，创建游客模式
        createGuestUser()
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
  const login = async (inputUserId, inputPassword) => {
    try {
      console.log('🔐 [UserContext] 登录中...', { userId: inputUserId })
      
      const result = await authService.login(inputUserId, inputPassword)
      
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
      console.error('❌ [UserContext] 登录失败:', error)
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message || '登录失败'
      }
    }
  }

  /**
   * 注册
   */
  const register = async (inputPassword) => {
    try {
      console.log('📝 [UserContext] 注册中...')
      
      const result = await authService.register(inputPassword)
      
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
      
      return { success: true, userId: result.user_id, token: result.access_token }
    } catch (error) {
      console.error('❌ [UserContext] 注册失败:', error)
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message || '注册失败'
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

