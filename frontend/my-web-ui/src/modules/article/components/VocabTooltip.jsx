/**
 * VocabTooltip - Tooltip to show vocabulary explanation on hover
 */
export default function VocabTooltip({ token, explanation, isVisible }) {
  if (!isVisible || !explanation) return null

  return (
    <div className="absolute z-50 mt-1 p-3 bg-gray-900 text-white text-xs rounded shadow-lg max-w-xs">
      <div className="font-semibold text-sm">{explanation.word}</div>
      {explanation.pronunciation && (
        <div className="text-gray-300 text-xs mt-1">{explanation.pronunciation}</div>
      )}
      <div className="mt-2 text-gray-200">{explanation.definition}</div>
      {explanation.examples && explanation.examples.length > 0 && (
        <div className="mt-2">
          <div className="font-medium text-gray-300">Examples:</div>
          {explanation.examples.slice(0, 1).map((example, idx) => (
            <div key={idx} className="mt-1 italic text-gray-400 text-xs">
              {example}
            </div>
          ))}
        </div>
      )}
      {explanation.difficulty && (
        <div className="mt-2">
          <span className={`inline-block px-1 py-0.5 text-xs rounded`}>
            {explanation.difficulty}
          </span>
        </div>
      )}
    </div>
  )
}

