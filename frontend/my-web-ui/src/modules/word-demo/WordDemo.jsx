import { useState, useEffect } from 'react'
import { useVocabList, useWordInfo, useToggleVocabStar, useRefreshData } from '../../hooks/useApi'
import { apiService } from '../../services/api'
import LearnPageLayout from '../shared/components/LearnPageLayout'
import LearnCard from '../shared/components/LearnCard'
import LearnDetailPage from '../shared/components/LearnDetailPage'
import ReviewCard from '../shared/components/ReviewCard'
import ReviewResults from '../shared/components/ReviewResults'

function WordDemo() {
  const [selectedWord, setSelectedWord] = useState(null)
  const [selectedWordId, setSelectedWordId] = useState(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [isReviewMode, setIsReviewMode] = useState(false)
  const [reviewWords, setReviewWords] = useState([])
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0)
  const [reviewResults, setReviewResults] = useState([])

  // 使用 React Query 获取词汇数据
  const { data: vocabData, isLoading, isError, error } = useVocabList()

  // 单词查询功能
  const [searchTerm, setSearchTerm] = useState('')
  const wordInfo = useWordInfo(searchTerm)

  // 收藏功能
  const toggleStarMutation = useToggleVocabStar()
  
  // 数据刷新功能
  const { refreshVocab } = useRefreshData()

  // 🔧 新增：当选中词汇时，获取完整的词汇详情（包含examples）
  useEffect(() => {
    if (selectedWordId) {
      setIsLoadingDetail(true)
      console.log(`🔍 [WordDemo] Fetching vocab detail for ID: ${selectedWordId}`)
      
      apiService.getVocabById(selectedWordId)
        .then(response => {
          console.log(`✅ [WordDemo] Vocab detail fetched:`, response)
          // 处理API响应格式
          const vocabData = response?.data || response
          setSelectedWord(vocabData)
          setIsLoadingDetail(false)
        })
        .catch(error => {
          console.error(`❌ [WordDemo] Error fetching vocab detail:`, error)
          setIsLoadingDetail(false)
        })
    }
  }, [selectedWordId])

  const handleWordSelect = (word) => {
    // 🔧 修改：设置 ID 触发详情加载，而不是直接使用列表数据
    setSelectedWordId(word.vocab_id)
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

  const handleReviewAnswer = (choice) => {
    const currentWord = reviewWords[currentReviewIndex]
    setReviewResults((prev) => [...prev, { item: currentWord, choice }])
  }

  const handleNextReview = () => {
    if (currentReviewIndex < reviewWords.length - 1) {
      setCurrentReviewIndex((prev) => prev + 1)
    } else {
      // 显示结果页：保持复习模式为真，但将索引推进到长度以触发结果视图
      setCurrentReviewIndex(reviewWords.length)
    }
  }

  const handleBackToWords = () => {
    setIsReviewMode(false)
    setSelectedWord(null)
    setSelectedWordId(null)
  }

  const handleFilterChange = (filterId, value) => {
    // 这里可以根据需要在本地过滤 vocab 列表
  }

  const handleToggleStar = (item) => {
    const newStarredState = !item.is_starred
    toggleStarMutation.mutate({
      id: item.vocab_id,
      isStarred: newStarredState
    })
  }

  const handleRefreshData = () => {
    refreshVocab()
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

  // 复习模式
  if (isReviewMode) {
    if (currentReviewIndex < reviewWords.length) {
      return (
        <div className="h-full bg-gray-100 p-8">
          <div className="max-w-6xl mx-auto">
            <ReviewCard
              type="vocab"
              item={reviewWords[currentReviewIndex]}
              index={currentReviewIndex}
              total={reviewWords.length}
              onAnswer={handleReviewAnswer}
              onNext={handleNextReview}
            />
          </div>
        </div>
      )
    }
    return (
      <div className="h-full bg-gray-100 p-8">
        <div className="max-w-6xl mx-auto">
          <ReviewResults results={reviewResults} onBack={handleBackToWords} />
        </div>
      </div>
    )
  }

  // 详情页面
  if (selectedWordId) {
    return (
      <div className="h-full bg-gray-100 p-8">
        <div className="max-w-6xl mx-auto">
          <LearnDetailPage
            type="vocab"
            data={selectedWord}
            loading={isLoadingDetail}
            onBack={() => {
              setSelectedWord(null)
              setSelectedWordId(null)
            }}
            onToggleStar={handleToggleStar}
          />
        </div>
      </div>
    )
  }

  // 主列表页面（使用统一布局）
  const list = (vocabData?.data || [])
    .filter((w) => (searchTerm ? String(w.vocab_body || '').toLowerCase().includes(searchTerm.toLowerCase()) : true))

  return (
    <LearnPageLayout
      title="词汇学习"
      onStartReview={handleStartReview}
      onSearch={(value) => setSearchTerm(value)}
      onFilterChange={handleFilterChange}
      onRefresh={handleRefreshData}
      showFilters={true}
      showSearch={true}
      showRefreshButton={true}
      backgroundClass="bg-gray-100"
    >
      {/* 搜索建议区域（可选） */}
      {wordInfo.isSuccess && wordInfo.data?.status === 'success' && (
        <div className="col-span-1 md:col-span-2 lg:col-span-3">
          <div className="mt-0 mb-4 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold">{wordInfo.data.data.word}</h3>
            <p>{wordInfo.data.data.definition || '暂无定义'}</p>
          </div>
        </div>
      )}

      {/* 词汇列表 */}
      {list.map((word) => (
        <LearnCard
          key={word.vocab_id}
          type="vocab"
          data={word}
          onClick={() => handleWordSelect(word)}
          onToggleStar={handleToggleStar}
        />
      ))}
    </LearnPageLayout>
  )
}

export default WordDemo 