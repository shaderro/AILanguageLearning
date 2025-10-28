import { useState, useEffect } from 'react'
import { apiService } from '../../../services/api'

/**
 * Custom hook to manage grammar notations for an article
 */
export function useGrammarNotations(articleId) {
  const [grammarNotations, setGrammarNotations] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (articleId) {
      loadGrammarNotations(articleId)
    }
  }, [articleId])

  const loadGrammarNotations = async (textId) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await apiService.getGrammarNotations(textId)
      
      if (response && response.data) {
        setGrammarNotations(response.data)
      } else {
        setGrammarNotations([])
      }
    } catch (err) {
      console.error('❌ [useGrammarNotations] Error loading grammar notations:', err)
      setError(err.message || 'Failed to load grammar notations')
      setGrammarNotations([])
    } finally {
      setIsLoading(false)
    }
  }

  /**
   * Check if a sentence has grammar notations
   * @param {number} sentenceId - The sentence ID to check
   * @returns {boolean} Whether the sentence has grammar notations
   */
  const hasGrammarNotation = (sentenceId) => {
    return grammarNotations.some(notation => 
      notation.sentence_id === sentenceId
    )
  }

  /**
   * Get grammar notation for a specific sentence
   * @param {number} sentenceId - The sentence ID
   * @returns {Object|null} The grammar notation object or null
   */
  const getGrammarNotation = (sentenceId) => {
    return grammarNotations.find(notation => 
      notation.sentence_id === sentenceId
    ) || null
  }

  /**
   * Get all grammar notations for a sentence
   * @param {number} sentenceId - The sentence ID
   * @returns {Array} Array of grammar notation objects
   */
  const getGrammarNotationsForSentence = (sentenceId) => {
    return grammarNotations.filter(notation => 
      notation.sentence_id === sentenceId
    )
  }

  return {
    grammarNotations,
    isLoading,
    error,
    hasGrammarNotation,
    getGrammarNotation,
    getGrammarNotationsForSentence,
    reload: () => loadGrammarNotations(articleId)
  }
}
