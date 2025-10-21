import { useState, useEffect } from 'react'
import { apiService } from '../../../services/api'

/**
 * TokenNotation - 显示已提问token的注释卡片
 * 
 * Props:
 * - isVisible: 是否显示
 * - note: 注释内容（暂时固定为测试文字）
 * - position: 定位信息（可选）
 */
export default function TokenNotation({ 
  isVisible = false, 
  note = "This is a test note", 
  position = {},
  textId = null,
  sentenceId = null,
  tokenIndex = null
}) {
  const [show, setShow] = useState(false)

  useEffect(() => {
    if (isVisible) {
      // 短暂延迟后显示，避免闪烁
      const timer = setTimeout(() => setShow(true), 150)
      
      // 调用 API 获取 vocab example 信息
      if (textId && sentenceId && tokenIndex) {
        console.log(`🔍 [TokenNotation] Fetching vocab example for:`, {
          textId,
          sentenceId, 
          tokenIndex
        })
        
        apiService.getVocabExampleByLocation(textId, sentenceId, tokenIndex)
          .then(response => {
            console.log(`✅ [TokenNotation] Vocab example result:`, response)
            // response 已经通过拦截器处理，直接是 vocab example 对象（或 null）
            if (response && response.vocab_id) {
              console.log(`📝 [TokenNotation] Found vocab example:`, {
                vocab_id: response.vocab_id,
                text_id: response.text_id,
                sentence_id: response.sentence_id,
                context_explanation: response.context_explanation,
                token_indices: response.token_indices
              })
            } else {
              console.log(`❌ [TokenNotation] No vocab example found for text_id=${textId}, sentence_id=${sentenceId}, token_index=${tokenIndex}`)
            }
          })
          .catch(error => {
            console.error(`❌ [TokenNotation] Error fetching vocab example:`, error)
          })
      }
      
      return () => clearTimeout(timer)
    } else {
      setShow(false)
    }
  }, [isVisible, textId, sentenceId, tokenIndex])

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

