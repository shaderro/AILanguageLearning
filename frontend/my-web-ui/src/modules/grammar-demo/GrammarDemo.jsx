import { useState } from 'react'
import LearnPageLayout from '../shared/components/LearnPageLayout'
import LearnCard from '../shared/components/LearnCard'
import LearnDetailPage from '../shared/components/LearnDetailPage'
import ReviewCard from '../shared/components/ReviewCard'
import ReviewResults from '../shared/components/ReviewResults'
import { useGrammarList, useToggleGrammarStar, useRefreshData } from '../../hooks/useApi'

const GrammarDemo = () => {
  // 使用API获取语法数据
  const { data: grammarData, isLoading, isError, error } = useGrammarList()
  const toggleStarMutation = useToggleGrammarStar()
  const { refreshGrammar } = useRefreshData()

  // 处理收藏功能
  const handleToggleStar = (grammarId, isStarred) => {
    toggleStarMutation.mutate({ id: grammarId, isStarred })
  }

  // 处理刷新数据
  const handleRefreshData = () => {
    refreshGrammar()
  }

  // 从API数据中提取语法列表
  const allGrammar = grammarData?.data || []

  const [filterText, setFilterText] = useState('')
  const list = allGrammar.filter((g) => (filterText ? g.rule_name.toLowerCase().includes(filterText.toLowerCase()) : true))

  const [selectedGrammar, setSelectedGrammar] = useState(null)
  const [isReviewMode, setIsReviewMode] = useState(false)
  const [reviewItems, setReviewItems] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [results, setResults] = useState([])

  const startReview = () => {
    const shuffled = [...allGrammar].sort(() => 0.5 - Math.random())
    setReviewItems(shuffled.slice(0, 5))
    setCurrentIndex(0)
    setResults([])
    setIsReviewMode(true)
  }

  const handleAnswer = (choice) => {
    const item = reviewItems[currentIndex]
    setResults((prev) => [...prev, { item, choice }])
  }

  const handleNext = () => {
    if (currentIndex < reviewItems.length - 1) {
      setCurrentIndex((v) => v + 1)
    } else {
      // 显示结果页：保持复习模式为真，但将索引推进到长度以触发结果视图
      setCurrentIndex(reviewItems.length)
    }
  }

  const handleFilterChange = (filterId, value) => {
    // 这里可以扩展为多条件过滤；目前示例：用任意filter改变即作为文本过滤
    if (typeof value === 'string') {
      setFilterText(value === 'all' ? '' : value)
    }
  }

  // 复习模式
  if (isReviewMode) {
    if (currentIndex < reviewItems.length) {
      return (
        <div className="h-full bg-gray-100 p-8">
          <div className="max-w-6xl mx-auto">
            <ReviewCard
              type="grammar"
              item={reviewItems[currentIndex]}
              index={currentIndex}
              total={reviewItems.length}
              onAnswer={handleAnswer}
              onNext={handleNext}
            />
          </div>
        </div>
      )
    }
    return (
      <div className="h-full bg-gray-100 p-8">
        <div className="max-w-6xl mx-auto">
          <ReviewResults results={results} onBack={() => setIsReviewMode(false)} />
        </div>
      </div>
    )
  }

  // 详情页
  if (selectedGrammar) {
    return (
      <div className="h-full bg-gray-100 p-8">
        <div className="max-w-6xl mx-auto">
          <LearnDetailPage 
            type="grammar" 
            data={selectedGrammar} 
            onBack={() => setSelectedGrammar(null)}
            onToggleStar={handleToggleStar}
          />
        </div>
      </div>
    )
  }

  // 加载状态
  if (isLoading) {
    return (
      <LearnPageLayout
        title="语法学习"
        onStartReview={startReview}
        onSearch={(value) => setFilterText(value)}
        onFilterChange={handleFilterChange}
        showFilters={true}
        showSearch={true}
        backgroundClass="bg-gray-100"
        onRefresh={handleRefreshData}
        showRefreshButton={true}
      >
        <div className="col-span-full flex justify-center items-center h-32">
          <div className="text-gray-500">加载语法数据中...</div>
        </div>
      </LearnPageLayout>
    )
  }

  // 错误状态
  if (isError) {
    return (
      <LearnPageLayout
        title="语法学习"
        onStartReview={startReview}
        onSearch={(value) => setFilterText(value)}
        onFilterChange={handleFilterChange}
        showFilters={true}
        showSearch={true}
        backgroundClass="bg-gray-100"
        onRefresh={handleRefreshData}
        showRefreshButton={true}
      >
        <div className="col-span-full flex justify-center items-center h-32">
          <div className="text-red-500">加载语法数据失败: {error?.message}</div>
        </div>
      </LearnPageLayout>
    )
  }

  // 列表页：使用统一布局
  return (
    <LearnPageLayout
      title="语法学习"
      onStartReview={startReview}
      onSearch={(value) => setFilterText(value)}
      onFilterChange={handleFilterChange}
      showFilters={true}
      showSearch={true}
      backgroundClass="bg-gray-100"
      onRefresh={handleRefreshData}
      showRefreshButton={true}
    >
      {list.map((g) => (
        <LearnCard 
          key={g.rule_id} 
          type="grammar" 
          data={g} 
          onClick={() => setSelectedGrammar(g)}
          onToggleStar={handleToggleStar}
        />
      ))}
    </LearnPageLayout>
  )
}

export default GrammarDemo
