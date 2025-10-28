import { useState, useEffect, useCallback } from 'react'
import { apiService } from '../../../services/api'

/**
 * 统一的Notation缓存管理器
 * 在文章页面加载时预加载所有grammar notation和vocab notation数据
 */
export function useNotationCache(articleId) {
  // Grammar notations缓存
  const [grammarNotations, setGrammarNotations] = useState([])
  const [grammarRulesCache, setGrammarRulesCache] = useState(new Map()) // grammarId -> grammarRule
  
  // Vocab notations缓存
  const [vocabNotations, setVocabNotations] = useState([])
  const [vocabExamplesCache, setVocabExamplesCache] = useState(new Map()) // key -> vocabExample
  
  // 加载状态
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [isInitialized, setIsInitialized] = useState(false)

  // 预加载所有数据
  const loadAllNotations = useCallback(async (textId) => {
    if (!textId) return

    console.log('🚀 [useNotationCache] Starting to load all notations for textId:', textId)
    setIsLoading(true)
    setError(null)

    try {
      // 只加载grammar notations，vocab examples通过单独的API获取
      const grammarResponse = await apiService.getGrammarNotations(textId)

      console.log('🔍 [useNotationCache] Grammar notations response:', grammarResponse)

      // 处理grammar notations
      if (grammarResponse && grammarResponse.data) {
        const grammarData = Array.isArray(grammarResponse.data) ? grammarResponse.data : []
        setGrammarNotations(grammarData)
        console.log('✅ [useNotationCache] Loaded grammar notations:', grammarData.length)
        console.log('🔍 [useNotationCache] Grammar notations data:', grammarData)

        // 预加载所有grammar rules
        const grammarRulesMap = new Map()
        for (const notation of grammarData) {
          if (notation.grammar_id && !grammarRulesMap.has(notation.grammar_id)) {
            try {
              const ruleResponse = await apiService.getGrammarById(notation.grammar_id)
              if (ruleResponse && ruleResponse.data) {
                grammarRulesMap.set(notation.grammar_id, ruleResponse.data)
                console.log('✅ [useNotationCache] Cached grammar rule:', notation.grammar_id)
              }
            } catch (err) {
              console.warn('⚠️ [useNotationCache] Failed to load grammar rule:', notation.grammar_id, err)
            }
          }
        }
        setGrammarRulesCache(grammarRulesMap)
        console.log('✅ [useNotationCache] Cached grammar rules:', grammarRulesMap.size)
      }

      // Vocab examples通过单独的API按需获取，不在这里预加载
      console.log('ℹ️ [useNotationCache] Vocab examples will be loaded on-demand via API')

      setIsInitialized(true)
      console.log('🎉 [useNotationCache] All notations loaded successfully!')

    } catch (err) {
      console.error('❌ [useNotationCache] Error loading notations:', err)
      setError(err.message || 'Failed to load notations')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 初始化加载
  useEffect(() => {
    if (articleId && !isInitialized) {
      loadAllNotations(articleId)
    }
  }, [articleId, isInitialized, loadAllNotations])

  // 获取句子的grammar notations
  const getGrammarNotationsForSentence = useCallback((sentenceId) => {
    return grammarNotations.filter(notation => 
      notation.sentence_id === sentenceId
    )
  }, [grammarNotations])

  // 获取句子的vocab notations
  const getVocabNotationsForSentence = useCallback((sentenceId) => {
    return vocabNotations.filter(notation => 
      notation.sentence_id === sentenceId
    )
  }, [vocabNotations])

  // 获取特定token的vocab example（通过API按需获取）
  const getVocabExampleForToken = useCallback(async (textId, sentenceId, tokenIndex) => {
    const key = `${textId}:${sentenceId}:${tokenIndex}`
    console.log('🔍 [getVocabExampleForToken] Looking for key:', key)
    
    // 首先检查缓存
    if (vocabExamplesCache.has(key)) {
      console.log('✅ [getVocabExampleForToken] Found in cache:', key)
      return vocabExamplesCache.get(key)
    }
    
    // 如果缓存中没有，通过API获取
    console.log('🔍 [getVocabExampleForToken] Not in cache, fetching from API...')
    try {
      const { apiService } = await import('../../../services/api')
      const axiosResp = await apiService.getVocabExampleByLocation(textId, sentenceId, tokenIndex)
      // axiosResp -> { data: { success, data } } in mock
      const payload = axiosResp?.data?.data ?? axiosResp?.data ?? axiosResp
      console.log('📥 [getVocabExampleForToken] Raw API response:', axiosResp)
      console.log('📦 [getVocabExampleForToken] Parsed payload:', payload)

      if (payload && payload.vocab_id) {
        console.log('✅ [getVocabExampleForToken] Fetched from API (parsed):', payload)
        // 标准化：确保有 token_index 供缓存 key 使用
        const normalized = {
          vocab_id: payload.vocab_id,
          text_id: payload.text_id,
          sentence_id: payload.sentence_id,
          token_index: payload.token_index ?? tokenIndex,
          context_explanation: payload.context_explanation,
          token_indices: payload.token_indices || []
        }
        setVocabExamplesCache(prev => {
          const newCache = new Map(prev)
          newCache.set(key, normalized)
          return newCache
        })
        return normalized
      } else {
        console.log('❌ [getVocabExampleForToken] No vocab example found for:', key)
        return null
      }
    } catch (error) {
      console.error('❌ [getVocabExampleForToken] API error:', error)
      return null
    }
  }, [vocabExamplesCache])

  // 获取grammar rule详情
  const getGrammarRuleById = useCallback((grammarId) => {
    return grammarRulesCache.get(grammarId) || null
  }, [grammarRulesCache])

  // 检查句子是否有grammar notation
  const hasGrammarNotation = useCallback((sentenceId) => {
    return grammarNotations.some(notation => 
      notation.sentence_id === sentenceId
    )
  }, [grammarNotations])

  // 检查句子是否有vocab notation
  const hasVocabNotation = useCallback((sentenceId) => {
    return vocabNotations.some(notation => 
      notation.sentence_id === sentenceId
    )
  }, [vocabNotations])

  // 刷新缓存（当有新的notation被创建时调用）
  const refreshCache = useCallback(() => {
    if (articleId) {
      console.log('🔄 [useNotationCache] Refreshing cache for articleId:', articleId)
      setIsInitialized(false)
      loadAllNotations(articleId)
    }
  }, [articleId, loadAllNotations])

  // 添加新的grammar notation到缓存
  const addGrammarNotationToCache = useCallback((notation) => {
    console.log('➕ [useNotationCache] Adding grammar notation to cache:', notation)
    setGrammarNotations(prev => {
      // 检查是否已存在，避免重复添加
      const exists = prev.some(n => 
        n.text_id === notation.text_id && 
        n.sentence_id === notation.sentence_id && 
        n.grammar_id === notation.grammar_id
      )
      if (exists) {
        console.log('⚠️ [useNotationCache] Grammar notation already exists in cache')
        return prev
      }
      return [...prev, notation]
    })
  }, [])

  // 添加新的vocab notation到缓存
  const addVocabNotationToCache = useCallback((notation) => {
    console.log('➕ [useNotationCache] Adding vocab notation to cache:', notation)
    setVocabNotations(prev => {
      // 检查是否已存在，避免重复添加
      const exists = prev.some(n => 
        n.text_id === notation.text_id && 
        n.sentence_id === notation.sentence_id && 
        n.token_index === notation.token_index
      )
      if (exists) {
        console.log('⚠️ [useNotationCache] Vocab notation already exists in cache')
        return prev
      }
      return [...prev, notation]
    })
  }, [])

  // 添加新的grammar rule到缓存
  const addGrammarRuleToCache = useCallback((rule) => {
    console.log('➕ [useNotationCache] Adding grammar rule to cache:', rule)
    setGrammarRulesCache(prev => {
      const newCache = new Map(prev)
      newCache.set(rule.rule_id, rule)
      return newCache
    })
  }, [])

  // 添加新的vocab example到缓存
  const addVocabExampleToCache = useCallback((example) => {
    console.log('➕ [useNotationCache] Adding vocab example to cache:', example)
    const key = `${example.text_id}:${example.sentence_id}:${example.token_index}`
    setVocabExamplesCache(prev => {
      const newCache = new Map(prev)
      newCache.set(key, example)
      return newCache
    })
  }, [])

  return {
    // 状态
    isLoading,
    error,
    isInitialized,
    
    // Grammar notations
    grammarNotations,
    getGrammarNotationsForSentence,
    getGrammarRuleById,
    hasGrammarNotation,
    
    // Vocab notations
    vocabNotations,
    getVocabNotationsForSentence,
    getVocabExampleForToken,
    hasVocabNotation,
    
    // 缓存管理
    refreshCache,
    
    // 实时缓存更新
    addGrammarNotationToCache,
    addVocabNotationToCache,
    addGrammarRuleToCache,
    addVocabExampleToCache
  }
}
