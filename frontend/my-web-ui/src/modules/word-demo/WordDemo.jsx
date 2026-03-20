import { useState, useEffect } from 'react'
import { useVocabList, useWordInfo, useToggleVocabStar, useRefreshData, useArticles } from '../../hooks/useApi'
import { apiService } from '../../services/api'
import { useUser } from '../../contexts/UserContext'
import { useLanguage } from '../../contexts/LanguageContext'
import LearnPageLayout from '../shared/components/LearnPageLayout'
import LearnCard from '../shared/components/LearnCard'
import LearnDetailPage from '../shared/components/LearnDetailPage'
import ReviewCard from '../shared/components/ReviewCard'
import VocabReviewCard from '../../components/features/review/VocabReviewCard'
import ReviewResults from '../shared/components/ReviewResults'
import { useUIText } from '../../i18n/useUIText'
import VocabDetailCard from '../../components/features/vocab/VocabDetailCard'

function WordDemo() {
  const [selectedWord, setSelectedWord] = useState(null)
  const [selectedWordId, setSelectedWordId] = useState(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  // 🔧 缓存详情页面的词汇数据，避免切换时重新加载
  const [detailPageCache, setDetailPageCache] = useState(new Map())
  // 🔧 延迟显示加载UI的状态（超过0.5s才显示）
  const [showLoadingUI, setShowLoadingUI] = useState(false)
  // 🔧 保存上一个卡片数据，在加载期间保持显示
  const [previousWord, setPreviousWord] = useState(null)
  const [isReviewMode, setIsReviewMode] = useState(false)
  const [reviewWords, setReviewWords] = useState([])
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0)
  const [reviewResults, setReviewResults] = useState([])
  // 🔧 缓存预加载的词汇详情
  const [vocabDetailCache, setVocabDetailCache] = useState(new Map())
  
  // 从 UserContext 获取当前用户
  const { userId, isGuest } = useUser()
  
  // 从 LanguageContext 获取选择的语言
  const { selectedLanguage } = useLanguage()
  const t = useUIText()

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

  // 🔧 新增：当选中词汇时，获取完整的词汇详情（包含examples）- 优化：延迟加载UI显示
  useEffect(() => {
    if (selectedWordId) {
      // 🔧 先检查缓存
      const cached = detailPageCache.get(selectedWordId)
      if (cached) {
        console.log(`✅ [WordDemo] 使用缓存的词汇详情: ${selectedWordId}`)
        setSelectedWord(cached)
        setIsLoadingDetail(false)
        setShowLoadingUI(false)
        setPreviousWord(cached)
        return
      }
      
      // 🔧 如果缓存中没有，先尝试从列表数据中获取
      const allVocabs = vocabData?.data || []
      const listItem = allVocabs.find(w => w.vocab_id === selectedWordId)
      if (listItem && listItem.examples && Array.isArray(listItem.examples) && listItem.examples.length > 0) {
        // 列表数据中已有完整数据，直接使用并缓存
        setSelectedWord(listItem)
        setIsLoadingDetail(false)
        setShowLoadingUI(false)
        setPreviousWord(listItem)
        setDetailPageCache(prev => new Map(prev).set(selectedWordId, listItem))
        return
      }
      
      // 🔧 需要从API加载：保持上一个卡片显示，延迟0.5s后才显示加载UI
      setIsLoadingDetail(true)
      setShowLoadingUI(false) // 先不显示加载UI
      // 🔧 previousWord 已在切换时保存，这里不需要再次设置
      
      // 🔧 延迟0.5s后显示加载UI
      const loadingUITimer = setTimeout(() => {
        setShowLoadingUI(true)
      }, 500)
      
      console.log(`🔍 [WordDemo] Fetching vocab detail for ID: ${selectedWordId}`)
      
      apiService.getVocabById(selectedWordId)
        .then(response => {
          console.log(`✅ [WordDemo] Vocab detail fetched:`, response)
          // 处理API响应格式
          const vocabData = response?.data || response
          setSelectedWord(vocabData)
          setIsLoadingDetail(false)
          setShowLoadingUI(false)
          setPreviousWord(vocabData)
          // 🔧 缓存数据
          setDetailPageCache(prev => new Map(prev).set(selectedWordId, vocabData))
          clearTimeout(loadingUITimer)
        })
        .catch(error => {
          console.error(`❌ [WordDemo] Error fetching vocab detail:`, error)
          // 🔧 如果API失败，尝试使用列表数据作为后备
          if (listItem) {
            setSelectedWord(listItem)
            setPreviousWord(listItem)
            setDetailPageCache(prev => new Map(prev).set(selectedWordId, listItem))
          }
          setIsLoadingDetail(false)
          setShowLoadingUI(false)
          clearTimeout(loadingUITimer)
        })
      
      // 🔧 清理定时器
      return () => {
        clearTimeout(loadingUITimer)
      }
    } else {
      setPreviousWord(null)
      setShowLoadingUI(false)
    }
  }, [selectedWordId, vocabData, detailPageCache, selectedWord])

  const handleWordSelect = (word) => {
    // 🔧 修改：设置 ID 触发详情加载，而不是直接使用列表数据
    setSelectedWordId(word.vocab_id)
  }

  const handleStartReview = async () => {
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
      const message = t('当前筛选条件下没有词汇，请更改筛选选项后再试')
      if (window.confirm(message)) {
        // 用户点击确定后不做任何操作，只是关闭提示
      }
      return
    }
    
    // 🔧 预加载所有词汇的详情（包含 examples）
    const newCache = new Map()
    const loadPromises = sortedList.map(async (vocab) => {
      // 如果列表数据中已经有 examples，直接使用
      if (vocab.examples && Array.isArray(vocab.examples) && vocab.examples.length > 0) {
        newCache.set(vocab.vocab_id, vocab)
        return
      }
      
      // 否则，异步加载详情
      try {
        const response = await apiService.getVocabById(vocab.vocab_id)
        const detailData = response?.data?.data || response?.data || response
        if (detailData) {
          newCache.set(vocab.vocab_id, { ...vocab, ...detailData })
        } else {
          newCache.set(vocab.vocab_id, vocab)
        }
      } catch (error) {
        console.warn(`⚠️ [WordDemo] 预加载词汇 ${vocab.vocab_id} 详情失败:`, error)
        newCache.set(vocab.vocab_id, vocab)
      }
    })
    
    // 使用排序后的列表进行复习（保持时间排序，不随机打乱）
    console.log('🔁 [WordDemo] 开始词汇复习，总题数:', sortedList.length)
    setReviewWords(sortedList)
    setCurrentReviewIndex(0)
    setReviewResults([])
    setIsReviewMode(true)
    
    // 🔧 后台预加载详情（不阻塞界面）
    Promise.all(loadPromises).then(() => {
      setVocabDetailCache(newCache)
      console.log(`✅ [WordDemo] 预加载完成，缓存了 ${newCache.size} 个词汇详情`)
    })
  }

  const handleReviewAnswer = async (choice) => {
    const currentWord = reviewWords[currentReviewIndex]
    setReviewResults((prev) => [...prev, { item: currentWord, choice }])
    console.log('📝 [WordDemo] 记录复习答案:', {
      vocab_id: currentWord?.vocab_id,
      choice,
      currentIndex: currentReviewIndex,
      totalWords: reviewWords.length,
    })
    
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
    console.log('➡️ [WordDemo] 请求下一题:', {
      currentIndex: currentReviewIndex,
      totalWords: reviewWords.length,
      resultsCount: reviewResults.length,
    })
    // 🔧 防止连续快速点击导致的卡顿
    if (currentReviewIndex < reviewWords.length - 1) {
      setCurrentReviewIndex((prev) => {
        // 确保不会超出范围
        const next = prev + 1
        return next < reviewWords.length ? next : prev
      })
    } else {
      // 显示结果页：保持复习模式为真，但将索引推进到长度以触发结果视图
      setCurrentReviewIndex(reviewWords.length)
      console.log('✅ [WordDemo] 已到最后一题，推进到结算页索引:', reviewWords.length)
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
    // 🔧 清理缓存（可选，也可以保留以便下次快速加载）
    // setVocabDetailCache(new Map())
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
        <div className="text-lg">{t('加载词汇数据中...')}</div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center.h-full">
        <div className="text-red-500">{t('加载失败')}: {error?.message}</div>
      </div>
    )
  }

  // 复习模式
  if (isReviewMode) {
    const isReviewComplete =
      reviewWords.length > 0 && reviewResults.length >= reviewWords.length

    console.log('🔍 [WordDemo] 渲染复习模式:', {
      currentIndex: currentReviewIndex,
      totalWords: reviewWords.length,
      resultsCount: reviewResults.length,
      isReviewComplete,
    })

    if (isReviewComplete && currentReviewIndex < reviewWords.length) {
      console.warn('⚠️ [WordDemo] 复习结果已完成但索引未推进到末尾，强制显示结算页', {
        currentIndex: currentReviewIndex,
        totalWords: reviewWords.length,
        resultsCount: reviewResults.length,
      })
    }

    if (!isReviewComplete && currentReviewIndex < reviewWords.length) {
      const currentVocab = reviewWords[currentReviewIndex]
      // 🔧 优先使用缓存中的完整数据
      const cachedVocab = vocabDetailCache.get(currentVocab.vocab_id)
      const vocabToShow = cachedVocab || currentVocab
      
      return (
        <div className="h-full bg-white p-8">
          <div className="max-w-6xl mx-auto">
            <VocabReviewCard
              key={vocabToShow?.vocab_id}
              vocab={vocabToShow}
              currentProgress={currentReviewIndex + 1}
              totalProgress={reviewWords.length}
              onClose={handleBackToWords}
              onPrevious={currentReviewIndex > 0 ? handlePrevReview : null}
              onNext={currentReviewIndex < reviewWords.length - 1 ? handleNextReview : null}
              onDontKnow={() => {
                handleReviewAnswer('unknown')
                setTimeout(() => {
                  handleNextReview()
                }, 300)
              }}
              onKnow={() => {
                handleReviewAnswer('know')
                setTimeout(() => {
                  handleNextReview()
                }, 300)
              }}
            />
          </div>
        </div>
      )
    }
    return (
      <div className="h-full bg-white p-8">
        <div className="max-w-6xl mx-auto">
          <ReviewResults results={reviewResults} onBack={handleBackToWords} />
        </div>
      </div>
    )
  }

  // 详情页面
  if (selectedWordId) {
    // 计算当前过滤和排序后的列表
    const allVocabs = vocabData?.data || []
    const filteredVocabs = allVocabs
      .filter((w) => (searchTerm ? String(w.vocab_body || '').toLowerCase().includes(searchTerm.toLowerCase()) : true))
    
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
    
    // 找到当前词汇在列表中的索引
    const currentIndex = sortedList.findIndex(w => w.vocab_id === selectedWordId)
    
    const handlePreviousVocab = () => {
      if (currentIndex > 0) {
        // 🔧 在切换前保存当前卡片，以便在加载期间显示
        if (selectedWord) {
          setPreviousWord(selectedWord)
        }
        const prevWord = sortedList[currentIndex - 1]
        setSelectedWordId(prevWord.vocab_id)
      }
    }
    
    const handleNextVocab = () => {
      if (currentIndex < sortedList.length - 1) {
        // 🔧 在切换前保存当前卡片，以便在加载期间显示
        if (selectedWord) {
          setPreviousWord(selectedWord)
        }
        const nextWord = sortedList[currentIndex + 1]
        setSelectedWordId(nextWord.vocab_id)
      }
    }
    
    // 🔧 在加载期间，如果数据未缓存且加载时间超过0.5s，显示加载UI；否则显示上一个卡片或当前卡片
    // 🔧 如果 previousWord 存在，在加载期间继续显示；否则显示当前卡片或加载状态
    const displayWord = selectedWord || previousWord
    // 🔧 如果 previousWord 不存在（首次加载），立即显示加载状态；否则延迟0.5s
    const shouldShowLoading = isLoadingDetail && !detailPageCache.has(selectedWordId) && (showLoadingUI || !previousWord)
    
    return (
      <div className="h-full bg-white p-8" style={{ backgroundColor: 'white', minHeight: '100%' }}>
        <div className="max-w-6xl mx-auto">
          <VocabDetailCard
            vocab={displayWord}
            loading={shouldShowLoading}
            onPrevious={currentIndex > 0 ? handlePreviousVocab : null}
            onNext={currentIndex < sortedList.length - 1 ? handleNextVocab : null}
            onBack={() => {
              setSelectedWord(null)
              setSelectedWordId(null)
              setPreviousWord(null)
              setShowLoadingUI(false)
            }}
            currentIndex={currentIndex}
            totalCount={sortedList.length}
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
    { value: 'all', label: t('全部文章') },
    ...articles
      .filter(article => article && (article.id || article.text_id))
      .map((article) => {
        const fallbackLabel = `${t('文章')} ${article.id || article.text_id}`
        return {
          value: String(article.id || article.text_id),
          label: article.title || article.text_title || fallbackLabel
        }
      })
  ]
  
  console.log('🔍 [WordDemo] 文章选项:', articleOptions.length, '个', articleOptions.map(opt => opt.label))
  
  const filters = [
    {
      id: 'learn_status',
      label: t('学习状态'),
      options: [
        { value: 'all', label: t('全部') },
        { value: 'mastered', label: t('已掌握') },
        { value: 'not_mastered', label: t('未掌握') }
      ],
      placeholder: t('选择学习状态'),
      value: learnStatus
    },
    {
      id: 'text_id',
      label: t('文章'),
      options: articleOptions,
      placeholder: t('选择文章'),
      value: textId
    }
  ]

  return (
    <LearnPageLayout
      title=""
      onStartReview={handleStartReview}
      onSearch={(value) => setSearchTerm(value)}
      onFilterChange={handleFilterChange}
      filters={filters}
      onRefresh={handleRefreshData}
      showFilters={true}
      showSearch={false}
      showRefreshButton={false}
      backgroundClass="bg-white"
      sortOrder={sortOrder}
      onSortChange={setSortOrder}
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