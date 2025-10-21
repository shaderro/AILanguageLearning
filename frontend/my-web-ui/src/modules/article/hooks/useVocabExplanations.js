import { useState } from 'react'
import { getTokenId } from '../utils/tokenUtils'

/**
 * Custom hook to manage vocabulary explanations
 */
export function useVocabExplanations() {
  const [vocabExplanations, setVocabExplanations] = useState(() => new Map())
  const [hoveredTokenId, setHoveredTokenId] = useState(null)

  const handleGetExplanation = (token, explanation, sentenceIdx) => {
    const tokenId = getTokenId(token, sentenceIdx)
    console.debug('[useVocabExplanations.set] sentenceIdx=', sentenceIdx, 'uid=', tokenId)
    if (tokenId) {
      setVocabExplanations(prev => new Map(prev).set(tokenId, explanation))
    }
  }

  const hasExplanation = (token, sentenceIdx) => {
    const tokenId = getTokenId(token, sentenceIdx)
    return tokenId ? vocabExplanations.has(tokenId) : false
  }

  const getExplanation = (token, sentenceIdx) => {
    const tokenId = getTokenId(token, sentenceIdx)
    return tokenId ? vocabExplanations.get(tokenId) : null
  }

  return {
    vocabExplanations,
    hoveredTokenId,
    setHoveredTokenId,
    handleGetExplanation,
    hasExplanation,
    getExplanation
  }
}

