import { useState, useEffect } from 'react'

const SuggestedQuestions = ({ 
  quotedText, 
  onQuestionSelect, 
  isVisible = false,
  inputValue = '',
  onQuestionClick 
}) => {
  const [selectedQuestion, setSelectedQuestion] = useState(null)

  const suggestedQuestions = [
    "这句话是什么意思？",
    "这句话的语法结构是什么？",
    "这个词汇怎么使用？",
    "能给我一个例句吗？"
  ]

  // 当组件显示时，重置选中状态
  useEffect(() => {
    if (isVisible) {
      setSelectedQuestion(null)
    }
  }, [isVisible])

  // 当输入框有内容时，取消高亮
  useEffect(() => {
    if (inputValue.trim() !== '') {
      setSelectedQuestion(null)
    }
  }, [inputValue])

  const handleQuestionClick = (question) => {
    setSelectedQuestion(question)
    onQuestionSelect(question)
    // 通知父组件问题被点击
    if (onQuestionClick) {
      onQuestionClick(question)
    }
  }

  // 点击其他位置取消高亮
  const handleContainerClick = (e) => {
    // 如果点击的是容器而不是按钮，取消高亮
    if (e.target === e.currentTarget) {
      setSelectedQuestion(null)
    }
  }

  if (!isVisible || !quotedText) return null

  return (
    <div 
      className="w-full bg-gray-50 border-t border-gray-200 px-4 py-3"
      onClick={handleContainerClick}
    >
      <div className="text-sm text-gray-600 mb-2">
        你可能想问...
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestedQuestions.map((question, index) => (
          <button
            key={index}
            onClick={() => handleQuestionClick(question)}
            className={`
              px-3 py-1.5 text-sm rounded-lg border transition-all duration-200
              ${selectedQuestion === question
                ? 'bg-blue-500 text-white border-blue-500 shadow-sm'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700'
              }
            `}
          >
            "{question}"
          </button>
        ))}
      </div>
    </div>
  )
}

export default SuggestedQuestions
