import { useState, useEffect } from 'react'

const WordCardDetail = ({ word, onClose }) => {
  const [wordData, setWordData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchWordData = async () => {
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

    fetchWordData()
  }, [word])

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading word details...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-500 mb-4">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Error loading word data</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={onClose}
          className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          Close
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Word Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 capitalize mb-2">{wordData.word}</h1>
        <div className="w-16 h-1 bg-blue-500 mx-auto rounded"></div>
      </div>

      {/* Definition */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 mb-3 flex items-center">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          Definition
        </h2>
        <p className="text-blue-800 leading-relaxed text-lg">{wordData.definition}</p>
      </div>

      {/* Example */}
      <div className="bg-green-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-green-900 mb-3 flex items-center">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          Example Usage
        </h2>
        <div className="bg-white rounded-lg p-4 border-l-4 border-green-500">
          <p className="text-green-800 italic text-lg leading-relaxed">"{wordData.example}"</p>
        </div>
      </div>

      {/* Additional Info */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Word Information
        </h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Word Type:</span>
            <span className="ml-2 font-medium text-gray-900">Noun</span>
          </div>
          <div>
            <span className="text-gray-600">Syllables:</span>
            <span className="ml-2 font-medium text-gray-900">{wordData.word.length > 5 ? '2' : '1'}</span>
          </div>
          <div>
            <span className="text-gray-600">Length:</span>
            <span className="ml-2 font-medium text-gray-900">{wordData.word.length} letters</span>
          </div>
          <div>
            <span className="text-gray-600">Language:</span>
            <span className="ml-2 font-medium text-gray-900">English</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-3 pt-4">
        <button
          onClick={onClose}
          className="flex-1 px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
        >
          Close
        </button>
        <button
          onClick={() => {
            // 这里可以添加更多功能，比如发音、收藏等
            console.log('More actions for:', wordData.word)
          }}
          className="flex-1 px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors font-medium"
        >
          More Actions
        </button>
      </div>
    </div>
  )
}

export default WordCardDetail 