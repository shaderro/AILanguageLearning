import { useState, useEffect } from 'react'
import LearnPageLayout from '../shared/components/LearnPageLayout'
import LearnCard from '../shared/components/LearnCard'
import LearnDetailPage from '../shared/components/LearnDetailPage'
import ReviewCard from '../shared/components/ReviewCard'
import ReviewResults from '../shared/components/ReviewResults'
import { useGrammarList, useToggleGrammarStar, useRefreshData, useArticles } from '../../hooks/useApi'
import { apiService } from '../../services/api'
import { useUser } from '../../contexts/UserContext'
import { useLanguage } from '../../contexts/LanguageContext'

const GrammarDemo = () => {
  // 从 UserContext 获取当前用户
  const { userId, isGuest, isAuthenticated } = useUser()
  
  // 从 LanguageContext 获取选择的语言
  const { selectedLanguage } = useLanguage()
  
  // 学习状态过滤
  const [learnStatus, setLearnStatus] = useState('all')
  
  // 文章过滤
  const [textId, setTextId] = useState('all')
  
  // 获取文章列表（使用 useArticles hook，它会处理响应格式）
  const { data: articlesResponse, isLoading: articlesLoading } = useArticles(userId, selectedLanguage, isGuest)
  
  console.log('🔍 [GrammarDemo] useArticles 返回:', articlesResponse, 'loading:', articlesLoading)
  
  // 处理文章数据：提取数组并按字母顺序排序
  const articlesData = (() => {
    if (!articlesResponse) {
      console.log('⚠️ [GrammarDemo] articlesResponse 为空')
      return []
    }
    
    console.log('🔍 [GrammarDemo] articlesResponse 类型:', typeof articlesResponse)
    console.log('🔍 [GrammarDemo] articlesResponse.data 类型:', typeof articlesResponse?.data)
    console.log('🔍 [GrammarDemo] articlesResponse.data 是否为数组:', Array.isArray(articlesResponse?.data))
    
    // useArticles 返回的格式：响应拦截器处理后是 { data: [...], count: ... }
    let articles = []
    if (Array.isArray(articlesResponse?.data)) {
      articles = articlesResponse.data
      console.log('🔍 [GrammarDemo] 从 articlesResponse.data 提取:', articles.length, '篇')
    } else if (Array.isArray(articlesResponse)) {
      articles = articlesResponse
      console.log('🔍 [GrammarDemo] articlesResponse 直接是数组:', articles.length, '篇')
    } else {
      console.warn('⚠️ [GrammarDemo] 无法识别的 articlesResponse 格式:', articlesResponse)
    }
    
    // 按标题字母顺序排序
    if (articles.length > 0) {
      const sorted = articles.sort((a, b) => {
        const titleA = (a.title || a.text_title || '').toLowerCase()
        const titleB = (b.title || b.text_title || '').toLowerCase()
        return titleA.localeCompare(titleB)
      })
      console.log('🔍 [GrammarDemo] 排序后的文章:', sorted.length, '篇')
      return sorted
    }
    console.log('⚠️ [GrammarDemo] 文章列表为空')
    return []
  })()
  
  console.log('🔍 [GrammarDemo] 最终文章数据:', articlesData.length, '篇', articlesData.length > 0 ? articlesData[0] : '')
  
  // 使用API获取语法数据 - 传入 userId、isGuest、language、learnStatus 和 textId
  const { data: grammarData, isLoading, isError, error } = useGrammarList(userId, isGuest, selectedLanguage, learnStatus, textId)
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
  // 注意：language和learn_status过滤已经在API层面完成，这里只需要处理搜索过滤
  const allGrammar = grammarData?.data || []
  console.log(`🔍 [GrammarDemo] 当前过滤状态: learnStatus=${learnStatus}, language=${selectedLanguage}, 语法数量=${allGrammar.length}`)

  const [filterText, setFilterText] = useState('')
  const list = allGrammar.filter((g) => (filterText ? (g.rule_name || g.name || '').toLowerCase().includes(filterText.toLowerCase()) : true))

  const [selectedGrammar, setSelectedGrammar] = useState(null)
  const [selectedGrammarId, setSelectedGrammarId] = useState(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [isReviewMode, setIsReviewMode] = useState(false)
  const [reviewItems, setReviewItems] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [results, setResults] = useState([])

  // 🔧 新增：当选中语法时，获取完整的语法详情（包含examples）
  useEffect(() => {
    if (selectedGrammarId) {
      setIsLoadingDetail(true)
      console.log(`🔍 [GrammarDemo] Fetching grammar detail for ID: ${selectedGrammarId}`)
      
      apiService.getGrammarById(selectedGrammarId)
        .then(response => {
          console.log(`✅ [GrammarDemo] Grammar detail fetched:`, response)
          // 处理API响应格式
          const grammarData = response?.data || response
          setSelectedGrammar(grammarData)
          setIsLoadingDetail(false)
        })
        .catch(error => {
          console.error(`❌ [GrammarDemo] Error fetching grammar detail:`, error)
          setIsLoadingDetail(false)
        })
    }
  }, [selectedGrammarId])

  const startReview = () => {
    // 使用当前filter后的所有语法规则
    const filteredGrammar = list || []
    
    if (filteredGrammar.length === 0) {
      // 如果为空，显示提示（使用更友好的方式）
      const message = '当前筛选条件下没有语法规则，请更改筛选选项后再试'
      if (window.confirm(message)) {
        // 用户点击确定后不做任何操作，只是关闭提示
      }
      return
    }
    
    // 使用所有filter后的语法规则进行复习（不限制数量）
    const shuffled = [...filteredGrammar].sort(() => 0.5 - Math.random())
    setReviewItems(shuffled)
    setCurrentIndex(0)
    setResults([])
    setIsReviewMode(true)
  }

  const handleAnswer = async (choice) => {
    const item = reviewItems[currentIndex]
    setResults((prev) => [...prev, { item, choice }])
    
    // 如果用户选择"认识"，更新learn_status为mastered
    if (choice === 'know' && item.rule_id) {
      try {
        console.log(`🔄 [GrammarDemo] 正在更新语法规则 ${item.rule_id} 的学习状态为 mastered`)
        const response = await apiService.updateGrammar(item.rule_id, {
          learn_status: 'mastered'
        })
        console.log(`✅ [GrammarDemo] 更新成功:`, response)
        // 刷新数据
        refreshGrammar()
      } catch (error) {
        console.error(`❌ [GrammarDemo] 更新学习状态失败:`, error)
        console.error(`❌ [GrammarDemo] 错误详情:`, error.response?.data || error.message)
      }
    }
  }

  const handleNext = () => {
    if (currentIndex < reviewItems.length - 1) {
      setCurrentIndex((v) => v + 1)
    } else {
      // 显示结果页：保持复习模式为真，但将索引推进到长度以触发结果视图
      setCurrentIndex(reviewItems.length)
    }
  }

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((v) => v - 1)
    }
  }

  const handleFilterChange = (filterId, value) => {
    // 处理学习状态过滤
    if (filterId === 'learn_status') {
      setLearnStatus(value)
    }
    // 处理文章过滤
    if (filterId === 'text_id') {
      setTextId(value)
    } else if (typeof value === 'string') {
      // 保留原有的文本过滤逻辑（如果需要）
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
              onBack={() => setIsReviewMode(false)}
              onPrevCard={handlePrev}
              onNextCard={handleNext}
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
  if (selectedGrammarId) {
    return (
      <div className="h-full bg-gray-100 p-8">
        <div className="max-w-6xl mx-auto">
          <LearnDetailPage 
            type="grammar" 
            data={selectedGrammar}
            loading={isLoadingDetail}
            onBack={() => {
              setSelectedGrammar(null)
              setSelectedGrammarId(null)
            }}
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

  // 配置过滤器
  const articles = Array.isArray(articlesData) ? articlesData : []
  console.log('🔍 [GrammarDemo] 文章数据:', articles.length, '篇', articles.length > 0 ? articles[0] : '')
  
  const articleOptions = [
    { value: 'all', label: '全部文章' },
    ...articles
      .filter(article => article && (article.id || article.text_id)) // 过滤掉无效的文章
      .map(article => ({
        value: String(article.id || article.text_id),
        label: article.title || article.text_title || `文章 ${article.id || article.text_id}`
      }))
  ]
  
  console.log('🔍 [GrammarDemo] 文章选项:', articleOptions.length, '个', articleOptions.map(opt => opt.label))
  
  const filters = [
    {
      id: 'learn_status',
      label: '学习状态',
      options: [
        { value: 'all', label: '全部' },
        { value: 'mastered', label: '已掌握' },
        { value: 'not_mastered', label: '未掌握' }
      ],
      placeholder: '选择学习状态',
      value: learnStatus
    },
    {
      id: 'text_id',
      label: '文章',
      options: articleOptions,
      placeholder: '选择文章',
      value: textId
    }
  ]

  // 列表页：使用统一布局
  return (
    <LearnPageLayout
      title="语法学习"
      onStartReview={startReview}
      onSearch={(value) => setFilterText(value)}
      onFilterChange={handleFilterChange}
      filters={filters}
      showFilters={true}
      showSearch={true}
      backgroundClass="bg-gray-100"
      onRefresh={handleRefreshData}
      showRefreshButton={true}
    >
      {/* 显示当前语言过滤状态 */}
      {selectedLanguage !== 'all' && (
        <div className="col-span-full mb-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-700">
            <span className="font-medium">当前筛选：</span>{selectedLanguage}
            <span className="ml-2 text-gray-600">({list.length} 个语法规则)</span>
          </p>
        </div>
      )}
      
      {list.map((g) => (
        <LearnCard 
          key={g.rule_id} 
          type="grammar" 
          data={g} 
          onClick={() => setSelectedGrammarId(g.rule_id)}
          onToggleStar={handleToggleStar}
        />
      ))}
    </LearnPageLayout>
  )
}

export default GrammarDemo
