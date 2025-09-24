import { useState, useEffect } from 'react'

const ToastNotice = ({ 
  message = "知识点已总结加入列表", 
  duration = 2000, 
  onClose,
  isVisible = false 
}) => {
  const [isShowing, setIsShowing] = useState(false)
  const [isFading, setIsFading] = useState(false)

  useEffect(() => {
    if (isVisible) {
      setIsShowing(true)
      setIsFading(false)
      
      const timer = setTimeout(() => {
        setIsFading(true)
        
        // 先触发渐隐和上移动画，动画结束后再关闭
        const fadeTimer = setTimeout(() => {
          setIsFading(true) // 开始渐隐和上移
          // 1000ms后（动画结束）再隐藏（与下方 CSS 过渡时长一致）
          const hideTimer = setTimeout(() => {
            setIsShowing(false)
            onClose && onClose()
          }, 600)
          // 清理hideTimer
          return () => clearTimeout(hideTimer)
        }, 0) // 立即执行渐隐和上移
        return () => clearTimeout(fadeTimer)
      }, duration)
      
      return () => clearTimeout(timer)
    }
  }, [isVisible, duration])

  if (!isShowing) return null

  return (
    <div 
      className={`
        bg-blue-600 text-white px-4 py-3 rounded-lg shadow-lg
        transform transition-all duration-1000 ease-in-out
        ${isFading ? 'opacity-0 translate-y-6' : 'opacity-100 translate-y-0'}
        pointer-events-auto
        max-w-xs w-[320px]
      `}
    >
      <div className="flex items-start">
        <svg 
          className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" 
          fill="currentColor" 
          viewBox="0 0 20 20"
        >
          <path 
            fillRule="evenodd" 
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" 
            clipRule="evenodd" 
          />
        </svg>
        <div className="flex-1">
          <div className="font-medium leading-5 mb-0.5">知识点总结</div>
          <p className="text-sm leading-snug break-words">{message}</p>
        </div>
      </div>
    </div>
  )
}

export default ToastNotice
