import { useState, useRef, useEffect } from 'react'
import { getTokenId } from '../utils/tokenUtils'

/**
 * Custom hook to manage token selection state
 * 支持同一句子内多选，切换句子或点击空白处时清空选择
 */
export function useTokenSelection({ sentences, onTokenSelect, articleId, clearSentenceSelection, selectTokensInContext, addDebugLog }) {
  // 🔧 使用 ref 稳定函数引用，避免因为函数引用变化导致 hook 重新执行
  // 注意：这些 ref 会在每次渲染时更新，但不会触发 hook 重新执行
  const onTokenSelectRef = useRef(onTokenSelect)
  const clearSentenceSelectionRef = useRef(clearSentenceSelection)
  const selectTokensInContextRef = useRef(selectTokensInContext)
  const addDebugLogRef = useRef(addDebugLog)
  
  // 更新 ref（但不触发重新渲染）
  onTokenSelectRef.current = onTokenSelect
  clearSentenceSelectionRef.current = clearSentenceSelection
  selectTokensInContextRef.current = selectTokensInContext
  addDebugLogRef.current = addDebugLog
  
  // 🔧 使用全局存储来持久化选择状态，避免组件重新挂载时丢失
  // 关键：React StrictMode 会故意重新挂载组件，导致 useRef 重新初始化
  if (typeof window !== 'undefined') {
    if (!window.__tokenSelectionState) {
      window.__tokenSelectionState = new Map()
    }
  }
  
  // 🔧 为每个 articleId 创建独立的选择状态存储
  const stateKey = `article-${articleId || 'default'}`
  const globalState = typeof window !== 'undefined' ? window.__tokenSelectionState : null
  
  // 🔧 从全局存储恢复或创建新的 ref
  const selectedTokenIdRef = useRef((() => {
    if (globalState && globalState.has(stateKey)) {
      const savedState = globalState.get(stateKey)
      // 🔧 不在渲染期间调用 addDebugLog，延迟到 useEffect 中
      return new Set(savedState.selectedTokenIds || [])
    }
    return new Set()
  })())
  
  // 🔧 使用 useEffect 延迟日志调用，避免在渲染期间更新其他组件的状态
  useEffect(() => {
    // 清除所有调试日志
  }, []) // 🔧 只在组件挂载时执行一次
  
  const activeSentenceRef = useRef((() => {
    if (globalState && globalState.has(stateKey)) {
      return globalState.get(stateKey).activeSentence ?? null
    }
    return null
  })())
  
  // 🔧 每次更新时同步到全局存储
  const syncToGlobalState = (selectedIds, activeSentence) => {
    if (globalState) {
      globalState.set(stateKey, {
        selectedTokenIds: Array.from(selectedIds),
        activeSentence: activeSentence,
        lastUpdated: Date.now()
      })
    }
  }
  
  // 🔧 追踪 hook 实例（使用全局 Map 来追踪所有实例，避免重新挂载时误判）
  const hookInstanceIdRef = useRef((() => {
    const id = Math.random().toString(36).substr(2, 9)
    // 使用全局 Map 追踪实例（存储在 window 上，避免模块重新加载时丢失）
    if (typeof window !== 'undefined') {
      if (!window.__tokenSelectionInstances) {
        window.__tokenSelectionInstances = new Map()
      }
      window.__tokenSelectionInstances.set(id, {
        createdAt: Date.now(),
        articleId: articleId
      })
    }
    return id
  })())
  
  // 🔧 使用 articleId 作为稳定的标识符，而不是随机生成的实例 ID
  // 关键：同一个 article 的 hook 应该共享同一个"首次创建"状态
  // 这样即使组件重新挂载，也不会重复记录"首次创建"
  const hookIdentifier = `article-${articleId || 'default'}`
  
  // 🔧 追踪每个 article 的 hook 是否已经初始化过（使用全局存储，持久化）
  if (typeof window !== 'undefined') {
    if (!window.__tokenSelectionInitialized) {
      window.__tokenSelectionInitialized = new Set()
    }
  }
  
  // 🔧 使用 ref 避免频繁警告（必须在条件语句外声明）
  const lastWarningRef = useRef(0)
  
  const isInitialized = typeof window !== 'undefined' && 
    window.__tokenSelectionInitialized && 
    window.__tokenSelectionInitialized.has(hookIdentifier)
  
  // 🔧 标记为已初始化（只在真正首次创建时）
  if (!isInitialized && typeof window !== 'undefined' && window.__tokenSelectionInitialized) {
    window.__tokenSelectionInitialized.add(hookIdentifier)
  }
  
  // 🔧 使用 useEffect 延迟日志调用，避免在渲染期间更新其他组件的状态
  useEffect(() => {
    // 清除所有调试日志
  }, []) // 🔧 只在组件挂载时执行一次
  
  // state 仅用于触发 UI 更新
  const [selectedTokenIds, setSelectedTokenIds] = useState(new Set())
  const [activeSentenceIndex, setActiveSentenceIndex] = useState(null)
  
  // 🔧 移除 useEffect 同步机制，避免无限循环
  // 原因分析：
  // 1. useEffect 依赖 selectedTokenIds 和 activeSentenceIndex
  // 2. 在 useEffect 内部调用 setSelectedTokenIds 和 setActiveSentenceIndex
  // 3. 这会导致：state 更新 → useEffect 触发 → state 更新 → useEffect 触发 → 无限循环
  // 
  // 解决方案：
  // - ref 和 state 的同步已经在 emitSelection 和 clearSelection 中处理
  // - 全局存储机制已经可以恢复状态
  // - 不需要额外的同步 useEffect
  // 
  // 如果确实需要同步，应该在 emitSelection 和 clearSelection 中处理，而不是在 useEffect 中

  const buildSelectedTexts = (sIdx, tokenIdsSet) => {
    if (sIdx == null || !tokenIdsSet || tokenIdsSet.size === 0) {
      return []
    }
    
    const tokens = (sentences[sIdx]?.tokens || [])
    const texts = []
    
    // 🔧 按照 token 在数组中的顺序构建文本，确保顺序正确
    for (let i = 0; i < tokens.length; i++) {
      const tk = tokens[i]
      if (tk && typeof tk === 'object') {
        const id = getTokenId(tk, sIdx)
        if (tokenIdsSet.has(id)) {
          const tokenText = tk.token_body ?? tk.token ?? ''
          if (tokenText) {
            texts.push(tokenText)
          }
        }
      }
    }
    
    return texts
  }

  const buildSelectionContext = (sIdx, tokenIdsSet) => {
    if (sIdx == null || !tokenIdsSet || tokenIdsSet.size === 0 || !sentences[sIdx]) {
      return null
    }
    
    const sentence = sentences[sIdx]
    const tokens = sentence.tokens || []
    const selectedTokens = []
    const selectedTexts = []
    const tokenIndices = []
    
    for (let i = 0; i < tokens.length; i++) {
      const tk = tokens[i]
      if (tk && typeof tk === 'object') {
        const id = getTokenId(tk, sIdx)
        if (tokenIdsSet.has(id)) {
          selectedTokens.push(tk)
          selectedTexts.push(tk.token_body ?? '')
          tokenIndices.push(tk.sentence_token_id ?? (i + 1))
        }
      }
    }
    
    if (selectedTokens.length === 0) {
      return null
    }
    
    const textId = articleId || sentence.text_id || sentence.textId || 1
    const sentenceId = sentence.sentence_id || sentence.sentenceId || (sIdx + 1)
    const wordTokens = sentence.word_tokens || sentence.wordTokens || null
    const language = sentence.language || sentence.language_name || null
    const languageCode = sentence.language_code || sentence.languageCode || null
    const isNonWhitespace = sentence.is_non_whitespace ?? sentence.isNonWhitespace ?? null
    
    const context = {
      sentence: {
        text_id: textId,
        sentence_id: sentenceId,
        sentence_body: sentence.sentence_body || sentence.sentenceBody || sentence.text || '',
        language,
        language_code: languageCode,
        is_non_whitespace: isNonWhitespace,
        tokens: sentence.tokens || [],
        word_tokens: wordTokens
      },
      tokens: selectedTokens,
      selectedTexts: selectedTexts,
      tokenIndices: tokenIndices
    }
    
    return context
  }

  const emitSelection = (selectedTokenIdsSet, lastTokenText = '') => {
    // 🔧 先更新 ref（创建新的 Set 避免引用问题）
    // 这是同步操作，立即生效
    const newSet = new Set(selectedTokenIdsSet)
    selectedTokenIdRef.current = newSet
    
    // 🔧 同步到全局存储，避免组件重新挂载时丢失
    syncToGlobalState(selectedTokenIdRef.current, activeSentenceRef.current)
    
    // 🔧 更新 state（触发 UI 更新）
    // 注意：state 更新是异步的，但 ref 已经同步更新
    // 🔧 确保创建新的 Set 对象，触发 React 重新渲染
    const newStateSet = new Set(selectedTokenIdsSet)
    setSelectedTokenIds(newStateSet)
    
    // 🔧 调试：打印选择状态
    if (addDebugLogRef.current && typeof addDebugLogRef.current === 'function') {
      addDebugLogRef.current('info', `✅ [选择] emitSelection - 更新选中状态: ${newStateSet.size} 个 token, IDs: ${Array.from(newStateSet).join(', ')}`, null)
    }
    
    if (onTokenSelectRef.current && selectedTokenIdsSet.size > 0) {
      const selectedTexts = buildSelectedTexts(activeSentenceRef.current, selectedTokenIdsSet)
      const context = buildSelectionContext(activeSentenceRef.current, selectedTokenIdsSet)
      
      // 🔧 调试：打印选择的文本和上下文
      if (addDebugLogRef.current && typeof addDebugLogRef.current === 'function') {
        addDebugLogRef.current('info', `📝 [选择] emitSelection - 选择的文本: "${selectedTexts.join(' ')}", 上下文 tokens 数量: ${context?.tokens?.length || 0}`, null)
      }
      
      // 使用最后一个 token 的文本作为主要文本
      onTokenSelectRef.current(lastTokenText, selectedTokenIdsSet, selectedTexts, context)
      
      // 同步更新新选择系统
      if (typeof selectTokensInContextRef.current === 'function' && context && context.tokens.length > 0) {
        const textId = context.sentence.text_id
        const sentenceId = context.sentence.sentence_id
        const tokenIds = context.tokens.map(t => t.sentence_token_id)
        
        selectTokensInContextRef.current(textId, sentenceId, tokenIds)
      }
    }
  }

  const clearSelection = (options = {}) => {
    const { skipSentence = false } = options
    
    selectedTokenIdRef.current = new Set()
    setSelectedTokenIds(new Set())
    activeSentenceRef.current = null
    setActiveSentenceIndex(null)
    
    // 🔧 同步到全局存储
    syncToGlobalState(selectedTokenIdRef.current, activeSentenceRef.current)
    
    if (!skipSentence && clearSentenceSelectionRef.current) {
      clearSentenceSelectionRef.current()
    }
  }

  const selectSingle = (sIdx, token) => {
    const tokenId = getTokenId(token, sIdx)
    if (!tokenId) {
      return
    }
    
    // 🔧 在读取 ref 之前记录初始状态
    // 重要：直接读取 ref.current，确保获取最新值
    let initialRefSize = selectedTokenIdRef.current.size
    let initialSentence = activeSentenceRef.current
    
    // 🔧 如果 ref 为空但 state 有值，从 state 恢复 ref（防止 ref 被意外重置）
    if (initialRefSize === 0 && selectedTokenIds.size > 0) {
      selectedTokenIdRef.current = new Set(selectedTokenIds)
      if (activeSentenceIndex !== null) {
        activeSentenceRef.current = activeSentenceIndex
      }
      // 重新读取
      initialRefSize = selectedTokenIdRef.current.size
      initialSentence = activeSentenceRef.current
    }
    
    // 🔧 验证 ref 对象本身是否有效
    const refIsValid = selectedTokenIdRef && typeof selectedTokenIdRef === 'object' && 'current' in selectedTokenIdRef
    
    // 🔧 如果 ref 无效或为空，记录警告
    if (!refIsValid) {
      return
    }
    
    // 🔧 读取当前状态（在句子切换之前）
    let currentSelection = selectedTokenIdRef.current
    let currentSentence = activeSentenceRef.current
    
    // 处理句子切换
    if (currentSentence === null) {
      // 首次选择：初始化
      activeSentenceRef.current = sIdx
      setActiveSentenceIndex(sIdx)
      // 🔧 如果 ref 已经有值，保留它（可能是之前的选择）
      if (currentSelection.size === 0) {
        selectedTokenIdRef.current = new Set()
      }
      // 🔧 同步到全局存储
      syncToGlobalState(selectedTokenIdRef.current, activeSentenceRef.current)
      
      // 🔧 重新读取 ref（确保使用最新值）
      currentSelection = selectedTokenIdRef.current
      currentSentence = activeSentenceRef.current
    } else if (currentSentence !== sIdx) {
      // 切换到不同句子：清空之前的选择
      selectedTokenIdRef.current = new Set()
      activeSentenceRef.current = sIdx
      setActiveSentenceIndex(sIdx)
      // 🔧 同步到全局存储
      syncToGlobalState(selectedTokenIdRef.current, activeSentenceRef.current)
      
      // 🔧 重新读取 ref（确保使用最新值）
      currentSelection = selectedTokenIdRef.current
      currentSentence = activeSentenceRef.current
    }
    
    // 🔧 在同一句子内处理 token 选择（toggle 行为）
    // 重要：在句子切换后，重新从 ref 读取最新值
    const latestSelection = selectedTokenIdRef.current
    const newSelection = new Set(latestSelection)
    
    if (latestSelection.has(tokenId)) {
      // 已选中：移除（取消选择）
      newSelection.delete(tokenId)
    } else {
      // 未选中：添加（选择）
      newSelection.add(tokenId)
    }
    
    // 发出选择事件
    emitSelection(newSelection, token?.token_body ?? '')
  }

  /**
   * 选择范围内的 token（用于拖拽选择）
   * @param {number} sIdx - 句子索引
   * @param {number} startTokenIdx - 起始 token 索引（数组索引，从 0 开始）
   * @param {number} endTokenIdx - 结束 token 索引（数组索引，从 0 开始）
   * @param {boolean} mergeWithExisting - 是否与现有选择合并（默认 false，拖拽时替换选择）
   */
  const selectRange = (sIdx, startTokenIdx, endTokenIdx, mergeWithExisting = false) => {
    // 🔧 立即打印日志，确保函数被调用时能看到
    if (addDebugLogRef.current && typeof addDebugLogRef.current === 'function') {
      addDebugLogRef.current('info', `🔧 [selectRange] 函数被调用 - 句子: ${sIdx}, 起始: ${startTokenIdx}, 结束: ${endTokenIdx}, 合并: ${mergeWithExisting}`, null)
    }
    
    // 验证句子索引和 token 索引的有效性
    if (!sentences || !sentences[sIdx]) {
      if (addDebugLogRef.current && typeof addDebugLogRef.current === 'function') {
        addDebugLogRef.current('error', `❌ [selectRange] 验证失败：无效的句子索引 ${sIdx}`, null)
      }
      return
    }
    
    const tokens = sentences[sIdx].tokens || []
    if (tokens.length === 0) {
      return
    }
    
    // 确保索引在有效范围内
    const validStartIdx = Math.max(0, Math.min(startTokenIdx, tokens.length - 1))
    const validEndIdx = Math.max(0, Math.min(endTokenIdx, tokens.length - 1))
    
    // 计算有效范围（支持反向拖拽）
    const rangeStart = Math.min(validStartIdx, validEndIdx)
    const rangeEnd = Math.max(validStartIdx, validEndIdx)
    
    // 检查是否在同一句子内
    const currentSentence = activeSentenceRef.current
    if (currentSentence !== null && currentSentence !== sIdx) {
      // 切换到不同句子：清空之前的选择
      selectedTokenIdRef.current = new Set()
      activeSentenceRef.current = sIdx
      setActiveSentenceIndex(sIdx)
      syncToGlobalState(selectedTokenIdRef.current, activeSentenceRef.current)
    } else if (currentSentence === null) {
      // 首次选择：初始化句子
      activeSentenceRef.current = sIdx
      setActiveSentenceIndex(sIdx)
    }
    
    // 获取当前选择（如果需要合并）
    const newSelection = mergeWithExisting 
      ? new Set(selectedTokenIdRef.current) 
      : new Set()
    
    // 遍历范围内的所有 token，将可选择的 token 添加到选择集合
    let lastTokenText = ''
    for (let i = rangeStart; i <= rangeEnd; i++) {
      const token = tokens[i]
      if (token && typeof token === 'object' && token.selectable) {
        const tokenId = getTokenId(token, sIdx)
        if (tokenId) {
          newSelection.add(tokenId)
          lastTokenText = token.token_body ?? ''
        }
      }
    }
    
    // 在调试面板中打印 selectRange 信息（每次调用时都打印）
    const logMessage = `selectRange - 句子索引: ${sIdx}, 起始Token索引: ${startTokenIdx}, 结束Token索引: ${endTokenIdx}, 有效范围: ${rangeStart}-${rangeEnd}, 合并: ${mergeWithExisting}, 选择数量: ${newSelection.size}`
    
    // 确保日志一定会打印到调试面板
    // 使用 addDebugLogRef.current（它会在每次渲染时更新）
    if (addDebugLogRef.current && typeof addDebugLogRef.current === 'function') {
      addDebugLogRef.current('info', logMessage, null)
    }
    
    // 🔧 调试：打印选择前的状态
    if (addDebugLogRef.current && typeof addDebugLogRef.current === 'function') {
      addDebugLogRef.current('info', `🔄 [selectRange] 准备调用 emitSelection - 选择数量: ${newSelection.size}, Token IDs: ${Array.from(newSelection).join(', ')}`, null)
    }
    
    // 调用 emitSelection 更新选择状态
    emitSelection(newSelection, lastTokenText)
  }

  return {
    selectedTokenIds, // 直接返回 Set
    activeSentenceIndex,
    activeSentenceRef,
    selectedTokenIdsRef: selectedTokenIdRef, // 🔧 直接返回 ref 对象本身，而不是快照
    clearSelection,
    addSingle: selectSingle,
    selectRange, // 🔧 新增：范围选择函数
    emitSelection
  }
}

