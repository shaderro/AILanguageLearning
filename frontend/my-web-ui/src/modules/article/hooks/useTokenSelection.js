import { useState, useRef } from 'react'
import { getTokenId } from '../utils/tokenUtils'

/**
 * Custom hook to manage token selection state
 */
export function useTokenSelection({ sentences, onTokenSelect, articleId }) {
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
        const id = getTokenId(tk)
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
        const id = getTokenId(tk)
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
    setSelectedTokenIds(set)
    if (onTokenSelect) {
      const selectedTexts = buildSelectedTexts(activeSentenceRef.current, set)
      const context = buildSelectionContext(activeSentenceRef.current, set)
      onTokenSelect(lastTokenText, set, selectedTexts, context)
    }
  }

  const clearSelection = () => {
    const empty = new Set()
    emitSelection(empty, '')
    activeSentenceRef.current = null
    setActiveSentenceIndex(null)
  }

  const addSingle = (sIdx, token) => {
    if (activeSentenceRef.current != null && activeSentenceRef.current !== sIdx) {
      clearSelection()
      return
    }
    const uid = getTokenId(token)
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

