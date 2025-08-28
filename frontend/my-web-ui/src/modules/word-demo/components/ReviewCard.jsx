import { useState, useEffect } from 'react'
import CardBase from '../../shared/components/CardBase'

const ReviewCard = ({ words = [], onComplete, onClose }) => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [showDefinition, setShowDefinition] = useState(false)
  const [wordData, setWordData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userChoices, setUserChoices] = useState([])

  const currentWord = words[currentIndex]

  useEffect(() => {
    if (currentWord) {
      fetchWordData(currentWord)
    }
  }, [currentWord])

  const fetchWordData = async (word) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`http://localhost:8000/api/word?text=${encodeURIComponent(word)}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setWordData(data)
    } catch (err) {
      setError(err.message)
      console.error('Error fetching word data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleChoice = (choice) => {
    const newChoices = [...userChoices, { word: currentWord, choice }]
    setUserChoices(newChoices)
    setShowDefinition(true)
  }

  const handleNext = () => {
    if (currentIndex < words.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setShowDefinition(false)
    } else {
      // Review completed
      onComplete(userChoices)
    }
  }

  const handleClose = () => {
    onClose()
  }

  if (!currentWord) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md mx-auto">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">No words to review</h2>
          <button
            onClick={handleClose}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8 max-w-md mx-auto">
      {/* Progress */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600">
            Word {currentIndex + 1} of {words.length}
          </span>
          <span className="text-sm text-gray-600">
            {Math.round(((currentIndex + 1) / words.length) * 100)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentIndex + 1) / words.length) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Word Display */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4 capitalize">
          {currentWord}
        </h1>
        
        {!showDefinition ? (
          <div>
            <p className="text-gray-600 mb-6">How well do you know this word?</p>
            
            {/* Choice Buttons */}
            <div className="space-y-3">
              <button
                onClick={() => handleChoice('vague')}
                className="w-full bg-yellow-100 text-yellow-800 py-3 px-4 rounded-lg hover:bg-yellow-200 transition-colors border-2 border-yellow-300"
              >
                🤔 模糊 (Vague)
              </button>
              <button
                onClick={() => handleChoice('known')}
                className="w-full bg-green-100 text-green-800 py-3 px-4 rounded-lg hover:bg-green-200 transition-colors border-2 border-green-300"
              >
                ✅ 认识 (Known)
              </button>
              <button
                onClick={() => handleChoice('unknown')}
                className="w-full bg-red-100 text-red-800 py-3 px-4 rounded-lg hover:bg-red-200 transition-colors border-2 border-red-300"
              >
                ❌ 不认识 (Unknown)
              </button>
            </div>
          </div>
        ) : (
          <div>
            {/* Definition Display */}
            <div className="bg-gray-50 p-6 rounded-lg mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Definition</h3>
              <p className="text-gray-700 leading-relaxed mb-4">
                {wordData?.definition || 'Definition not available'}
              </p>
              <h4 className="text-md font-semibold text-gray-800 mb-2">Example</h4>
              <p className="text-gray-600 italic">
                "{wordData?.example || 'Example not available'}"
              </p>
            </div>

            {/* Next Button */}
            <button
              onClick={handleNext}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors"
            >
              {currentIndex < words.length - 1 ? 'Next Word' : 'Complete Review'}
            </button>
          </div>
        )}
      </div>

      {/* Close Button */}
      <div className="text-center">
        <button
          onClick={handleClose}
          className="text-gray-500 hover:text-gray-700 transition-colors"
        >
          Exit Review
        </button>
      </div>
    </div>
  )
}

export default ReviewCard
