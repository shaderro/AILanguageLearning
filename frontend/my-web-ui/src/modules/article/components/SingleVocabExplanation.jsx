import React from "react";

// Single Vocab Explanation in Article View 组件
function SingleVocabExplanation({ explanation, isVisible, onClose }) {
  if (!isVisible || !explanation) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-800">词汇解释</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
          >
            
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Word and Basic Info */}
          <div className="mb-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">{explanation.word}</h3>
            {explanation.pronunciation && (
              <div className="text-gray-600 text-lg mb-2">{explanation.pronunciation}</div>
            )}
            {explanation.partOfSpeech && (
              <span className="inline-block bg-blue-100 text-blue-800 text-sm px-3 py-1 rounded-full">
                {explanation.partOfSpeech}
              </span>
            )}
          </div>

          {/* Definition */}
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-800 mb-3">定义</h4>
            <div className="text-gray-700 text-base leading-relaxed bg-gray-50 p-4 rounded-lg">
              {explanation.definition}
            </div>
          </div>

          {/* Examples */}
          {explanation.examples && explanation.examples.length > 0 && (
            <div className="mb-6">
              <h4 className="text-lg font-semibold text-gray-800 mb-3">例句</h4>
              <div className="space-y-3">
                {explanation.examples.map((example, idx) => (
                  <div key={idx} className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
                    <div className="text-gray-700 italic">{example}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Additional Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Difficulty */}
            {explanation.difficulty && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h5 className="font-semibold text-gray-700 mb-2">难度</h5>
                <span className={`inline-block px-3 py-1 text-sm rounded-full ${
                  explanation.difficulty === "easy" ? "bg-green-100 text-green-800" :
                  explanation.difficulty === "medium" ? "bg-yellow-100 text-yellow-800" :
                  "bg-red-100 text-red-800"
                }`}>
                  {explanation.difficulty}
                </span>
              </div>
            )}

            {/* Etymology */}
            {explanation.etymology && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h5 className="font-semibold text-gray-700 mb-2">词源</h5>
                <div className="text-gray-600 text-sm">{explanation.etymology}</div>
              </div>
            )}

            {/* Synonyms */}
            {explanation.synonyms && explanation.synonyms.length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h5 className="font-semibold text-gray-700 mb-2">同义词</h5>
                <div className="text-gray-600 text-sm">
                  {explanation.synonyms.join(", ")}
                </div>
              </div>
            )}

            {/* Antonyms */}
            {explanation.antonyms && explanation.antonyms.length > 0 && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h5 className="font-semibold text-gray-700 mb-2">反义词</h5>
                <div className="text-gray-600 text-sm">
                  {explanation.antonyms.join(", ")}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end p-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}

export default SingleVocabExplanation;
