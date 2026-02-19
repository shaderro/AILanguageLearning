/**
 * 用户头像组件
 * 显示已登录用户的信息和登出选项
 */
import { useState } from 'react'
import { useUiLanguage } from '../../../contexts/UiLanguageContext'
import { colors } from '../../../design-tokens'

const UserAvatar = ({ userId, email, onLogout, onOpenProfile }) => {
  const [showMenu, setShowMenu] = useState(false)
  const { uiLanguage } = useUiLanguage()

  const labels = uiLanguage === 'en'
    ? {
        currentUser: 'Current user',
        profile: 'Profile & Settings',
        logout: 'Sign out',
        user: 'User'
      }
    : {
        currentUser: '当前用户',
        profile: '个人中心与设置',
        logout: '登出',
        user: '用户'
      }

  // 🔧 顶部仅显示 "User"（不带 ID），头像为纯色圆点
  const displayText = labels.user

  return (
    <div className="relative">
      {/* 用户头像按钮 */}
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center space-x-2 px-3 py-2 rounded-md hover:bg-gray-100 transition-colors"
      >
        {/* 头像图标：纯色圆点，不显示文字 */}
        <div 
          className="w-8 h-8 rounded-full"
          style={{ backgroundColor: colors.primary[400] }}
        />
        
        {/* 文本：固定显示 User，不展示 ID 或邮箱 */}
        <span className="text-sm font-medium text-gray-700">
          {displayText}
        </span>

        {/* 下拉箭头 */}
        <svg 
          className={`w-4 h-4 text-gray-500 transition-transform ${showMenu ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* 下拉菜单 */}
      {showMenu && (
        <>
          {/* 点击外部关闭菜单 */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setShowMenu(false)}
          />
          
          {/* 菜单内容 */}
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-20">
            <div className="py-1">
              {/* 仅保留设置与退出登录 */}
              <button
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                onClick={() => {
                  setShowMenu(false)
                  if (onOpenProfile) {
                    onOpenProfile()
                  }
                }}
              >
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span>{labels.profile}</span>
                </div>
              </button>

              {/* 分割线 */}
              <div className="border-t border-gray-200 my-1" />

              {/* 登出按钮 */}
              <button
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                onClick={() => {
                  setShowMenu(false)
                  onLogout()
                }}
              >
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  <span>{labels.logout}</span>
                </div>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default UserAvatar


