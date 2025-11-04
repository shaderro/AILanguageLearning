import { useState, useRef } from 'react'
import { getTokenId } from '../utils/tokenUtils'

/**
 * Custom hook to manage token selection state
 */
export function useTokenSelection({ sentences, onTokenSelect, articleId, clearSentenceInteraction }) {
  const [selectedTokenIds, setSelectedTokenIds] = useState(() => new Set())
  const [activeSentenceIndex, setActiveSentenceIndex] = useState(null)
  const activeSentenceRef = useRef(null)

  const buildSelectedTexts = (sIdx, idSet) => {
    if (sIdx == null) return []
    const tokens = (sentences[sIdx]?.tokens || [])
    const texts = []
    for (let i = 0; i < tokens.length; i++) {
      const tk = tokens[i]
      if (tk && typeof tk === 'object') {
        const id = getTokenId(tk, sIdx)
        if (id && idSet.has(id)) texts.push(tk.token_body ?? '')
      }
    }
    return texts
  }

  // Build detailed token and sentence info
  const buildSelectionContext = (sIdx, idSet) => {
    if (sIdx == null || !sentences[sIdx]) return null
    
    const sentence = sentences[sIdx]
    const tokens = sentence.tokens || []
    const selectedTokens = []
    const selectedTexts = []
    const tokenIndices = []
    
    for (let i = 0; i < tokens.length; i++) {
      const tk = tokens[i]
      if (tk && typeof tk === 'object') {
        const id = getTokenId(tk, sIdx)
        if (id && idSet.has(id)) {
          selectedTokens.push(tk)
          selectedTexts.push(tk.token_body ?? '')
          tokenIndices.push(tk.sentence_token_id ?? (i + 1))
        }
      }
    }
    
    // 确保text_id和sentence_id有正确的值
    // 优先使用传入的articleId，然后尝试从句子对象获取，最后使用默认值
    const textId = articleId || sentence.text_id || sentence.textId || 1
    const sentenceId = sentence.sentence_id || sentence.sentenceId || (sIdx + 1)  // 使用索引+1作为默认值
    
    console.log('🔍 [useTokenSelection] Building selection context:')
    console.log('  - articleId (from props):', articleId)
    console.log('  - Original sentence.text_id:', sentence.text_id)
    console.log('  - Original sentence.sentence_id:', sentence.sentence_id)
    console.log('  - Final textId:', textId)
    console.log('  - Final sentenceId:', sentenceId)
    
    return {
      sentence: {
        text_id: textId,
        sentence_id: sentenceId,
        sentence_body: sentence.sentence_body || sentence.sentenceBody || sentence.text || ''
      },
      tokens: selectedTokens,
      selectedTexts,
      tokenIndices
    }
  }

  const emitSelection = (set, lastTokenText = '') => {
    // 写入 document.title 以便无控制台时也能看到
    const logMsg = `emit: size=${set.size}, active=${activeSentenceRef.current}`
    document.title = logMsg
    
    console.log('📡 [useTokenSelection.emitSelection] Called with:', {
      setSize: set.size,
      setContents: Array.from(set),
      lastTokenText,
      activeSentence: activeSentenceRef.current
    })
    console.trace('📡 [useTokenSelection.emitSelection] Call stack')
    
    setSelectedTokenIds(set)
    if (onTokenSelect) {
      const selectedTexts = buildSelectedTexts(activeSentenceRef.current, set)
      const context = buildSelectionContext(activeSentenceRef.current, set)
      console.log('📡 [useTokenSelection.emitSelection] Built data:', {
        selectedTexts,
        contextTokens: context?.tokens?.length
      })
      onTokenSelect(lastTokenText, set, selectedTexts, context)
    }
  }

  const clearSelection = () => {
    // 写入标题栏
    document.title = 'clearSelection() called!'
    console.log('🧹 [useTokenSelection.clearSelection] Called')
    console.trace('🧹 [useTokenSelection.clearSelection] Call stack')
    
    const empty = new Set()
    emitSelection(empty, '')
    activeSentenceRef.current = null
    setActiveSentenceIndex(null)
    // 清除句子交互状态
    if (clearSentenceInteraction) {
      clearSentenceInteraction()
    }
  }

  const addSingle = (sIdx, token) => {
    // 任何 token 选择都应取消句子级选择（避免整句与token同时高亮/上报）
    if (typeof clearSentenceInteraction === 'function') {
      try { clearSentenceInteraction() } catch {}
    }
    // 如果选择了其他句子的token，先清除当前选择，然后设置新句子为活跃状态
    if (activeSentenceRef.current != null && activeSentenceRef.current !== sIdx) {
      clearSelection()
      // 设置新的活跃句子
      activeSentenceRef.current = sIdx
      setActiveSentenceIndex(sIdx)
      // 重新开始选择，只选择当前token
      const uid = getTokenId(token, sIdx)
      console.debug('[useTokenSelection.addSingle] sIdx=', sIdx, 'uid=', uid, 'token=', token?.token_body, 'new sentence')
      if (!uid) return
      const next = new Set([uid])
      emitSelection(next, token?.token_body ?? '')
      return
    }
    
    const uid = getTokenId(token, sIdx)
    console.debug('[useTokenSelection.addSingle] sIdx=', sIdx, 'uid=', uid, 'token=', token?.token_body)
    if (!uid) return
    const next = new Set(selectedTokenIds)
    next.add(uid)
    
    // 确保 activeSentenceIndex 状态与 activeSentenceRef 同步
    if (activeSentenceRef.current !== sIdx) {
      activeSentenceRef.current = sIdx
      setActiveSentenceIndex(sIdx)
    } else if (activeSentenceIndex !== sIdx) {
      setActiveSentenceIndex(sIdx)
    }
    
    emitSelection(next, token?.token_body ?? '')
  }

  return {
    selectedTokenIds,
    activeSentenceIndex,
    activeSentenceRef,
    clearSelection,
    addSingle,
    emitSelection
  }
}

