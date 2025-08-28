import { useState, useEffect } from 'react'
import CardBase from '../../shared/components/CardBase'

const GrammarCard = ({ grammar = 'present-perfect', onClick }) => {
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

  return (
    <CardBase
      title={grammarData?.rule || grammar}
      data={grammarData}
      loading={loading}
      error={error}
      onClick={onClick}
    >
      {grammarData && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Structure
            </h3>
            <p className="text-gray-800 leading-relaxed">
              {grammarData.structure}
            </p>
          </div>
          
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Usage
            </h3>
            <p className="text-gray-800 leading-relaxed">
              {grammarData.usage}
            </p>
          </div>
          
          <div>
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">
              Example
            </h3>
            <p className="text-gray-600 italic leading-relaxed">
              "{grammarData.example}"
            </p>
          </div>
        </div>
      )}
    </CardBase>
  )
}

export default GrammarCard
