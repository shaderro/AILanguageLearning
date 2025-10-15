import { useState, useCallback } from 'react'

/**
 * Custom hook to manage token notation content
 * 
 * 用于管理每个token的notation内容
 * 
 * 返回:
 * - notations: Map对象，存储每个token的notation内容
 * - getNotationContent: 获取指定token的notation内容
 * - setNotationContent: 设置指定token的notation内容
 * - clearNotationContent: 清除指定token的notation内容
 * - clearAllNotations: 清除所有notation内容
 */
export function useTokenNotations() {
  // 使用Map存储notation内容
  // key: "textId:sentenceId:tokenId"
  // value: notation content (string)
  const [notations, setNotations] = useState(() => new Map())

  /**
   * 获取指定token的notation内容
   * 
   * @param {number} textId - 文章ID
   * @param {number} sentenceId - 句子ID
   * @param {number} tokenId - Token ID
   * @returns {string|null} - Notation内容，如果没有则返回null
   */
  const getNotationContent = useCallback((textId, sentenceId, tokenId) => {
    const key = `${textId}:${sentenceId}:${tokenId}`
    return notations.get(key) || null
  }, [notations])

  /**
   * 设置指定token的notation内容
   * 
   * @param {number} textId - 文章ID
   * @param {number} sentenceId - 句子ID
   * @param {number} tokenId - Token ID
   * @param {string} content - Notation内容
   * 
   * 使用示例:
   *   setNotationContent(1, 5, 12, "这是一个重要的词汇")
   */
  const setNotationContent = useCallback((textId, sentenceId, tokenId, content) => {
    const key = `${textId}:${sentenceId}:${tokenId}`
    
    console.log(`📝 [TokenNotations] Setting notation for ${key}:`, content)
    
    setNotations(prev => {
      const newMap = new Map(prev)
      newMap.set(key, content)
      return newMap
    })
  }, [])

  /**
   * 清除指定token的notation内容
   * 
   * @param {number} textId - 文章ID
   * @param {number} sentenceId - 句子ID
   * @param {number} tokenId - Token ID
   */
  const clearNotationContent = useCallback((textId, sentenceId, tokenId) => {
    const key = `${textId}:${sentenceId}:${tokenId}`
    
    console.log(`🗑️ [TokenNotations] Clearing notation for ${key}`)
    
    setNotations(prev => {
      const newMap = new Map(prev)
      newMap.delete(key)
      return newMap
    })
  }, [])

  /**
   * 清除所有notation内容
   */
  const clearAllNotations = useCallback(() => {
    console.log('🗑️ [TokenNotations] Clearing all notations')
    setNotations(new Map())
  }, [])

  return {
    notations,
    getNotationContent,
    setNotationContent,
    clearNotationContent,
    clearAllNotations
  }
}


