import { useState } from 'react'
import { useVocabList, useWordInfo } from '../../hooks/useApi'
import WordCard from './components/WordCard'
import WordCardDetail from './components/WordCardDetail'
import StartReviewButton from '../shared/components/StartReviewButton'
import ReviewCard from './components/ReviewCard'
import ReviewResults from './components/ReviewResults'

function WordDemo() {
  const [selectedWord, setSelectedWord] = useState(null)
  const [isReviewMode, setIsReviewMode] = useState(false)
  const [reviewWords, setReviewWords] = useState([])
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0)
  const [reviewResults, setReviewResults] = useState([])

  // 使用 React Query 获取词汇数据
  const { data: vocabData, isLoading, isError, error } = useVocabList()

  // 单词查询功能
  const [searchTerm, setSearchTerm] = useState('')
  const wordInfo = useWordInfo(searchTerm)

  const handleWordSelect = (word) => {
    setSelectedWord(word)
  }

  const handleStartReview = () => {
    if (vocabData?.data) {
      // 随机选择词汇进行复习
      const shuffled = [...vocabData.data].sort(() => 0.5 - Math.random())
      setReviewWords(shuffled.slice(0, 5)) // 选择5个词汇
      setCurrentReviewIndex(0)
      setReviewResults([])
      setIsReviewMode(true)
    }
  }

  const handleReviewAnswer = (isCorrect) => {
    const currentWord = reviewWords[currentReviewIndex]
    setReviewResults(prev => [...prev, { word: currentWord, isCorrect }])
    
    if (currentReviewIndex < reviewWords.length - 1) {
      setCurrentReviewIndex(prev => prev + 1)
    } else {
      setIsReviewMode(false)
    }
  }

  const handleBackToWords = () => {
    setIsReviewMode(false)
    setSelectedWord(null)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg">加载词汇数据中...</div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500">加载失败: {error.message}</div>
      </div>
    )
  }

  if (isReviewMode) {
    if (currentReviewIndex < reviewWords.length) {
      return (
        <ReviewCard
          word={reviewWords[currentReviewIndex]}
          onAnswer={handleReviewAnswer}
          currentIndex={currentReviewIndex}
          totalCount={reviewWords.length}
        />
      )
    } else {
      return (
        <ReviewResults
          results={reviewResults}
          onBackToWords={handleBackToWords}
        />
      )
    }
  }

  if (selectedWord) {
    return (
      <WordCardDetail
        word={selectedWord}
        onBack={() => setSelectedWord(null)}
      />
    )
  }

  return (
    <div className="h-full bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">词汇学习</h1>
          <StartReviewButton onClick={handleStartReview} />
        </div>

        {/* 搜索功能 */}
        <div className="mb-6">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="搜索词汇..."
              className="flex-1 px-4 py-2 border rounded-lg"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          {wordInfo.isSuccess && wordInfo.data.status === 'success' && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold">{wordInfo.data.data.word}</h3>
              <p>{wordInfo.data.data.definition || '暂无定义'}</p>
            </div>
          )}
        </div>

        {/* 词汇列表 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {vocabData?.data?.map((word) => (
            <WordCard
              key={word.vocab_id}
              word={word}
              onClick={() => handleWordSelect(word)}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

export default WordDemo 