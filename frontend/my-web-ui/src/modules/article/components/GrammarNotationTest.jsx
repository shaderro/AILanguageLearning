import { useState } from 'react'
import GrammarNotation from './GrammarNotation'

/**
 * GrammarNotationTest - 测试语法注释卡片功能的组件
 */
export default function GrammarNotationTest() {
  const [showNotation, setShowNotation] = useState(false)
  const [showCard, setShowCard] = useState(false)

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">语法注释卡片测试</h1>
      
      <div className="space-y-4">
        <div className="p-4 border rounded-lg">
          <h2 className="text-lg font-semibold mb-2">测试说明</h2>
          <p className="text-gray-600 mb-4">
            悬停在下面的语法注释下划线上，应该会显示语法注释卡片，包含该句子的所有语法规则信息。
          </p>
          
          <div className="flex gap-4 mb-4">
            <button
              onClick={() => setShowNotation(!showNotation)}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              {showNotation ? '隐藏' : '显示'} 语法注释
            </button>
            
            <button
              onClick={() => setShowCard(!showCard)}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              {showCard ? '隐藏' : '显示'} 卡片
            </button>
          </div>
        </div>

        {/* 测试句子 */}
        <div className="relative p-4 bg-gray-50 rounded-lg">
          <p className="text-lg leading-relaxed">
            这是一个测试句子，包含一些语法结构。
            <span className="relative inline-block">
              <span className="text-blue-600 font-medium">语法测试</span>
              {/* 语法注释下划线 */}
              <GrammarNotation
                isVisible={showNotation}
                textId={1}
                sentenceId={1}
                grammarId={1}
                markedTokenIds={[]}
                onMouseEnter={() => console.log('Mouse entered grammar notation')}
                onMouseLeave={() => console.log('Mouse left grammar notation')}
              />
            </span>
            继续句子的其余部分。
          </p>
        </div>

        {/* 模拟vocab notation和asked token */}
        <div className="p-4 bg-yellow-50 rounded-lg">
          <h3 className="font-semibold mb-2">测试交互优先级</h3>
          <p className="text-sm text-gray-600 mb-2">
            下面的元素用于测试悬停优先级：
          </p>
          
          <div className="flex gap-4">
            <span className="px-2 py-1 bg-green-200 rounded text-sm vocab-notation">
              词汇注释 (vocab-notation)
            </span>
            <span className="px-2 py-1 bg-red-200 rounded text-sm asked-token">
              已提问标记 (asked-token)
            </span>
          </div>
          
          <p className="text-xs text-gray-500 mt-2">
            当悬停在这些元素上时，语法注释卡片不应该显示。
          </p>
        </div>

        {/* 调试信息 */}
        <div className="p-4 bg-gray-100 rounded-lg">
          <h3 className="font-semibold mb-2">调试信息</h3>
          <div className="text-sm space-y-1">
            <div>语法注释显示: {showNotation ? '是' : '否'}</div>
            <div>卡片显示: {showCard ? '是' : '否'}</div>
            <div>文章ID: 1</div>
            <div>句子ID: 1</div>
            <div>语法规则ID: 1</div>
          </div>
        </div>
      </div>
    </div>
  )
}
