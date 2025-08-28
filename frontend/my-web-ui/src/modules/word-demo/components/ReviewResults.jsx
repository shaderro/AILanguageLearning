const ReviewResults = ({ results = [], onClose, onRestart }) => {
  const totalWords = results.length
  const knownCount = results.filter(r => r.choice === 'known').length
  const vagueCount = results.filter(r => r.choice === 'vague').length
  const unknownCount = results.filter(r => r.choice === 'unknown').length

  const getChoiceColor = (choice) => {
    switch (choice) {
      case 'known': return 'text-green-600'
      case 'vague': return 'text-yellow-600'
      case 'unknown': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getChoiceIcon = (choice) => {
    switch (choice) {
      case 'known': return '✅'
      case 'vague': return '🤔'
      case 'unknown': return '❌'
      default: return '❓'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Review Complete!</h1>
        <p className="text-gray-600">You've reviewed {totalWords} words</p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="text-center p-4 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{knownCount}</div>
          <div className="text-sm text-green-700">Known</div>
        </div>
        <div className="text-center p-4 bg-yellow-50 rounded-lg">
          <div className="text-2xl font-bold text-yellow-600">{vagueCount}</div>
          <div className="text-sm text-yellow-700">Vague</div>
        </div>
        <div className="text-center p-4 bg-red-50 rounded-lg">
          <div className="text-2xl font-bold text-red-600">{unknownCount}</div>
          <div className="text-sm text-red-700">Unknown</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600">Mastery Level</span>
          <span className="text-sm text-gray-600">
            {Math.round((knownCount / totalWords) * 100)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-green-500 h-3 rounded-full transition-all duration-500"
            style={{ width: `${(knownCount / totalWords) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Detailed Results */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Word-by-Word Results</h3>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {results.map((result, index) => (
            <div 
              key={index} 
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <span className="font-medium text-gray-800 capitalize">
                {result.word}
              </span>
              <span className={`flex items-center space-x-2 ${getChoiceColor(result.choice)}`}>
                <span>{getChoiceIcon(result.choice)}</span>
                <span className="text-sm">
                  {result.choice === 'known' ? 'Known' : 
                   result.choice === 'vague' ? 'Vague' : 'Unknown'}
                </span>
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-4">
        <button
          onClick={onRestart}
          className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Restart Review
        </button>
        <button
          onClick={onClose}
          className="flex-1 bg-gray-500 text-white py-3 px-4 rounded-lg hover:bg-gray-600 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  )
}

export default ReviewResults
