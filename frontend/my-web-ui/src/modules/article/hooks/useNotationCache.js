import { useState, useEffect, useCallback, useRef } from 'react'
import { apiService } from '../../../services/api'
import { logVocabNotationDebug } from '../utils/vocabNotationDebug'

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
    
    // 🔧 检查textId是否为有效数字（上传模式下可能是字符串'upload'）
    const validTextId = typeof textId === 'string' && textId === 'upload' ? null : textId
    if (!validTextId || (typeof validTextId === 'string' && isNaN(parseInt(validTextId)))) {
      // 跳过无效的textId（如上载模式）
      console.log('⚠️ [useNotationCache] Skipping load: invalid textId', textId)
      setIsInitialized(true)
      return
    }

    // 移除详细日志（已通过测试，减少不必要的日志输出）
    setIsLoading(true)
    setError(null)

    try {
      logVocabNotationDebug('📥 [useNotationCache] loadAllNotations start', { textId: validTextId })
      // 并行加载grammar notations和vocab notations
      const [grammarResponse, vocabResponse] = await Promise.all([
        apiService.getGrammarNotations(validTextId),
        apiService.getVocabNotations(validTextId)
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
        
        // 🔍 先检查原始数据是否包含 word_token_token_ids
        console.log('🔍 [useNotationCache] 检查原始 API 数据中的 word_token_token_ids:')
        vocabList.forEach((n, idx) => {
          console.log(`  notation ${idx}:`, {
            token_id: n.token_id,
            word_token_id: n.word_token_id,
            word_token_token_ids: n.word_token_token_ids,
            has_field: 'word_token_token_ids' in n,
            all_keys: Object.keys(n)
          })
        })
        
        // 转换为前端使用的格式（确保有token_index字段）
        const formattedVocabNotations = vocabList.map(notation => ({
          user_id: notation.user_id,
          text_id: notation.text_id,
          sentence_id: notation.sentence_id,
          token_id: notation.token_id,
          token_index: notation.token_id, // 添加token_index字段作为别名
          vocab_id: notation.vocab_id,
          word_token_id: notation.word_token_id, // 🔧 新增：word_token_id（用于非空格语言的完整词标注）
          word_token_token_ids: notation.word_token_token_ids || null, // 🔧 新增：word_token的所有token_ids（用于显示完整下划线）
          created_at: notation.created_at
        }))
        
        // 🔍 检查格式化后的数据
        console.log('🔍 [useNotationCache] 格式化后的数据:')
        formattedVocabNotations.forEach((n, idx) => {
          console.log(`  formatted ${idx}:`, {
            token_id: n.token_id,
            word_token_id: n.word_token_id,
            word_token_token_ids: n.word_token_token_ids,
            has_field: 'word_token_token_ids' in n
          })
        })
        
        // 🔍 只记录有 word_token_token_ids 的 notations（用于调试）
        const wordTokenNotations = formattedVocabNotations.filter(n => n.word_token_token_ids && Array.isArray(n.word_token_token_ids) && n.word_token_token_ids.length > 0)
        if (wordTokenNotations.length > 0) {
          console.log('✅ [useNotationCache] 发现 word_token_token_ids:', wordTokenNotations.map(n => ({
            token_id: n.token_id,
            word_token_id: n.word_token_id,
            word_token_token_ids: n.word_token_token_ids
          })))
        } else {
          console.warn('⚠️ [useNotationCache] 没有发现任何 word_token_token_ids！')
        }
        
        console.log('✅ [useNotationCache] 加载了', formattedVocabNotations.length, '个 vocab notations')
        logVocabNotationDebug('📦 [useNotationCache] vocab notations loaded', {
          textId: validTextId,
          count: formattedVocabNotations.length,
        })
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
          word_token_id: notation.word_token_id, // 🔧 新增：word_token_id（用于非空格语言的完整词标注）
          word_token_token_ids: notation.word_token_token_ids || null, // 🔧 新增：word_token的所有token_ids（用于显示完整下划线）
          created_at: notation.created_at
        }))
        logVocabNotationDebug('📦 [useNotationCache] vocab notations loaded (legacy format)', {
          textId: validTextId,
          count: formattedVocabNotations.length,
        })
        setVocabNotations(formattedVocabNotations)
        // 不再预加载所有 examples：改为按需懒加载 + 新建后单次写缓存
      } else {
        console.warn('⚠️ [useNotationCache] No vocab notations found or invalid response format')
        logVocabNotationDebug('📦 [useNotationCache] vocab notations empty/invalid', { textId: validTextId })
        setVocabNotations([])
      }

      setIsInitialized(true)
      // 移除成功日志（已通过测试）

    } catch (err) {
      console.error('❌ [useNotationCache] Error loading notations:', err)
      logVocabNotationDebug('❌ [useNotationCache] loadAllNotations error', {
        textId: validTextId,
        message: err?.message || String(err),
      })
      setError(err.message || 'Failed to load notations')
      // 🔧 即使出错也要设置 isInitialized，避免无限重试
      setIsInitialized(true)
      // 设置空数组，避免显示错误
      setGrammarNotations([])
      setVocabNotations([])
    } finally {
      setIsLoading(false)
      logVocabNotationDebug('✅ [useNotationCache] loadAllNotations finished', { textId: validTextId })
    }
  }, [])

  // 初始化加载
  useEffect(() => {
    // 🔧 检查articleId是否为有效数字（上传模式下可能是字符串'upload'）
    const validArticleId = typeof articleId === 'string' && articleId === 'upload' ? null : articleId
    if (validArticleId && !isInitialized) {
      loadAllNotations(validArticleId)
    } else if (articleId === 'upload') {
      // 如果是上传模式，直接标记为已初始化，避免不必要的加载
      setIsInitialized(true)
    }
  }, [articleId, isInitialized, loadAllNotations])

  // 🔧 使用 ref 保存最新的数组引用，避免闭包问题
  const grammarNotationsRef = useRef(grammarNotations)
  const vocabNotationsRef = useRef(vocabNotations)
  
  useEffect(() => {
    grammarNotationsRef.current = grammarNotations
    vocabNotationsRef.current = vocabNotations
  }, [grammarNotations, vocabNotations])

  // 获取句子的grammar notations
  // 🔧 使用 ref 缓存上次的结果，只在结果变化时输出日志
  const lastResultCacheRef = useRef(new Map()) // key: sentenceId, value: { count, notationIds }
  
  const getGrammarNotationsForSentence = useCallback((sentenceId) => {
    // 🔧 确保类型一致（数字比较）
    const sid = Number(sentenceId)
    const filtered = grammarNotationsRef.current.filter(notation => {
      const notationSid = Number(notation.sentence_id)
      return notationSid === sid
    })
    
    // 🔍 诊断日志：只在结果变化时输出（避免刷屏）
    const lastResult = lastResultCacheRef.current.get(sid)
    const currentNotationIds = filtered.map(n => n.notation_id || n.grammar_id).sort().join(',')
    const lastNotationIds = lastResult?.notationIds || ''
    
    // 只在结果数量变化或 notation IDs 变化时输出日志
    if (filtered.length > 0 && (filtered.length !== lastResult?.count || currentNotationIds !== lastNotationIds)) {
      console.log('🔍 [useNotationCache] getGrammarNotationsForSentence (结果变化):', {
        sentenceId,
        sid,
        totalNotations: grammarNotationsRef.current.length,
        filteredCount: filtered.length,
        previousCount: lastResult?.count || 0,
        filteredNotations: filtered.map(n => ({
          notation_id: n.notation_id,
          grammar_id: n.grammar_id,
          sentence_id: n.sentence_id,
          text_id: n.text_id
        }))
      })
      
      // 更新缓存
      lastResultCacheRef.current.set(sid, {
        count: filtered.length,
        notationIds: currentNotationIds
      })
    }
    
    return filtered
  }, []) // 🔧 不依赖数组，使用 ref 访问最新值

  // 获取句子的vocab notations
  const getVocabNotationsForSentence = useCallback((sentenceId) => {
    // 确保类型一致（数字比较）
    const sid = Number(sentenceId)
    
    const filtered = vocabNotationsRef.current.filter(notation => 
      Number(notation.sentence_id) === sid
    )
    
    // 🔍 调试日志已移除（减少控制台输出）
    
    return filtered
  }, []) // 🔧 不依赖数组，使用 ref 访问最新值

  // 获取特定token的vocab example（通过API按需获取）
  const getVocabExampleForToken = useCallback(async (textId, sentenceId, tokenIndex) => {
    const key = `${textId}:${sentenceId}:${tokenIndex}`
    
    // 1. 先查本地缓存
    if (vocabExamplesCache.has(key)) {
      logVocabNotationDebug('⚡ [getVocabExampleForToken] cache hit', { key })
      return vocabExamplesCache.get(key)
    }

    // 2. 优先通过 vocab_notations 绑定的 vocab_id 精确查找
    try {
      const sid = Number(sentenceId)
      const tid = Number(tokenIndex)

      // 🔧 修复：在当前缓存的 vocabNotations 中查找匹配的标注
      // 优先匹配：精确 token_id 匹配
      let matchedNotation = vocabNotationsRef.current.find(n => {
        return Number(n.sentence_id) === sid && Number(n.token_id) === tid
      })
      if (matchedNotation) {
        logVocabNotationDebug('🧩 [getVocabExampleForToken] matched notation by token_id', {
          key,
          vocab_id: matchedNotation.vocab_id,
          token_id: matchedNotation.token_id,
          word_token_id: matchedNotation.word_token_id,
        })
      }
      
      // 🔧 如果没有精确匹配，尝试通过 word_token_token_ids 匹配
      if (!matchedNotation) {
        matchedNotation = vocabNotationsRef.current.find(n => {
          if (Number(n.sentence_id) !== sid) return false
          // 检查 word_token_token_ids 是否包含当前 token
          if (n?.word_token_token_ids && Array.isArray(n.word_token_token_ids) && n.word_token_token_ids.length > 0) {
            const tokenIdsArray = n.word_token_token_ids.map(id => Number(id))
            return tokenIdsArray.includes(tid)
          }
          return false
        })
        if (matchedNotation) {
          logVocabNotationDebug('🧩 [getVocabExampleForToken] matched notation by word_token_token_ids', {
            key,
            vocab_id: matchedNotation.vocab_id,
            token_id: matchedNotation.token_id,
            word_token_id: matchedNotation.word_token_id,
          })
        } else {
          logVocabNotationDebug('⚠️ [getVocabExampleForToken] no matched notation in cache', {
            key,
            vocabNotationsCount: Array.isArray(vocabNotationsRef.current) ? vocabNotationsRef.current.length : null,
          })
        }
      }

      if (matchedNotation && matchedNotation.vocab_id) {
        const { apiService } = await import('../../../services/api')
        logVocabNotationDebug('🌐 [getVocabExampleForToken] fetching vocab by id', {
          key,
          vocab_id: matchedNotation.vocab_id,
        })
        // 通过 vocab_id 获取词汇详情（包含所有 examples）
        const vocabResp = await apiService.getVocabById(matchedNotation.vocab_id)
        const vocabData = vocabResp?.data || vocabResp

        // 在该 vocab 的例句中，找到同一篇文章、同一句子的例句
        const examples = Array.isArray(vocabData?.examples) ? vocabData.examples : []
        const matchedExample = examples.find(ex => 
          Number(ex.text_id) === Number(textId) && Number(ex.sentence_id) === sid
        ) || examples[0]  // 退而求其次，取第一条

        if (matchedExample) {
          const normalized = {
            vocab_id: vocabData.vocab_id,
            text_id: matchedExample.text_id,
            sentence_id: matchedExample.sentence_id,
            token_index: tid,
            context_explanation: matchedExample.context_explanation,
            token_indices: matchedExample.token_indices || []
          }
          setVocabExamplesCache(prev => {
            const newCache = new Map(prev)
            newCache.set(key, normalized)
            return newCache
          })
          logVocabNotationDebug('✅ [getVocabExampleForToken] example resolved via vocab_id', {
            key,
            vocab_id: normalized.vocab_id,
            hasExplanation: Boolean(normalized.context_explanation),
          })
          return normalized
        }
      }
    } catch (error) {
      console.error('❌ [getVocabExampleForToken] Failed to fetch by vocab_id:', error)
      logVocabNotationDebug('❌ [getVocabExampleForToken] fetch by vocab_id failed', {
        key,
        message: error?.message || String(error),
      })
      // 不中断，继续走 tokenIndex 回退逻辑
    }

    // 3. 回退：使用按位置查询的老接口（可能存在 tokenIndex 不完全匹配的问题）
    try {
      const { apiService } = await import('../../../services/api')
      logVocabNotationDebug('🌐 [getVocabExampleForToken] fallback getVocabExampleByLocation', { key })
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
        logVocabNotationDebug('✅ [getVocabExampleForToken] example resolved via location', {
          key,
          vocab_id: normalized.vocab_id,
          hasExplanation: Boolean(normalized.context_explanation),
        })
        return normalized
      } else {
        logVocabNotationDebug('⚠️ [getVocabExampleForToken] no payload from location', { key })
        return null
      }
    } catch (error) {
      console.error('❌ [getVocabExampleForToken] API error (by location):', error)
      logVocabNotationDebug('❌ [getVocabExampleForToken] fallback location error', {
        key,
        message: error?.message || String(error),
      })
      return null
    }
  }, [vocabExamplesCache]) // 🔧 移除 vocabNotations 依赖，使用 ref 访问

  // 获取grammar rule详情
  const getGrammarRuleById = useCallback((grammarId) => {
    return grammarRulesCache.get(grammarId) || null
  }, [grammarRulesCache])

  // 检查句子是否有grammar notation
  const hasGrammarNotation = useCallback((sentenceId) => {
    return grammarNotationsRef.current.some(notation => 
      notation.sentence_id === sentenceId
    )
  }, []) // 🔧 不依赖数组，使用 ref 访问最新值

  // 检查句子是否有vocab notation
  const hasVocabNotation = useCallback((sentenceId) => {
    return vocabNotationsRef.current.some(notation => 
      notation.sentence_id === sentenceId
    )
  }, []) // 🔧 不依赖数组，使用 ref 访问最新值

  // 刷新缓存（当有新的notation被创建时调用）
  const refreshCache = useCallback(async () => {
    if (articleId) {
      console.log('🔄 [useNotationCache] ========== 开始刷新缓存 ==========')
      console.log('🔄 [useNotationCache] Refreshing cache for articleId:', articleId)
      console.log('🔄 [useNotationCache] 当前缓存状态:', {
        vocabNotationsCount: vocabNotations.length,
        grammarNotationsCount: grammarNotations.length
      })
      
      setIsInitialized(false)
      await loadAllNotations(articleId)
      
      console.log('✅ [useNotationCache] 缓存刷新完成')
      console.log('🔄 [useNotationCache] ========== 缓存刷新结束 ==========')
    } else {
      console.warn('⚠️ [useNotationCache] 无法刷新缓存：articleId 为空')
    }
  }, [articleId, loadAllNotations, vocabNotations.length, grammarNotations.length])

  // 添加新的grammar notation到缓存
  const addGrammarNotationToCache = useCallback((notation) => {
    // 🔍 诊断日志：追踪调用来源
    const stackTrace = new Error().stack
    console.log('➕ [useNotationCache] addGrammarNotationToCache 被调用:', {
      notation_id: notation.notation_id,
      grammar_id: notation.grammar_id,
      text_id: notation.text_id,
      sentence_id: notation.sentence_id,
      callStack: stackTrace?.split('\n').slice(1, 5).join(' -> ')
    })
    
    setGrammarNotations(prev => {
      console.log('🔍 [useNotationCache] addGrammarNotationToCache - 当前缓存状态:', {
        prevCount: prev.length,
        existingNotations: prev.map(n => ({
          notation_id: n.notation_id,
          grammar_id: n.grammar_id,
          text_id: n.text_id,
          sentence_id: n.sentence_id
        }))
      })
      
      // 检查是否已存在，避免重复添加
      const exists = prev.some(n => {
        const match = n.text_id === notation.text_id && 
                     n.sentence_id === notation.sentence_id && 
                     n.grammar_id === notation.grammar_id
        if (match) {
          console.warn('⚠️ [useNotationCache] 发现重复的 grammar notation:', {
            existing: {
              notation_id: n.notation_id,
              grammar_id: n.grammar_id,
              text_id: n.text_id,
              sentence_id: n.sentence_id
            },
            new: {
              notation_id: notation.notation_id,
              grammar_id: notation.grammar_id,
              text_id: notation.text_id,
              sentence_id: notation.sentence_id
            }
          })
        }
        return match
      })
      
      if (exists) {
        console.log('⚠️ [useNotationCache] Grammar notation already exists in cache, 跳过添加')
        return prev
      }
      
      const newList = [...prev, notation]
      console.log('✅ [useNotationCache] Grammar notation 添加成功:', {
        prevCount: prev.length,
        newCount: newList.length,
        addedNotation: {
          notation_id: notation.notation_id,
          grammar_id: notation.grammar_id,
          text_id: notation.text_id,
          sentence_id: notation.sentence_id
        }
      })
      return newList
    })
  }, [])

  // 添加新的vocab notation到缓存
  const addVocabNotationToCache = useCallback((notation) => {
    // 🔍 诊断日志：追踪调用来源
    const stackTrace = new Error().stack
    console.log('➕ [useNotationCache] ========== 开始添加 vocab notation 到缓存 ==========')
    console.log('➕ [useNotationCache] addVocabNotationToCache 被调用:', {
      notation_id: notation.notation_id,
      vocab_id: notation.vocab_id,
      text_id: notation.text_id,
      sentence_id: notation.sentence_id,
      token_index: notation.token_index,
      token_id: notation.token_id,
      callStack: stackTrace?.split('\n').slice(1, 5).join(' -> ')
    })
    console.log('➕ [useNotationCache] 接收到的 notation:', JSON.stringify(notation, null, 2))
    
    setVocabNotations(prev => {
      console.log('➕ [useNotationCache] setVocabNotations 回调执行，prev 数量:', prev.length)
      console.log('🔍 [useNotationCache] addVocabNotationToCache - 当前缓存状态:', {
        prevCount: prev.length,
        existingNotations: prev.map(n => ({
          notation_id: n.notation_id,
          vocab_id: n.vocab_id,
          text_id: n.text_id,
          sentence_id: n.sentence_id,
          token_index: n.token_index,
          token_id: n.token_id
        }))
      })
      
      // 检查是否已存在，避免重复添加
      const exists = prev.some(n => {
        const match = n.text_id === notation.text_id && 
                     n.sentence_id === notation.sentence_id && 
                     (n.token_index === notation.token_index || n.token_id === notation.token_id || n.token_id === notation.token_index)
        if (match) {
          console.warn('⚠️ [useNotationCache] 发现重复的 vocab notation:', {
            existing: {
              notation_id: n.notation_id,
              vocab_id: n.vocab_id,
              text_id: n.text_id,
              sentence_id: n.sentence_id,
              token_index: n.token_index,
              token_id: n.token_id
            },
            new: {
              notation_id: notation.notation_id,
              vocab_id: notation.vocab_id,
              text_id: notation.text_id,
              sentence_id: notation.sentence_id,
              token_index: notation.token_index,
              token_id: notation.token_id
            }
          })
        }
        return match
      })
      
      if (exists) {
        console.log('⚠️ [useNotationCache] Vocab notation already exists in cache, 不添加')
        return prev
      }
      
      const newList = [...prev, notation]
      console.log('✅ [useNotationCache] Vocab notation 添加成功:', {
        prevCount: prev.length,
        newCount: newList.length,
        addedNotation: {
          notation_id: notation.notation_id,
          vocab_id: notation.vocab_id,
          text_id: notation.text_id,
          sentence_id: notation.sentence_id,
          token_index: notation.token_index,
          token_id: notation.token_id
        }
      })
      console.log('✅ [useNotationCache] 新列表 JSON:', JSON.stringify(newList, null, 2))
      return newList
    })
    
    console.log('➕ [useNotationCache] ========== 添加 vocab notation 完成 ==========')
  }, [])  // 🔧 移除 vocabNotations 依赖，避免闭包问题

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
