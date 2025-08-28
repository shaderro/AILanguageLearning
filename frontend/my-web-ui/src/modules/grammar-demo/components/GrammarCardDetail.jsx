import { useState, useEffect } from 'react'

const GrammarCardDetail = ({ grammar, onClose }) => {
  const [grammarData, setGrammarData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchGrammarData = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const response = await fetch(`http://localhost:8000/api/grammar?rule=${encodeURIComponent(grammar)}`)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        setGrammarData(data)
      } catch (err) {
        setError(err.message)
        console.error('Error fetching grammar data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchGrammarData()
  }, [grammar])

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-8 max-w-2xl mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded mb-6"></div>
          <div className="h-4 bg-gray-200 rounded mb-4"></div>
          <div className="h-4 bg-gray-200 rounded mb-4"></div>
          <div className="h-4 bg-gray-200 rounded mb-6"></div>
          <div className="h-4 bg-gray-200 rounded mb-4"></div>
          <div className="h-4 bg-gray-200 rounded mb-4"></div>
          <div className="h-4 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg p-8 max-w-2xl mx-auto">
        <div className="text-center">
          <div className="text-red-500 text-lg mb-4">Error loading grammar data</div>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={onClose}
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg p-8 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900 capitalize">
          {grammarData?.rule || grammar}
        </h1>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Structure</h2>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-gray-800 font-mono text-lg">
              {grammarData?.structure}
            </p>
          </div>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Usage</h2>
          <p className="text-gray-700 leading-relaxed text-lg">
            {grammarData?.usage}
          </p>
        </div>

        <div>
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Example</h2>
          <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
            <p className="text-gray-700 italic text-lg">
              "{grammarData?.example}"
            </p>
          </div>
        </div>

        {grammarData?.additionalExamples && (
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-3">More Examples</h2>
            <div className="space-y-2">
              {grammarData.additionalExamples.map((example, index) => (
                <div key={index} className="bg-gray-50 p-3 rounded">
                  <p className="text-gray-700 italic">"{example}"</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="flex justify-end space-x-4">
          <button
            onClick={onClose}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default GrammarCardDetail
