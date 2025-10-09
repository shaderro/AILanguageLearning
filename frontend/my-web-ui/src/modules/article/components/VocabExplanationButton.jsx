import { useState } from 'react'
import { apiService } from '../../../services/api'

/**
 * VocabExplanationButton - Button to fetch and display vocabulary explanation
 */
export default function VocabExplanationButton({ token, onGetExplanation }) {
  const [isLoading, setIsLoading] = useState(false)
  const [explanation, setExplanation] = useState(null)
  const [error, setError] = useState(null)

  const handleClick = async () => {
    if (explanation) return
    
    setIsLoading(true)
    setError(null)
    try {
      const result = await apiService.getVocabExplanation(token.token_body)
      
      setExplanation(result)
      if (onGetExplanation) {
        onGetExplanation(token, result)
      }
    } catch (error) {
      console.error('Failed to get vocab explanation:', error)
      setError('Failed to load explanation')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="mt-1">
      <button
        onClick={handleClick}
        disabled={isLoading}
        className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 rounded border border-blue-300 transition-colors duration-150 disabled:opacity-50"
      >
        {isLoading ? 'Loading...' : 'vocab explanation'}
      </button>
      {error && (
        <div className="mt-1 text-xs text-red-600">{error}</div>
      )}
      {explanation && (
        <div className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-sm max-w-md">
          <div className="font-semibold text-gray-800 text-base">{explanation.word}</div>
          {explanation.pronunciation && (
            <div className="text-gray-500 text-xs mt-1">{explanation.pronunciation}</div>
          )}
          {explanation.partOfSpeech && (
            <div className="text-blue-600 text-xs mt-1 font-medium">{explanation.partOfSpeech}</div>
          )}
          <div className="text-gray-700 mt-2">{explanation.definition}</div>
          
          {explanation.examples && explanation.examples.length > 0 && (
            <div className="mt-3">
              <div className="font-medium text-gray-700 text-sm">Examples:</div>
              {explanation.examples.map((example, idx) => (
                <div key={idx} className="text-gray-600 text-xs mt-1 italic pl-2 border-l-2 border-gray-300">
                  {example}
                </div>
              ))}
            </div>
          )}
          
          {explanation.synonyms && explanation.synonyms.length > 0 && (
            <div className="mt-3">
              <div className="font-medium text-gray-700 text-sm">Synonyms:</div>
              <div className="text-gray-600 text-xs mt-1">
                {explanation.synonyms.join(', ')}
              </div>
            </div>
          )}
          
          {explanation.difficulty && (
            <div className="mt-2">
              <span className={`inline-block px-2 py-1 text-xs rounded`}>
                {explanation.difficulty} difficulty
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

