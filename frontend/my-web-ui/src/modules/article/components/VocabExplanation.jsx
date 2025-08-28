import { useState } from 'react'

const VocabExplanation = ({ 
  word = "React", 
  definition = "一个用于构建用户界面的JavaScript库",
  isVisible = false,
  position = { x: 0, y: 0 }
}) => {
  const [isHovering, setIsHovering] = useState(false)

  // 如果不可见且不在hover状态，则不渲染
  if (!isVisible && !isHovering) return null

  // 边界检测和位置调整
  const getAdjustedPosition = () => {
    const cardWidth = 320 // 估计的卡片宽度
    const cardHeight = 120 // 估计的卡片高度
    const margin = 16 // 边距
    const verticalOffset = 40 // 垂直偏移量
    
    let adjustedX = position.x
    let adjustedY = position.y
    let showAbove = false // 是否显示在词汇上方
    
    // 检查左边界
    if (position.x - cardWidth / 2 < margin) {
      adjustedX = cardWidth / 2 + margin
    }
    
    // 检查右边界
    if (position.x + cardWidth / 2 > window.innerWidth - margin) {
      adjustedX = window.innerWidth - cardWidth / 2 - margin
    }
    
    // 检查下边界（确保卡片完全显示，包括偏移量）
    if (position.y + cardHeight + verticalOffset > window.innerHeight - margin) {
      adjustedY = position.y - cardHeight - 20
      showAbove = true
    }
    
    return { x: adjustedX, y: adjustedY, showAbove }
  }

  const adjustedPosition = getAdjustedPosition()

  return (
    <div
      className={`
        fixed z-50 pointer-events-none
        transition-all duration-300 ease-in-out
        ${isVisible || isHovering ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}
      `}
      style={{
        left: adjustedPosition.x,
        top: adjustedPosition.y,
        transform: adjustedPosition.showAbove 
          ? 'translate(-50%, -100%) translateY(-8px)' // 显示在上方
          : 'translate(-50%, 0) translateY(40px)' // 显示在下方，40px偏移
      }}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <div className="bg-gray-800 text-white px-3 py-2 rounded-lg shadow-lg text-sm leading-tight max-w-xs">
        <div className="font-medium mb-1">
          这个词的意思是...
        </div>
        <div className="text-gray-200">
          <span className="font-semibold text-blue-300">{word}</span>: {definition}
        </div>
      </div>
      
      {/* 小三角形指示器 */}
      <div 
        className={`absolute left-1/2 transform -translate-x-1/2 ${
          adjustedPosition.showAbove ? 'top-full' : 'bottom-full'
        }`}
        style={{ 
          [adjustedPosition.showAbove ? 'marginTop' : 'marginBottom']: '-1px' 
        }}
      >
        <div className={`w-0 h-0 border-l-4 border-r-4 border-transparent ${
          adjustedPosition.showAbove 
            ? 'border-t-4 border-t-gray-800' 
            : 'border-b-4 border-b-gray-800'
        }`}></div>
      </div>
    </div>
  )
}

export default VocabExplanation
