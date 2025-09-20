import { useState, useMemo } from 'react'
import LearnPageLayout from '../shared/components/LearnPageLayout'
import LearnCard from '../shared/components/LearnCard'
import LearnDetailPage from '../shared/components/LearnDetailPage'
import ReviewCard from '../shared/components/ReviewCard'
import ReviewResults from '../shared/components/ReviewResults'

const GrammarDemo = () => {
  // Demo 数据：可替换为从后端获取
  const allGrammar = useMemo(
    () => [
      { rule: 'present-perfect', rule_name: 'Present Perfect', structure: 'have/has + past participle', usage: '过去发生对现在有影响', example: 'I have eaten already.' },
      { rule: 'past-continuous', rule_name: 'Past Continuous', structure: 'was/were + v-ing', usage: '过去某时正在进行', example: 'I was reading when he called.' },
      { rule: 'future-simple', rule_name: 'Future Simple', structure: 'will + verb', usage: '一般将来时', example: 'I will go tomorrow.' },
      { rule: 'conditional', rule_name: 'Conditional', structure: 'if + clause', usage: '条件句', example: 'If it rains, we will stay home.' },
    ],
    []
  )

  const [filterText, setFilterText] = useState('')
  const list = allGrammar.filter((g) => (filterText ? (g.rule_name || g.rule).toLowerCase().includes(filterText.toLowerCase()) : true))

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
          <LearnDetailPage type="grammar" data={selectedGrammar} onBack={() => setSelectedGrammar(null)} />
        </div>
      </div>
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
    >
      {list.map((g) => (
        <LearnCard key={g.rule} type="grammar" data={g} onClick={() => setSelectedGrammar(g)} />
      ))}
    </LearnPageLayout>
  )
}

export default GrammarDemo
