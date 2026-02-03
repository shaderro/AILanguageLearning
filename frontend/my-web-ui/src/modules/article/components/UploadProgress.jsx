import { useState, useEffect } from 'react'
import { useUIText } from '../../../i18n/useUIText'

const UploadProgress = ({ onComplete, articleId = null }) => {
  const t = useUIText()
  const [currentStep, setCurrentStep] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)

  const steps = [
    { name: t('上传'), description: t('正在上传文件...') },
    { name: t('分句'), description: t('正在分析文章结构...') },
    { name: t('分词'), description: t('正在提取关键词...') },
    { name: t('建索引'), description: t('正在建立搜索索引...') },
    { name: t('处理'), description: t('正在处理文章内容...') }
  ]

  useEffect(() => {
    // 🔧 如果已经有 articleId，说明上传已完成，直接显示成功并跳转
    if (articleId) {
      console.log('✅ [UploadProgress] 检测到 articleId，上传已完成，准备跳转:', articleId)
      // 快速完成进度条动画
      let step = 0
      const fastInterval = setInterval(() => {
        step++
        setCurrentStep(step)
        if (step >= steps.length - 1) {
          clearInterval(fastInterval)
          // 显示成功动效
          setTimeout(() => {
            setIsComplete(true)
            setTimeout(() => {
              setShowSuccess(true)
              // 成功动效结束后调用完成回调，传递 articleId
              setTimeout(() => {
                onComplete && onComplete(articleId)
              }, 1500)
            }, 500)
          }, 300)
        }
      }, 300) // 快速完成动画
      return () => clearInterval(fastInterval)
    }

    // 🔧 当没有 articleId 时：只模拟推进到最后一步，然后“停住等待”
    // 不要在 articleId 为空时触发 onComplete(null)，否则会导致上传未完成就返回列表。
    const stepInterval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < steps.length - 1) {
          return prev + 1
        } else {
          clearInterval(stepInterval)
          // 到达最后一步后停住，等待 articleId 变为非空（由父组件传入）
          return prev
        }
      })
    }, 2000) // 🔧 延长每个步骤到2秒，让进度条更真实

    return () => clearInterval(stepInterval)
  }, [steps.length, onComplete, articleId])

  if (showSuccess) {
    return (
      <div className="flex-1 min-w-0 flex flex-col gap-4 bg-white p-6 rounded-lg shadow-md overflow-y-auto h-full">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            {/* 成功图标动画 */}
            <div className="mb-6">
              <div className="relative">
                <div className="w-16 h-16 bg-green-500 rounded-full mx-auto flex items-center justify-center animate-bounce">
                  <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
                {/* 扩散动画 */}
                <div className="absolute inset-0 w-16 h-16 bg-green-500 rounded-full mx-auto animate-ping opacity-75"></div>
              </div>
            </div>
            
            {/* 成功文字 */}
            <h2 className="text-3xl font-bold text-green-600 mb-2 animate-pulse">
              {t('上传成功！')}
            </h2>
            <p className="text-gray-600 text-lg">
              {t('文章已成功处理，正在跳转到阅读页面...')}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 min-w-0 flex flex-col gap-4 bg-white p-6 rounded-lg shadow-md overflow-y-auto h-full">
      <h2 className="text-xl font-semibold text-gray-800">{t('处理文章')}</h2>
      
      <div className="flex-1 flex items-center justify-center">
        <div className="w-full max-w-md">
          {/* 进度条 */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <span className="text-sm font-medium text-gray-700">{t('处理进度')}</span>
              <span className="text-sm text-gray-500">
                {Math.round(((currentStep + 1) / steps.length) * 100)}%
              </span>
            </div>
            
            {/* 主进度条 */}
            <div className="w-full bg-gray-200 rounded-full h-3 mb-6">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-1000 ease-out"
                style={{ 
                  width: `${((currentStep + 1) / steps.length) * 100}%` 
                }}
              ></div>
            </div>

            {/* 步骤指示器 */}
            <div className="flex justify-between">
              {steps.map((step, index) => (
                <div key={index} className="flex flex-col items-center">
                  <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-300
                    ${index <= currentStep 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-500'
                    }
                  `}>
                    {index < currentStep ? (
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      index + 1
                    )}
                  </div>
                  <span className={`
                    text-xs mt-2 text-center transition-colors duration-300
                    ${index <= currentStep ? 'text-blue-600 font-medium' : 'text-gray-500'}
                  `}>
                    {step.name}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 当前步骤描述 */}
          <div className="text-center">
            <div className="mb-4">
              <div className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full">
                <div className="w-2 h-2 bg-blue-600 rounded-full mr-2 animate-pulse"></div>
                <span className="text-sm font-medium">
                  {steps[currentStep]?.description || t('处理完成')}
                </span>
              </div>
            </div>
            
            {/* 加载动画 */}
            <div className="flex justify-center space-x-1">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default UploadProgress
