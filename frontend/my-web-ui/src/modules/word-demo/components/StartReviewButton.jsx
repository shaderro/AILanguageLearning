const StartReviewButton = ({ 
  onClick, 
  text = "Start Review", 
  className = "",
  position = "bottom-1/4", // 可自定义位置
  showIcon = true,
  disabled = false,
  loading = false
}) => {
  const baseClasses = `
    fixed left-1/2 transform -translate-x-1/2 z-40
    bg-green-500 hover:bg-green-600 text-white font-semibold py-3 px-8 
    rounded-full shadow-lg hover:shadow-xl transition-all duration-300 
    transform hover:scale-105 active:scale-95
    ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
    ${loading ? 'animate-pulse' : ''}
    ${className}
  `

  return (
    <div className={`fixed ${position} left-1/2 transform -translate-x-1/2 z-40`}>
      <button
        onClick={onClick}
        disabled={disabled || loading}
        className={baseClasses}
      >
        <div className="flex items-center space-x-2">
          {loading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
          ) : showIcon ? (
            <svg 
              className="w-5 h-5" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
              />
            </svg>
          ) : null}
          <span>{loading ? 'Loading...' : text}</span>
        </div>
      </button>
    </div>
  )
}

export default StartReviewButton 