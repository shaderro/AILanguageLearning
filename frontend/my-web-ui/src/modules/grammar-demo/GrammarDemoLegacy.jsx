import { useState, useEffect } from 'react'
import LearnPageLayout from '../shared/components/LearnPageLayout'
import LearnCard from '../shared/components/LearnCard'
import LearnDetailPage from '../shared/components/LearnDetailPage'
import ReviewCard from '../shared/components/ReviewCard'
import ReviewResults from '../shared/components/ReviewResults'
import GrammarReviewCard from '../../components/features/review/GrammarReviewCard'
import GrammarDetailCard from '../../components/features/grammar/GrammarDetailCard'
import { useGrammarList, useToggleGrammarStar, useRefreshData, useArticles } from '../../hooks/useApi'
import { apiService } from '../../services/api'
import { useUser } from '../../contexts/UserContext'
import { useLanguage } from '../../contexts/LanguageContext'
import { useUIText } from '../../i18n/useUIText'

const GrammarDemo = () => {
  // 从 UserContext 获取当前用户
  const { userId, isGuest, isAuthenticated } = useUser()
  
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

  const [filterText, setFilterText] = useState('')
  
  // 过滤和排序
  const filteredGrammar = allGrammar.filter((g) => (filterText ? (g.rule_name || g.name || '').toLowerCase().includes(filterText.toLowerCase()) : true))
  
  // 按时间排序（如果没有时间戳，使用 id 排序）
  const list = [...filteredGrammar].sort((a, b) => {
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
    const idA = a.rule_id || 0
    const idB = b.rule_id || 0
    if (sortOrder === 'desc') {
      return idB - idA // 倒序：id 大的在前（通常是更新的）
    } else {
      return idA - idB // 正序：id 小的在前（通常是更早的）
    }
  })

  // 🔧 从 URL 参数读取 grammarId（用于新标签页打开）
  const getGrammarIdFromURL = () => {
    const params = new URLSearchParams(window.location.search)
    const grammarId = params.get('grammarId')
    return grammarId ? parseInt(grammarId) : null
  }

  const clearGrammarIdFromURL = () => {
    const params = new URLSearchParams(window.location.search)
    if (!params.has('grammarId')) return
    params.delete('grammarId')
    const newUrl = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ''}`
    window.history.replaceState({}, '', newUrl)
  }
  
  const [selectedGrammar, setSelectedGrammar] = useState(null)
  const [selectedGrammarId, setSelectedGrammarId] = useState(null)
  const [selectedGrammarIndex, setSelectedGrammarIndex] = useState(-1)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  // 🔧 缓存详情页面的语法数据，避免切换时重新加载
  const [detailPageCache, setDetailPageCache] = useState(new Map())
  // 🔧 延迟显示加载UI的状态（超过0.5s才显示）
  const [showLoadingUI, setShowLoadingUI] = useState(false)
  // 🔧 保存上一个卡片数据，在加载期间保持显示
  const [previousGrammar, setPreviousGrammar] = useState(null)
  const [isReviewMode, setIsReviewMode] = useState(false)
  const [reviewItems, setReviewItems] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [results, setResults] = useState([])
  // 🔧 缓存预加载的语法详情
  const [grammarDetailCache, setGrammarDetailCache] = useState(new Map())
  
  // 🔧 从 URL 参数初始化 selectedGrammarId（用于新标签页打开）
  // 🔧 修复问题1：只在URL中明确包含grammarId时才设置（用于新标签页打开），而不是每次组件挂载都设置
  useEffect(() => {
    const urlGrammarId = getGrammarIdFromURL()
    // 🔧 如果URL中有grammarId，说明是从新标签页打开，应该显示详情页
    // 如果URL中没有grammarId，但selectedGrammarId有值，说明是用户点击了列表项，保持当前状态
    if (urlGrammarId && urlGrammarId !== selectedGrammarId) {
      console.log(`🔍 [GrammarDemo] URL中有grammarId=${urlGrammarId}，设置详情页`)
      setSelectedGrammarId(urlGrammarId)
      // 计算当前语法在列表中的索引（等待 allGrammar 加载完成）
      if (allGrammar.length > 0) {
        const index = allGrammar.findIndex(g => g.rule_id === urlGrammarId)
        if (index >= 0) {
          setSelectedGrammarIndex(index)
        }
      }
    } else if (!urlGrammarId && selectedGrammarId) {
      // 🔧 如果URL中没有grammarId，但selectedGrammarId有值，说明用户点击了导航栏的"语法"按钮
      // 应该清除selectedGrammarId，显示列表页
      console.log(`🔍 [GrammarDemo] URL中没有grammarId，清除selectedGrammarId，显示列表页`)
      setSelectedGrammarId(null)
      setSelectedGrammarIndex(-1)
      setSelectedGrammar(null)
    }
  }, []) // 只在组件挂载时执行一次
  
  // 🔧 当 allGrammar 加载完成后，如果 URL 中有 grammarId，设置索引
  useEffect(() => {
    const urlGrammarId = getGrammarIdFromURL()
    if (urlGrammarId && allGrammar.length > 0 && selectedGrammarIndex === -1) {
      const index = allGrammar.findIndex(g => g.rule_id === urlGrammarId)
      if (index >= 0) {
        setSelectedGrammarIndex(index)
        if (!selectedGrammarId) {
          setSelectedGrammarId(urlGrammarId)
        }
      }
    }
  }, [allGrammar, selectedGrammarIndex, selectedGrammarId])

  // 🔧 新增：当选中语法时，获取完整的语法详情（包含examples）- 优化：延迟加载UI显示
  useEffect(() => {
    if (selectedGrammarId) {
      // 🔧 先检查缓存
      const cached = detailPageCache.get(selectedGrammarId)
      if (cached) {
        console.log(`✅ [GrammarDemo] 使用缓存的语法详情: ${selectedGrammarId}`)
        setSelectedGrammar(cached)
        setIsLoadingDetail(false)
        setShowLoadingUI(false)
        setPreviousGrammar(cached)
        return
      }
      
      // 🔧 如果缓存中没有，先尝试从列表数据中获取
      const listItem = allGrammar.find(g => g.rule_id === selectedGrammarId)
      if (listItem && listItem.examples && Array.isArray(listItem.examples) && listItem.examples.length > 0) {
        // 列表数据中已有完整数据，直接使用并缓存
        setSelectedGrammar(listItem)
        setIsLoadingDetail(false)
        setShowLoadingUI(false)
        setPreviousGrammar(listItem)
        setDetailPageCache(prev => new Map(prev).set(selectedGrammarId, listItem))
        return
      }
      
      // 🔧 需要从API加载：保持上一个卡片显示，延迟0.5s后才显示加载UI
      setIsLoadingDetail(true)
      setShowLoadingUI(false) // 先不显示加载UI
      // 🔧 previousGrammar 已在切换时保存，这里不需要再次设置
      
      // 🔧 延迟0.5s后显示加载UI
      const loadingUITimer = setTimeout(() => {
        setShowLoadingUI(true)
      }, 500)
      
      console.log(`🔍 [GrammarDemo] Fetching grammar detail for ID: ${selectedGrammarId}`)
      
      // 先从列表中找到对应的语法规则作为后备
      if (listItem) {
        setPreviousGrammar(listItem)
      }
      
      apiService.getGrammarById(selectedGrammarId)
        .then(response => {
          console.log(`✅ [GrammarDemo] Grammar detail fetched:`, response)
          // 处理API响应格式：后端返回 { success: true, data: {...} }
          const grammarData = response?.data?.data || response?.data || response
          if (grammarData) {
            setSelectedGrammar(grammarData)
            setPreviousGrammar(grammarData)
            // 🔧 缓存数据
            setDetailPageCache(prev => new Map(prev).set(selectedGrammarId, grammarData))
          } else if (listItem) {
            // 如果 API 返回的数据格式不对，使用列表中的数据
            console.warn(`⚠️ [GrammarDemo] API response format unexpected, using list data`)
            setSelectedGrammar(listItem)
            setPreviousGrammar(listItem)
            setDetailPageCache(prev => new Map(prev).set(selectedGrammarId, listItem))
          }
          setIsLoadingDetail(false)
          setShowLoadingUI(false)
          clearTimeout(loadingUITimer)
        })
        .catch(error => {
          console.error(`❌ [GrammarDemo] Error fetching grammar detail:`, error)
          // 如果 API 失败，使用列表中的数据
          if (listItem) {
            console.log(`🔄 [GrammarDemo] Using list data as fallback`)
            setSelectedGrammar(listItem)
            setPreviousGrammar(listItem)
            setDetailPageCache(prev => new Map(prev).set(selectedGrammarId, listItem))
          } else {
            // 如果列表中也找不到，设置为 null 以显示错误
            setSelectedGrammar(null)
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
      setPreviousGrammar(null)
      setShowLoadingUI(false)
    }
  }, [selectedGrammarId, allGrammar, detailPageCache, selectedGrammar])

  const startReview = async () => {
    // 使用当前filter和排序后的所有语法规则（保持时间排序）
    // 注意：这里需要在函数内部重新计算 list，因为 list 是在组件渲染时计算的
    const allGrammar = grammarData?.data || []
    const filteredGrammar = allGrammar.filter((g) => (filterText ? (g.rule_name || g.name || '').toLowerCase().includes(filterText.toLowerCase()) : true))
    
    // 按时间排序（如果没有时间戳，使用 id 排序）
    const sortedList = [...filteredGrammar].sort((a, b) => {
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
      
      const idA = a.rule_id || 0
      const idB = b.rule_id || 0
      if (sortOrder === 'desc') {
        return idB - idA
      } else {
        return idA - idB
      }
    })
    
    if (sortedList.length === 0) {
      const message = t('当前筛选条件下没有语法规则，请更改筛选选项后再试')
      if (window.confirm(message)) {
        // 用户点击确定后不做任何操作，只是关闭提示
      }
      return
    }
    
    // 🔧 预加载所有语法规则的详情（包含 examples）
    const newCache = new Map()
    const loadPromises = sortedList.map(async (grammar) => {
      // 如果列表数据中已经有 examples，直接使用
      if (grammar.examples && Array.isArray(grammar.examples) && grammar.examples.length > 0) {
        newCache.set(grammar.rule_id, grammar)
        return
      }
      
      // 否则，异步加载详情
      try {
        const response = await apiService.getGrammarById(grammar.rule_id)
        const detailData = response?.data?.data || response?.data || response
        if (detailData) {
          newCache.set(grammar.rule_id, { ...grammar, ...detailData })
        } else {
          newCache.set(grammar.rule_id, grammar)
        }
      } catch (error) {
        console.warn(`⚠️ [GrammarDemo] 预加载语法 ${grammar.rule_id} 详情失败:`, error)
        newCache.set(grammar.rule_id, grammar)
      }
    })
    
    // 使用排序后的列表进行复习（保持时间排序，不随机打乱）
    setReviewItems(sortedList)
    setCurrentIndex(0)
    setResults([])
    setIsReviewMode(true)
    
    // 🔧 后台预加载详情（不阻塞界面）
    Promise.all(loadPromises).then(() => {
      setGrammarDetailCache(newCache)
      console.log(`✅ [GrammarDemo] 预加载完成，缓存了 ${newCache.size} 个语法详情`)
    })
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
    // 🔧 防止连续快速点击导致的卡顿
    if (currentIndex < reviewItems.length - 1) {
      setCurrentIndex((v) => {
        // 确保不会超出范围
        const next = v + 1
        return next < reviewItems.length ? next : v
      })
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
      return // 🔧 修复：避免继续执行，防止意外设置 filterText
    }
    // 处理文章过滤
    if (filterId === 'text_id') {
      setTextId(value)
      return // 🔧 修复：避免继续执行，防止意外设置 filterText
    }
    // 🔧 修复：只有明确的搜索过滤才设置 filterText
    // 其他情况不应该设置 filterText
  }

  // 复习模式
  if (isReviewMode) {
    if (currentIndex < reviewItems.length) {
      const currentItem = reviewItems[currentIndex]
      // 🔧 优先使用缓存中的完整数据
      const cachedGrammar = grammarDetailCache.get(currentItem.rule_id)
      const grammarToShow = cachedGrammar || currentItem
      
      // 处理答案的回调函数，需要同时调用 handleAnswer 和 handleNext
      const handleDontKnow = () => {
        handleAnswer('unknown')
        // 延迟一下再进入下一题，让用户看到反馈
        setTimeout(() => {
          handleNext()
        }, 300)
      }
      
      const handleKnow = () => {
        handleAnswer('know')
        // 延迟一下再进入下一题，让用户看到反馈
        setTimeout(() => {
          handleNext()
        }, 300)
      }
      
      return (
        <div className="h-full bg-white p-8">
          <div className="max-w-6xl mx-auto">
            <GrammarReviewCard
              grammar={grammarToShow}
              currentProgress={currentIndex + 1}
              totalProgress={reviewItems.length}
              onClose={() => setIsReviewMode(false)}
              onPrevious={handlePrev}
              onNext={handleNext}
              onDontKnow={handleDontKnow}
              onKnow={handleKnow}
            />
          </div>
        </div>
      )
    }
    return (
      <div className="h-full bg-white p-8">
        <div className="max-w-6xl mx-auto">
          <ReviewResults results={results} onBack={() => setIsReviewMode(false)} />
        </div>
      </div>
    )
  }

  // 详情页
  if (selectedGrammarId) {
    // 计算当前过滤和排序后的列表
    const allGrammar = grammarData?.data || []
    const filteredGrammar = allGrammar
      .filter((g) => (filterText ? (g.rule_name || g.name || '').toLowerCase().includes(filterText.toLowerCase()) : true))
    
    const sortedList = [...filteredGrammar].sort((a, b) => {
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
      
      const idA = a.rule_id || 0
      const idB = b.rule_id || 0
      if (sortOrder === 'desc') {
        return idB - idA
      } else {
        return idA - idB
      }
    })
    
    // 找到当前语法在列表中的索引
    const currentIndex = sortedList.findIndex(g => g.rule_id === selectedGrammarId)
    
    const handlePreviousGrammar = () => {
      if (currentIndex > 0) {
        // 🔧 在切换前保存当前卡片，以便在加载期间显示
        if (selectedGrammar) {
          setPreviousGrammar(selectedGrammar)
        }
        const prevGrammar = sortedList[currentIndex - 1]
        setSelectedGrammarId(prevGrammar.rule_id)
        setSelectedGrammarIndex(currentIndex - 1)
      }
    }
    
    const handleNextGrammar = () => {
      if (currentIndex < sortedList.length - 1) {
        // 🔧 在切换前保存当前卡片，以便在加载期间显示
        if (selectedGrammar) {
          setPreviousGrammar(selectedGrammar)
        }
        const nextGrammar = sortedList[currentIndex + 1]
        setSelectedGrammarId(nextGrammar.rule_id)
        setSelectedGrammarIndex(currentIndex + 1)
      }
    }
    
    // 🔧 在加载期间，如果数据未缓存且加载时间超过0.5s，显示加载UI；否则显示上一个卡片或当前卡片
    // 🔧 如果 previousGrammar 存在，在加载期间继续显示；否则显示当前卡片或加载状态
    const displayGrammar = selectedGrammar || previousGrammar
    // 🔧 如果 previousGrammar 不存在（首次加载），立即显示加载状态；否则延迟0.5s
    const shouldShowLoading = isLoadingDetail && !detailPageCache.has(selectedGrammarId) && (showLoadingUI || !previousGrammar)
    
    return (
      <div className="h-full bg-white p-8" style={{ backgroundColor: 'white', minHeight: '100%' }}>
        <div className="max-w-6xl mx-auto">
          <GrammarDetailCard
            grammar={displayGrammar}
            loading={shouldShowLoading}
            onPrevious={currentIndex > 0 ? handlePreviousGrammar : null}
            onNext={currentIndex < sortedList.length - 1 ? handleNextGrammar : null}
            onBack={() => {
              clearGrammarIdFromURL()
              setSelectedGrammar(null)
              setSelectedGrammarId(null)
              setSelectedGrammarIndex(-1)
              setPreviousGrammar(null)
              setShowLoadingUI(false)
            }}
            currentIndex={currentIndex}
            totalCount={sortedList.length}
          />
        </div>
      </div>
    )
  }

  // 配置过滤器（在所有状态下都需要）
  const articles = Array.isArray(articlesData) ? articlesData : []
  console.log('🔍 [GrammarDemo] 文章数据:', articles.length, '篇', articles.length > 0 ? articles[0] : '')
  
  const articleOptions = [
    { value: 'all', label: t('全部文章') },
    ...articles
      .filter(article => article && (article.id || article.text_id)) // 过滤掉无效的文章
      .map(article => {
        const fallbackLabel = `${t('文章')} ${article.id || article.text_id}`
        return {
          value: String(article.id || article.text_id),
          label: article.title || article.text_title || fallbackLabel
        }
      })
  ]
  
  console.log('🔍 [GrammarDemo] 文章选项:', articleOptions.length, '个', articleOptions.map(opt => opt.label))
  
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

  // 加载状态
  if (isLoading) {
    return (
      <LearnPageLayout
        title=""
        onStartReview={startReview}
        onSearch={(value) => setFilterText(value)}
        onFilterChange={handleFilterChange}
        filters={filters}
        showFilters={true}
        showSearch={false}
        backgroundClass="bg-white"
        onRefresh={handleRefreshData}
        showRefreshButton={false}
        sortOrder={sortOrder}
        onSortChange={setSortOrder}
      >
        <div className="col-span-full flex justify-center items-center h-32">
          <div className="text-gray-500">{t('加载语法数据中...')}</div>
        </div>
      </LearnPageLayout>
    )
  }

  // 错误状态
  if (isError) {
    return (
      <LearnPageLayout
        title=""
        onStartReview={startReview}
        onSearch={(value) => setFilterText(value)}
        onFilterChange={handleFilterChange}
        filters={filters}
        showFilters={true}
        showSearch={false}
        backgroundClass="bg-white"
        onRefresh={handleRefreshData}
        showRefreshButton={false}
        sortOrder={sortOrder}
        onSortChange={setSortOrder}
      >
        <div className="col-span-full flex justify-center items-center h-32">
          <div className="text-red-500">{t('加载语法数据失败')}: {error?.message}</div>
        </div>
      </LearnPageLayout>
    )
  }

  // 列表页：使用统一布局
  return (
    <LearnPageLayout
      title=""
      onStartReview={startReview}
      onSearch={(value) => setFilterText(value)}
      onFilterChange={handleFilterChange}
      filters={filters}
      showFilters={true}
      showSearch={false}
      backgroundClass="bg-white"
      onRefresh={handleRefreshData}
      showRefreshButton={false}
      sortOrder={sortOrder}
      onSortChange={setSortOrder}
    >
      {/* 空状态提示 */}
      {list.length === 0 && !isLoading && (
        <div className="col-span-full flex justify-center items-center h-32">
          <div className="text-gray-500">{t('没有找到语法规则')}</div>
        </div>
      )}
      
      {list.map((g) => (
        <LearnCard 
          key={g.rule_id} 
          type="grammar" 
          data={g} 
          onClick={() => {
            setSelectedGrammarId(g.rule_id)
            // 计算当前语法在列表中的索引
            const index = list.findIndex(item => item.rule_id === g.rule_id)
            setSelectedGrammarIndex(index)
          }}
          onToggleStar={handleToggleStar}
        />
      ))}
    </LearnPageLayout>
  )
}

export default GrammarDemo
