import { useState } from 'react'
import VocabExplanation from './VocabExplanation'

export default function ArticleViewer({ text, onTokenSelect }) {
  const [selectedTokens, setSelectedTokens] = useState(new Set())
  const [vocabPosition, setVocabPosition] = useState({ x: 0, y: 0 })
  const [showVocab, setShowVocab] = useState(false)
  const [currentVocabWord, setCurrentVocabWord] = useState('')
  const [currentVocabDefinition, setCurrentVocabDefinition] = useState('')

  // 重点词汇列表（测试阶段随机设置）
  const importantWords = new Set([
    'React', 'JavaScript', '组件', '虚拟DOM', 'JSX', '状态', '生命周期', '事件处理'
  ])

  // 重点词汇定义
  const vocabDefinitions = {
    'React': '一个用于构建用户界面的JavaScript库，由Facebook开发和维护，被广泛用于构建单页应用程序。',
    'JavaScript': '一种高级的、解释型的编程语言，主要用于网页开发，支持面向对象、命令式和声明式编程风格。',
    '组件': 'React中的基本构建块，是可重用的UI元素，可以是函数组件或类组件。',
    '虚拟DOM': 'React的核心概念，是一个轻量级的JavaScript对象，用于描述真实DOM的结构，提高渲染性能。',
    'JSX': 'JavaScript XML的缩写，是React中用于描述UI的语法扩展，让组件的编写更加直观。',
    '状态': 'React组件中的数据，当状态改变时会触发组件重新渲染，是组件交互的核心。',
    '生命周期': 'React组件从创建到销毁的整个过程，包括挂载、更新和卸载三个阶段。',
    '事件处理': 'React中处理用户交互的方式，使用驼峰命名法，如onClick、onChange等。'
  }

  // Split text into tokens by spaces and punctuation
  const tokens = text.split(/\s+/).filter(token => token.length > 0)

  const handleTokenClick = (token) => {
    const newSelectedTokens = new Set(selectedTokens)
    
    if (newSelectedTokens.has(token)) {
      newSelectedTokens.delete(token)
    } else {
      newSelectedTokens.add(token)
    }
    
    setSelectedTokens(newSelectedTokens)
    
    // Call the callback function
    if (onTokenSelect) {
      onTokenSelect(token, newSelectedTokens)
    }
  }

  const handleVocabHover = (event, token) => {
    const rect = event.currentTarget.getBoundingClientRect()
    setVocabPosition({
      x: rect.left + rect.width / 2,
      y: rect.top
    })
    setCurrentVocabWord(token)
    setCurrentVocabDefinition(vocabDefinitions[token] || '暂无定义')
    setShowVocab(true)
  }

  const handleVocabLeave = () => {
    setShowVocab(false)
  }

  return (
    <div className="flex-1 min-w-0 flex flex-col gap-4 bg-white p-6 rounded-lg shadow-md overflow-y-auto h-full">
      <h2 className="text-xl font-semibold text-gray-800">文章查看器</h2>
      
      <div className="flex flex-wrap gap-2 leading-relaxed">
        {tokens.map((token, index) => {
          const isSelected = selectedTokens.has(token)
          const isImportantWord = importantWords.has(token)
          
          return (
            <span
              key={`${token}-${index}`}
              onClick={() => handleTokenClick(token)}
              onMouseEnter={isImportantWord ? (e) => handleVocabHover(e, token) : undefined}
              onMouseLeave={isImportantWord ? handleVocabLeave : undefined}
              className={`
                cursor-pointer px-2 py-1 rounded transition-all duration-200 hover:bg-blue-100
                ${isSelected 
                  ? 'bg-blue-500 text-white hover:bg-blue-600' 
                  : isImportantWord
                    ? 'bg-yellow-50 text-gray-800 hover:bg-yellow-100 font-bold'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }
              `}
            >
              {token}
            </span>
          )
        })}
      </div>
      
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">
          已选择 <span className="font-semibold text-blue-600">{selectedTokens.size}</span> 个词汇
          {selectedTokens.size > 0 && (
            <span className="ml-2">
              (重点词汇: <span className="font-semibold text-yellow-600">
                {Array.from(selectedTokens).filter(token => importantWords.has(token)).length}
              </span>)
            </span>
          )}
        </p>
        {selectedTokens.size > 0 && (
          <p className="text-xs text-gray-500 mt-1">
            选中: {Array.from(selectedTokens).join(', ')}
          </p>
        )}
        <p className="text-xs text-gray-500 mt-2">
          重点词汇: <span className="font-semibold text-yellow-600">{importantWords.size}</span> 个
          <span className="ml-2 text-gray-400">
            (加粗显示，hover查看解释)
          </span>
        </p>
      </div>

      {/* Vocab Explanation */}
      <VocabExplanation
        word={currentVocabWord}
        definition={currentVocabDefinition}
        isVisible={showVocab}
        position={vocabPosition}
      />
    </div>
  )
} 