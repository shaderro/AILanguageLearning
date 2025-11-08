/**
 * 用户调试按钮
 * 仅用于开发阶段，显示当前用户和所有用户的信息
 * ⚠️ 生产环境应移除此组件
 */
import { useState, useEffect } from 'react'
import authService from '../services/authService'

const UserDebugButton = ({ userId, password }) => {
  const [showDebugInfo, setShowDebugInfo] = useState(false)
  const [allUsers, setAllUsers] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [passwordMapping, setPasswordMapping] = useState({})

  // 加载所有用户信息
  useEffect(() => {
    if (showDebugInfo) {
      loadAllUsers()
      setPasswordMapping(authService.getPasswordMapping())
    }
  }, [showDebugInfo])

  const loadAllUsers = async () => {
    setIsLoading(true)
    try {
      const result = await authService.getAllUsersDebug()
      console.log('📊 [Debug] Loaded all users:', result)
      
      // 检查返回的数据结构
      if (result && result.data && result.data.users) {
        console.log('✅ [Debug] Found users:', result.data.users.length)
        setAllUsers(result.data.users)
      } else if (result && result.users) {
        // 备用格式
        console.log('✅ [Debug] Found users (alt format):', result.users.length)
        setAllUsers(result.users)
      } else {
        console.warn('⚠️ [Debug] No users found in response')
        setAllUsers([])
      }
    } catch (error) {
      console.error('❌ [Debug] Failed to load users:', error)
      console.error('Error details:', error.response?.data)
      setAllUsers([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopyUserId = () => {
    navigator.clipboard.writeText(userId.toString())
    alert('User ID 已复制到剪贴板')
  }

  const handleCopyPassword = () => {
    navigator.clipboard.writeText(password)
    alert('密码已复制到剪贴板')
  }

  const handleCopyUserInfo = (uid, pwd) => {
    const text = `User ID: ${uid}\nPassword: ${pwd || '(未记录)'}`
    navigator.clipboard.writeText(text)
    alert('用户信息已复制到剪贴板')
  }

  return (
    <>
      {/* Debug 按钮 */}
      <button
        onClick={() => setShowDebugInfo(true)}
        className="px-3 py-1.5 bg-yellow-500 text-white text-xs font-medium rounded hover:bg-yellow-600 transition-colors flex items-center space-x-1"
        title="开发调试：查看用户信息"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
        </svg>
        <span>USER_DEBUG</span>
      </button>

      {/* Debug 信息模态框 */}
      {showDebugInfo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* 标题 */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900 flex items-center space-x-2">
                <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                <span>用户调试信息</span>
              </h3>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">{allUsers.length} 个用户</span>
                <button
                  onClick={() => setShowDebugInfo(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* 当前用户信息 */}
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span>当前用户</span>
              </h4>

                {/* 警告提示 */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
                <div className="flex items-start space-x-2">
                  <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-1.959-1.333-2.73 0L3.732 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-xs text-yellow-800">
                    ⚠️ 此功能仅用于开发调试<br />
                    生产环境请移除此组件
                  </p>
                </div>
              </div>

              {/* 用户信息 */}
              <div className="space-y-4">
              {/* User ID */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">用户 ID</label>
                  <button
                    onClick={handleCopyUserId}
                    className="text-xs text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span>复制</span>
                  </button>
                </div>
                <div className="text-2xl font-mono font-bold text-gray-900 bg-white px-3 py-2 rounded border border-gray-200">
                  {userId}
                </div>
              </div>

              {/* Password */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">密码</label>
                  <button
                    onClick={handleCopyPassword}
                    className="text-xs text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span>复制</span>
                  </button>
                </div>
                <div className="text-lg font-mono font-semibold text-gray-900 bg-white px-3 py-2 rounded border border-gray-200 break-all">
                  {password || '(密码未保存)'}
                </div>
              </div>

              {/* Token 信息 */}
              <div className="bg-gray-50 rounded-lg p-4">
                <label className="text-sm font-medium text-gray-700 mb-2 block">JWT Token</label>
                <div className="text-xs font-mono text-gray-600 bg-white px-3 py-2 rounded border border-gray-200 break-all max-h-24 overflow-y-auto">
                  {(() => {
                    const { token } = authService.getAuth()
                    return token || '(未找到 token)'
                  })()}
                </div>
              </div>
              </div>
            </div>

            {/* 分割线 */}
            <div className="border-t border-gray-300 my-6"></div>

            {/* 所有用户列表 */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-md font-bold text-gray-900">所有用户列表</h4>
                <button
                  onClick={loadAllUsers}
                  className="text-xs text-blue-600 hover:text-blue-700"
                >
                  🔄 刷新
                </button>
              </div>

              {isLoading ? (
                <div className="text-center py-4 text-gray-500">加载中...</div>
              ) : allUsers.length === 0 ? (
                <div className="text-center py-4 text-gray-500">暂无用户数据</div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {allUsers.map((user) => {
                    const userPassword = passwordMapping[user.user_id]
                    const isCurrentUser = user.user_id === userId
                    
                    return (
                      <div
                        key={user.user_id}
                        className={`bg-gray-50 rounded-lg p-3 border ${
                          isCurrentUser ? 'border-blue-400 bg-blue-50' : 'border-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-semibold text-gray-900">
                              User {user.user_id}
                            </span>
                            {isCurrentUser && (
                              <span className="text-xs bg-blue-500 text-white px-2 py-0.5 rounded">
                                当前
                              </span>
                            )}
                          </div>
                          <button
                            onClick={() => handleCopyUserInfo(user.user_id, userPassword)}
                            className="text-xs text-blue-600 hover:text-blue-700"
                          >
                            复制
                          </button>
                        </div>
                        <div className="text-xs space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-500 w-16">密码:</span>
                            <span className="font-mono text-gray-700">
                              {userPassword || <span className="text-gray-400">(未记录)</span>}
                            </span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-500 w-16">创建:</span>
                            <span className="text-gray-600">
                              {new Date(user.created_at).toLocaleString('zh-CN', {
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {allUsers.length > 0 && (
                <div className="mt-3 text-xs text-gray-500 bg-yellow-50 border border-yellow-200 rounded p-2">
                  💡 提示：只显示在本浏览器登录过的用户密码
                </div>
              )}
            </div>

            {/* 关闭按钮 */}
            <button
              onClick={() => setShowDebugInfo(false)}
              className="w-full mt-6 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors font-medium"
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </>
  )
}

export default UserDebugButton


