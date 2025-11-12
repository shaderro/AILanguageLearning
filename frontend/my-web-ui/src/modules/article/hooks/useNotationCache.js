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

    // 移除详细日志（已通过测试，减少不必要的日志输出）
    setIsLoading(true)
    setError(null)

    try {
      // 并行加载grammar notations和vocab notations
      const [grammarResponse, vocabResponse] = await Promise.all([
        apiService.getGrammarNotations(textId),
        apiService.getVocabNotations(textId)
      ])

      // 移除详细响应日志（功能已通过测试）

      // 处理grammar notations
      console.log('🔍 [useNotationCache] Grammar response:', grammarResponse)
      if (grammarResponse && grammarResponse.data) {
        const grammarData = grammarResponse.data.notations || grammarResponse.data
        const grammarList = Array.isArray(grammarData) ? grammarData : []
        console.log('📝 [useNotationCache] Loaded grammar notations:', grammarList.length, grammarList)
        setGrammarNotations(grammarList)

        // 预加载所有grammar rules
        const grammarRulesMap = new Map()
        for (const notation of grammarList) {
          if (notation.grammar_id && !grammarRulesMap.has(notation.grammar_id)) {
            try {
              const ruleResponse = await apiService.getGrammarById(notation.grammar_id)
              if (ruleResponse && ruleResponse.data) {
                grammarRulesMap.set(notation.grammar_id, ruleResponse.data)
                console.log('📚 [useNotationCache] Cached grammar rule:', notation.grammar_id, ruleResponse.data.rule_name)
              }
            } catch (err) {
              console.warn('⚠️ [useNotationCache] Failed to load grammar rule:', notation.grammar_id, err)
            }
          }
        }
        setGrammarRulesCache(grammarRulesMap)
        console.log('✅ [useNotationCache] Grammar cache ready:', grammarRulesMap.size, 'rules')
      }

      // 处理vocab notations（新API）
      console.log('🔍 [useNotationCache] Vocab response:', vocabResponse)
      console.log('🔍 [useNotationCache] vocabResponse.success:', vocabResponse?.success)
      console.log('🔍 [useNotationCache] vocabResponse.data:', vocabResponse?.data)
      
      if (vocabResponse && vocabResponse.success && vocabResponse.data) {
        // 新API返回格式：{ success: true, data: { notations: [...], count: N } }
        const vocabData = vocabResponse.data.notations || vocabResponse.data
        const vocabList = Array.isArray(vocabData) ? vocabData : []
        
        console.log('📝 [useNotationCache] vocabData:', vocabData)
        console.log('📝 [useNotationCache] vocabList length:', vocabList.length)
        console.log('📝 [useNotationCache] vocabList:', vocabList)
        
        // 转换为前端使用的格式（确保有token_index字段）
        const formattedVocabNotations = vocabList.map(notation => ({
          user_id: notation.user_id,
          text_id: notation.text_id,
          sentence_id: notation.sentence_id,
          token_id: notation.token_id,
          token_index: notation.token_id, // 添加token_index字段作为别名
          vocab_id: notation.vocab_id,
          created_at: notation.created_at
        }))
        
        console.log('✅ [useNotationCache] Formatted vocab notations:', formattedVocabNotations)
        setVocabNotations(formattedVocabNotations)
        // 不再预加载所有 examples：改为按需懒加载 + 新建后单次写缓存
      } else if (vocabResponse && vocabResponse.data) {
        // 兼容旧的API格式（直接从data中获取数组）
        const vocabData = Array.isArray(vocabResponse.data) ? vocabResponse.data : []
        const formattedVocabNotations = vocabData.map(notation => ({
          user_id: notation.user_id,
          text_id: notation.text_id,
          sentence_id: notation.sentence_id,
          token_id: notation.token_id,
          token_index: notation.token_id,
          vocab_id: notation.vocab_id,
          created_at: notation.created_at
        }))
        setVocabNotations(formattedVocabNotations)
        // 不再预加载所有 examples：改为按需懒加载 + 新建后单次写缓存
      } else {
        console.warn('⚠️ [useNotationCache] No vocab notations found or invalid response format')
        setVocabNotations([])
      }

      setIsInitialized(true)
      // 移除成功日志（已通过测试）

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
    // 确保类型一致（数字比较）
    const sid = Number(sentenceId)
    
    const filtered = vocabNotations.filter(notation => 
      Number(notation.sentence_id) === sid
    )
    
    return filtered
  }, [vocabNotations])

  // 获取特定token的vocab example（通过API按需获取）
  const getVocabExampleForToken = useCallback(async (textId, sentenceId, tokenIndex) => {
    const key = `${textId}:${sentenceId}:${tokenIndex}`
    
    // 首先检查缓存
    if (vocabExamplesCache.has(key)) {
      return vocabExamplesCache.get(key)
    }
    
    // 如果缓存中没有，通过API获取
    try {
      const { apiService } = await import('../../../services/api')
      const axiosResp = await apiService.getVocabExampleByLocation(textId, sentenceId, tokenIndex)
      // axiosResp -> { data: { success, data } } in mock
      const payload = axiosResp?.data?.data ?? axiosResp?.data ?? axiosResp

      if (payload && payload.vocab_id) {
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

  // 创建vocab notation（使用新API）
  const createVocabNotation = useCallback(async (textId, sentenceId, tokenId, vocabId = null, userId = 'default_user') => {
    try {
      console.log('➕ [useNotationCache] Creating vocab notation:', { textId, sentenceId, tokenId, vocabId, userId })
      
      const response = await apiService.createVocabNotation(userId, textId, sentenceId, tokenId, vocabId)
      
      // 处理响应（可能从拦截器返回不同的格式）
      const result = response?.data || response
      const success = result?.success !== false && (result?.success === true || response?.status === 200)
      
      if (success) {
        // 创建vocab notation对象
        const newNotation = {
          user_id: userId,
          text_id: textId,
          sentence_id: sentenceId,
          token_id: tokenId,
          token_index: tokenId,  // 添加token_index作为别名
          vocab_id: vocabId,
          created_at: new Date().toISOString()
        }
        
        // 添加到缓存
        addVocabNotationToCache(newNotation)
        
        // 只拉取一次该位置的 example 并写入缓存，避免后续悬浮重复请求
        try {
          const exampleResp = await apiService.getVocabExampleByLocation(textId, sentenceId, tokenId)
          const payload = exampleResp?.data?.data ?? exampleResp?.data ?? exampleResp
          if (payload && (payload.vocab_id || vocabId)) {
            const example = {
              vocab_id: payload.vocab_id ?? vocabId,
              text_id: textId,
              sentence_id: sentenceId,
              token_index: payload.token_index ?? tokenId,
              context_explanation: payload.context_explanation || '',
              token_indices: payload.token_indices || [tokenId]
            }
            const key = `${textId}:${sentenceId}:${example.token_index}`
            setVocabExamplesCache(prev => {
              const next = new Map(prev)
              next.set(key, example)
              return next
            })
            console.log('✅ [useNotationCache] Cached vocab example for new notation:', example)
          }
        } catch (e) {
          console.warn('⚠️ [useNotationCache] Failed to fetch example for new notation (cached will be missing until first hover fetch):', e?.message || e)
        }
        
        console.log('✅ [useNotationCache] Vocab notation created and added to cache:', newNotation)
        return { success: true, notation: newNotation }
      } else {
        console.error('❌ [useNotationCache] Failed to create vocab notation:', result?.error || 'Unknown error')
        return { success: false, error: result?.error || 'Unknown error' }
      }
    } catch (error) {
      console.error('❌ [useNotationCache] Error creating vocab notation:', error)
      return { success: false, error: error.message || 'Failed to create vocab notation' }
    }
  }, [addVocabNotationToCache])

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
    addVocabExampleToCache,
    
    // 创建功能（新API）
    createVocabNotation
  }
}
