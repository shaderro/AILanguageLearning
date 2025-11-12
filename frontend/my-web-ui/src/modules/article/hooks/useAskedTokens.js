import { useState, useEffect } from 'react'
import { apiService } from '../../../services/api'

/**
 * Custom hook to manage asked tokens state
 */
export function useAskedTokens(articleId, userId = 'default_user') {
  const [askedTokenKeys, setAskedTokenKeys] = useState(() => new Set())
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  // 获取已提问的tokens
  useEffect(() => {
    if (!articleId) return
    
    // 🔧 检查articleId是否为有效数字（上传模式下可能是字符串'upload'）
    const textId = typeof articleId === 'string' && articleId === 'upload' ? null : articleId
    if (!textId || (typeof textId === 'string' && isNaN(parseInt(textId)))) {
      // 跳过无效的textId（如上载模式）
      setAskedTokenKeys(new Set())
      return
    }

    const fetchAskedTokens = async () => {
      setIsLoading(true)
      setError(null)
      
      try {
        // 移除详细日志（已通过测试，减少不必要的日志输出）
        const response = await apiService.getAskedTokens(userId, textId)
        
        if (response.success && response.data?.asked_tokens) {
          const tokens = new Set(response.data.asked_tokens)
          setAskedTokenKeys(tokens)
        } else {
          setAskedTokenKeys(new Set())
        }
      } catch (err) {
        console.error('❌ [useAskedTokens] Failed to fetch asked tokens:', err)
        setError(err)
        setAskedTokenKeys(new Set())
      } finally {
        setIsLoading(false)
      }
    }

    fetchAskedTokens()
  }, [articleId, userId])

  // 检查token是否已提问
  const isTokenAsked = (textId, sentenceId, sentenceTokenId) => {
    const key = `${textId}:${sentenceId}:${sentenceTokenId}`
    return askedTokenKeys.has(key)
  }

  // 标记token为已提问
  const markAsAsked = async (textId, sentenceId, sentenceTokenId, vocabId = null, grammarId = null) => {
    try {
      const response = await apiService.markTokenAsked(userId, textId, sentenceId, sentenceTokenId, vocabId, grammarId)
      
      if (response.success) {
        const key = `${textId}:${sentenceId}:${sentenceTokenId}`
        setAskedTokenKeys(prev => new Set([...prev, key]))
        console.log('✅ [AskedTokens] Token marked:', key, { vocabId, grammarId })
        return true
      } else {
        console.error('❌ [AskedTokens] Failed to mark token:', response.error)
        return false
      }
    } catch (err) {
      console.error('❌ [AskedTokens] Error:', err)
      return false
    }
  }

  // 刷新asked tokens（从服务器重新获取）
  const refreshAskedTokens = async () => {
    // 🔧 检查articleId是否为有效数字
    const textId = typeof articleId === 'string' && articleId === 'upload' ? null : articleId
    if (!textId || (typeof textId === 'string' && isNaN(parseInt(textId)))) {
      console.warn('⚠️ [AskedTokens] Cannot refresh: invalid articleId', articleId)
      return false
    }
    
    try {
      console.log('🔄 [AskedTokens] Refreshing asked tokens...')
      const response = await apiService.getAskedTokens(userId, textId)
      
      if (response.success && response.data?.asked_tokens) {
        const tokens = new Set(response.data.asked_tokens)
        console.log('✅ [AskedTokens] Refreshed', tokens.size, 'asked tokens for article', articleId)
        setAskedTokenKeys(tokens)
        return true
      } else {
        console.warn('⚠️ [AskedTokens] No asked tokens found during refresh')
        return false
      }
    } catch (err) {
      console.error('❌ [AskedTokens] Failed to refresh asked tokens:', err)
      return false
    }
  }

  return {
    askedTokenKeys,
    isLoading,
    error,
    isTokenAsked,
    markAsAsked,
    refreshAskedTokens
  }
}

