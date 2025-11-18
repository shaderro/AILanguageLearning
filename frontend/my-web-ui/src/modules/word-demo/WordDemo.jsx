import { useState, useEffect } from 'react'
import { useVocabList, useWordInfo, useToggleVocabStar, useRefreshData, useArticles } from '../../hooks/useApi'
import { apiService } from '../../services/api'
import { useUser } from '../../contexts/UserContext'
import { useLanguage } from '../../contexts/LanguageContext'
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
  
  // 从 UserContext 获取当前用户
  const { userId, isGuest, isAuthenticated } = useUser()
  
  // 从 LanguageContext 获取选择的语言
  const { selectedLanguage } = useLanguage()

  // 学习状态过滤
  const [learnStatus, setLearnStatus] = useState('all')
  
  // 文章过滤
  const [textId, setTextId] = useState('all')
  
  // 时间排序：'desc' 倒序（最新在前），'asc' 正序（最早在前）
  const [sortOrder, setSortOrder] = useState('desc')
  
  // 获取文章列表（使用 useArticles hook，它会处理响应格式）
  const { data: articlesResponse, isLoading: articlesLoading } = useArticles(userId, selectedLanguage, isGuest)
  
  console.log('🔍 [WordDemo] useArticles 返回:', articlesResponse, 'loading:', articlesLoading)
  
  // 处理文章数据：提取数组并按字母顺序排序
  const articlesData = (() => {
    if (!articlesResponse) {
      console.log('⚠️ [WordDemo] articlesResponse 为空')
      return []
    }
    
    console.log('🔍 [WordDemo] articlesResponse 类型:', typeof articlesResponse)
    console.log('🔍 [WordDemo] articlesResponse.data 类型:', typeof articlesResponse?.data)
    console.log('🔍 [WordDemo] articlesResponse.data 是否为数组:', Array.isArray(articlesResponse?.data))
    
    // useArticles 返回的格式：响应拦截器处理后是 { data: [...], count: ... }
    let articles = []
    if (Array.isArray(articlesResponse?.data)) {
      articles = articlesResponse.data
      console.log('🔍 [WordDemo] 从 articlesResponse.data 提取:', articles.length, '篇')
    } else if (Array.isArray(articlesResponse)) {
      articles = articlesResponse
      console.log('🔍 [WordDemo] articlesResponse 直接是数组:', articles.length, '篇')
    } else {
      console.warn('⚠️ [WordDemo] 无法识别的 articlesResponse 格式:', articlesResponse)
    }
    
    // 按标题字母顺序排序
    if (articles.length > 0) {
      const sorted = articles.sort((a, b) => {
        const titleA = (a.title || a.text_title || '').toLowerCase()
        const titleB = (b.title || b.text_title || '').toLowerCase()
        return titleA.localeCompare(titleB)
      })
      console.log('🔍 [WordDemo] 排序后的文章:', sorted.length, '篇')
      return sorted
    }
    console.log('⚠️ [WordDemo] 文章列表为空')
    return []
  })()
  
  console.log('🔍 [WordDemo] 最终文章数据:', articlesData.length, '篇', articlesData.length > 0 ? articlesData[0] : '')

  // 使用 React Query 获取词汇数据 - 传入 userId、isGuest、language、learnStatus 和 textId
  const { data: vocabData, isLoading, isError, error } = useVocabList(userId, isGuest, selectedLanguage, learnStatus, textId)

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
    // 使用当前filter和排序后的所有词汇（保持时间排序）
    // 注意：这里需要在函数内部重新计算 list，因为 list 是在组件渲染时计算的
    const allVocabs = vocabData?.data || []
    const filteredVocabs = allVocabs
      .filter((w) => (searchTerm ? String(w.vocab_body || '').toLowerCase().includes(searchTerm.toLowerCase()) : true))
    
    // 按时间排序（如果没有时间戳，使用 id 排序）
    const sortedList = [...filteredVocabs].sort((a, b) => {
      const timeA = a.updated_at || a.created_at
      const timeB = b.updated_at || b.created_at
      
      if (timeA && timeB) {
        const dateA = new Date(timeA).getTime()
        const dateB = new Date(timeB).getTime()
        if (sortOrder === 'desc') {
          return dateB - dateA
        } else {
          return dateA - dateB
        }
      }
      
      const idA = a.vocab_id || 0
      const idB = b.vocab_id || 0
      if (sortOrder === 'desc') {
        return idB - idA
      } else {
        return idA - idB
      }
    })
    
    if (sortedList.length === 0) {
      const message = '当前筛选条件下没有词汇，请更改筛选选项后再试'
      if (window.confirm(message)) {
        // 用户点击确定后不做任何操作，只是关闭提示
      }
      return
    }
    
    // 使用排序后的列表进行复习（保持时间排序，不随机打乱）
    setReviewWords(sortedList)
    setCurrentReviewIndex(0)
    setReviewResults([])
    setIsReviewMode(true)
  }

  const handleReviewAnswer = async (choice) => {
    const currentWord = reviewWords[currentReviewIndex]
    setReviewResults((prev) => [...prev, { item: currentWord, choice }])
    
    // 如果用户选择"认识"，更新learn_status为mastered
    if (choice === 'know' && currentWord.vocab_id) {
      try {
        console.log(`🔄 [WordDemo] 正在更新词汇 ${currentWord.vocab_id} 的学习状态为 mastered`)
        const response = await apiService.updateVocab(currentWord.vocab_id, {
          learn_status: 'mastered'
        })
        console.log(`✅ [WordDemo] 更新成功:`, response)
        // 刷新数据
        refreshVocab()
      } catch (error) {
        console.error(`❌ [WordDemo] 更新学习状态失败:`, error)
        console.error(`❌ [WordDemo] 错误详情:`, error.response?.data || error.message)
      }
    }
  }

  const handleNextReview = () => {
    if (currentReviewIndex < reviewWords.length - 1) {
      setCurrentReviewIndex((prev) => prev + 1)
    } else {
      // 显示结果页：保持复习模式为真，但将索引推进到长度以触发结果视图
      setCurrentReviewIndex(reviewWords.length)
    }
  }

  const handlePrevReview = () => {
    if (currentReviewIndex > 0) {
      setCurrentReviewIndex((prev) => prev - 1)
    }
  }

  const handleBackToWords = () => {
    setIsReviewMode(false)
    setSelectedWord(null)
    setSelectedWordId(null)
  }

  const handleFilterChange = (filterId, value) => {
    // 处理学习状态过滤
    if (filterId === 'learn_status') {
      setLearnStatus(value)
    }
    // 处理文章过滤
    if (filterId === 'text_id') {
      setTextId(value)
    }
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
              onBack={handleBackToWords}
              onPrevCard={handlePrevReview}
              onNextCard={handleNextReview}
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
  // 注意：language和learn_status过滤已经在API层面完成，这里只需要处理搜索过滤
  const allVocabs = vocabData?.data || []
  console.log(`🔍 [WordDemo] 当前过滤状态: learnStatus=${learnStatus}, language=${selectedLanguage}, 词汇数量=${allVocabs.length}`)
  
  // 过滤和排序
  const filteredVocabs = allVocabs
    .filter((w) => (searchTerm ? String(w.vocab_body || '').toLowerCase().includes(searchTerm.toLowerCase()) : true))
  
  // 按时间排序（如果没有时间戳，使用 id 排序）
  const list = [...filteredVocabs].sort((a, b) => {
    // 优先使用 updated_at，如果没有则使用 created_at
    const timeA = a.updated_at || a.created_at
    const timeB = b.updated_at || b.created_at
    
    // 如果两个都有时间戳，按时间排序
    if (timeA && timeB) {
      const dateA = new Date(timeA).getTime()
      const dateB = new Date(timeB).getTime()
      if (sortOrder === 'desc') {
        return dateB - dateA // 倒序：最新的在前
      } else {
        return dateA - dateB // 正序：最早的在前
      }
    }
    
    // 如果都没有时间戳，使用 id 排序
    const idA = a.vocab_id || 0
    const idB = b.vocab_id || 0
    if (sortOrder === 'desc') {
      return idB - idA // 倒序：id 大的在前（通常是更新的）
    } else {
      return idA - idB // 正序：id 小的在前（通常是更早的）
    }
  })

  // 配置过滤器
  const articles = Array.isArray(articlesData) ? articlesData : []
  console.log('🔍 [WordDemo] 文章数据:', articles.length, '篇', articles.length > 0 ? articles[0] : '')
  
  const articleOptions = [
    { value: 'all', label: '全部文章' },
    ...articles
      .filter(article => article && (article.id || article.text_id)) // 过滤掉无效的文章
      .map(article => ({
        value: String(article.id || article.text_id),
        label: article.title || article.text_title || `文章 ${article.id || article.text_id}`
      }))
  ]
  
  console.log('🔍 [WordDemo] 文章选项:', articleOptions.length, '个', articleOptions.map(opt => opt.label))
  
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

  return (
    <LearnPageLayout
      title="词汇学习"
      onStartReview={handleStartReview}
      onSearch={(value) => setSearchTerm(value)}
      onFilterChange={handleFilterChange}
      filters={filters}
      onRefresh={handleRefreshData}
      showFilters={true}
      showSearch={true}
      showRefreshButton={true}
      backgroundClass="bg-gray-100"
      sortOrder={sortOrder}
      onSortChange={setSortOrder}
    >
      {/* 显示当前语言过滤状态 */}
      {selectedLanguage !== 'all' && (
        <div className="col-span-full mb-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-700">
            <span className="font-medium">当前筛选：</span>{selectedLanguage}
            <span className="ml-2 text-gray-600">({list.length} 个词汇)</span>
          </p>
        </div>
      )}
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