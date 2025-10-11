import { useState, useRef } from 'react'
import { getTokenId } from '../utils/tokenUtils'

/**
 * Custom hook to manage token selection state
 */
export function useTokenSelection({ sentences, onTokenSelect }) {
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
          tokenIndices.push(tk.sentence_token_id ?? i)
        }
      }
    }
    
    return {
      sentence: {
        text_id: sentence.text_id,
        sentence_id: sentence.sentence_id,
        sentence_body: sentence.sentence_body
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
    if (activeSentenceRef.current == null) {
      activeSentenceRef.current = sIdx
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

