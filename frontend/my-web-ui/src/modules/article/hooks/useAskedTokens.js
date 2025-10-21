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

    const fetchAskedTokens = async () => {
      setIsLoading(true)
      setError(null)
      
      try {
        const response = await apiService.getAskedTokens(userId, articleId)
        
        if (response.success && response.data?.asked_tokens) {
          const tokens = new Set(response.data.asked_tokens)
          console.log('✅ [AskedTokens] Loaded', tokens.size, 'asked tokens for article', articleId)
          setAskedTokenKeys(tokens)
        } else {
          console.warn('⚠️ [useAskedTokens] No asked tokens found')
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

  return {
    askedTokenKeys,
    isLoading,
    error,
    isTokenAsked,
    markAsAsked
  }
}

