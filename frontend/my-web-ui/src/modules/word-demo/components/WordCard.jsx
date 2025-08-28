import { useState, useEffect } from 'react'
import CardBase from '../../shared/components/CardBase'

const WordCard = ({ word = 'apple', onClick }) => {
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

  return (
    <CardBase
      title={wordData?.word || word}
      data={wordData}
      loading={loading}
      error={error}
      onClick={onClick}
    >
      {wordData && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Definition
            </h3>
            <p className="text-gray-800 leading-relaxed">
              {wordData.definition}
            </p>
          </div>
          
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Example
            </h3>
            <p className="text-gray-600 italic leading-relaxed">
              "{wordData.example}"
            </p>
          </div>
        </div>
      )}
    </CardBase>
  )
}

export default WordCard 