import { useState, useEffect } from 'react'

const ToastNotice = ({ 
  message = "知识点已总结加入列表", 
  duration = 120000, // 调试阶段：2分钟
  onClose,
  isVisible = false 
}) => {
  // 🔧 修复：如果 isVisible 为 true，初始状态就应该是 showing
  const [isShowing, setIsShowing] = useState(isVisible)
  const [isFading, setIsFading] = useState(false)

  useEffect(() => {
    if (isVisible) {
      console.log('🍞 [ToastNotice] isVisible 为 true，设置 isShowing 为 true')
      setIsShowing(true)
      setIsFading(false)
      
      const timer = setTimeout(() => {
        console.log('🍞 [ToastNotice] 开始渐隐动画')
        setIsFading(true)
        
        // 动画结束后再关闭
        const hideTimer = setTimeout(() => {
          console.log('🍞 [ToastNotice] 隐藏 toast 并调用 onClose')
          setIsShowing(false)
          onClose && onClose()
        }, 1000) // 等待渐隐动画完成（duration-1000ms）
        
        return () => clearTimeout(hideTimer)
      }, duration)
      
      return () => clearTimeout(timer)
    } else {
      setIsShowing(false)
    }
  }, [isVisible, duration, onClose])

  console.log('🍞 [ToastNotice] 渲染，isVisible:', isVisible, 'isShowing:', isShowing, 'message:', message)

  if (!isShowing) {
    console.log('🍞 [ToastNotice] isShowing 为 false，不渲染')
    return null
  }

  // 解析消息，将知识点名称部分加粗
  const renderMessage = () => {
    const suffix = ' 知识点已总结并加入列表'
    if (message.endsWith(suffix)) {
      const knowledgePart = message.slice(0, -suffix.length)
      return (
        <>
          <span className="font-bold">{knowledgePart}</span>
          <span>{suffix}</span>
        </>
      )
    }
    // 如果没有匹配到标准格式，直接显示原消息
    return message
  }

  return (
    <div 
      className={`
        bg-success-200 text-black px-4 py-3 rounded-lg shadow-lg
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
          <p className="text-sm leading-snug break-words">{renderMessage()}</p>
        </div>
      </div>
    </div>
  )
}

export default ToastNotice
