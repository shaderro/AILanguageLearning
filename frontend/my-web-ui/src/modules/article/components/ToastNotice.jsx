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
        
        const fadeTimer = setTimeout(() => {
          setIsShowing(false)
          onClose && onClose()
        }, 300) // 渐隐动画时间
        
        return () => clearTimeout(fadeTimer)
      }, duration)
      
      return () => clearTimeout(timer)
    }
  }, [isVisible, duration, onClose])

  if (!isShowing) return null

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none">
      <div 
        className={`
          bg-blue-600 text-white px-6 py-4 rounded-lg shadow-lg
          transform transition-all duration-300 ease-in-out
          ${isFading ? 'opacity-0 scale-95' : 'opacity-100 scale-100'}
          pointer-events-auto
        `}
        style={{
          aspectRatio: '4/3',
          minWidth: '280px',
          maxWidth: '400px'
        }}
      >
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="flex items-center justify-center mb-2">
              <svg 
                className="w-5 h-5 mr-2" 
                fill="currentColor" 
                viewBox="0 0 20 20"
              >
                <path 
                  fillRule="evenodd" 
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" 
                  clipRule="evenodd" 
                />
              </svg>
              <span className="font-medium">知识点总结</span>
            </div>
            <p className="text-sm leading-relaxed">
              {message}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ToastNotice
