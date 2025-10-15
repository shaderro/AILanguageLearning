import { useState, useEffect } from 'react'

/**
 * TokenNotation - 显示已提问token的注释卡片
 * 
 * Props:
 * - isVisible: 是否显示
 * - note: 注释内容（暂时固定为测试文字）
 * - position: 定位信息（可选）
 */
export default function TokenNotation({ isVisible = false, note = "This is a test note", position = {} }) {
  const [show, setShow] = useState(false)

  useEffect(() => {
    if (isVisible) {
      // 短暂延迟后显示，避免闪烁
      const timer = setTimeout(() => setShow(true), 150)
      return () => clearTimeout(timer)
    } else {
      setShow(false)
    }
  }, [isVisible])

  if (!show) return null

  return (
    <div 
      className="absolute top-full left-0 mt-1 z-50 transition-opacity duration-200"
      style={{
        minWidth: '200px',
        maxWidth: '300px',
        opacity: show ? 1 : 0,
        ...position
      }}
    >
      {/* 小箭头 */}
      <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-200 transform rotate-45 border-l border-t border-gray-300"></div>
      
      {/* 卡片主体 - 浅灰底、深灰色文字 */}
      <div className="bg-gray-100 border border-gray-300 rounded-lg shadow-lg p-3">
        <div className="text-sm text-gray-700 leading-relaxed">
          {note}
        </div>
      </div>
    </div>
  )
}

