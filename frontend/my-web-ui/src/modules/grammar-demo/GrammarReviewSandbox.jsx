import { useState, useEffect } from 'react'
import LearnPageLayout from '../shared/components/LearnPageLayout'
import LearnCard from '../shared/components/LearnCard'
// 注意：Sandbox 允许你自由重构，这里保留最小依赖，避免影响正式 GrammarDemo
import GrammarDetailCard from '../../components/features/grammar/GrammarDetailCard'
import { BaseCard } from '../../components/base'
import { useGrammarList, useToggleGrammarStar, useRefreshData, useArticles } from '../../hooks/useApi'
import { apiService } from '../../services/api'
import { useUser } from '../../contexts/UserContext'
import { useLanguage } from '../../contexts/LanguageContext'
import { useUIText } from '../../i18n/useUIText'

/**
 * 临时 Sandbox 页面：用于“重新设计语法复习页面”。
 *
 * 说明：
 * - 这是从 `GrammarDemo.jsx` 原样复制出来的一份独立实现，方便后续随意改动/重构。
 * - 访问方式：`/?page=grammarReviewSandbox`
 * - 你可以在这里做大改，而不影响正式入口 `/?page=grammarDemo`
 */
const GrammarReviewSandbox = () => {
  // 从 UserContext 获取当前用户
  const { userId, isGuest, isAuthenticated } = useUser()

  // 从 LanguageContext 获取选择的语言
  const { selectedLanguage } = useLanguage()
  const t = useUIText()

  // 文章过滤
  const [textId, setTextId] = useState('all')

  // 时间排序：'desc' 倒序（最新在前），'asc' 正序（最早在前）
  const [sortOrder, setSortOrder] = useState('desc')

  // 获取文章列表（使用 useArticles hook，它会处理响应格式）
  const { data: articlesResponse, isLoading: articlesLoading } = useArticles(userId, selectedLanguage, isGuest)

  console.log('🔍 [GrammarReviewSandbox] useArticles 返回:', articlesResponse, 'loading:', articlesLoading)

  // 处理文章数据：提取数组并按字母顺序排序
  const articlesData = (() => {
    if (!articlesResponse) {
      console.log('⚠️ [GrammarReviewSandbox] articlesResponse 为空')
      return []
    }

    console.log('🔍 [GrammarReviewSandbox] articlesResponse 类型:', typeof articlesResponse)
    console.log('🔍 [GrammarReviewSandbox] articlesResponse.data 类型:', typeof articlesResponse?.data)
    console.log('🔍 [GrammarReviewSandbox] articlesResponse.data 是否为数组:', Array.isArray(articlesResponse?.data))

    // useArticles 返回的格式：响应拦截器处理后是 { data: [...], count: ... }
    let articles = []
    if (Array.isArray(articlesResponse?.data)) {
      articles = articlesResponse.data
      console.log('🔍 [GrammarReviewSandbox] 从 articlesResponse.data 提取:', articles.length, '篇')
    } else if (Array.isArray(articlesResponse)) {
      articles = articlesResponse
      console.log('🔍 [GrammarReviewSandbox] articlesResponse 直接是数组:', articles.length, '篇')
    } else {
      console.warn('⚠️ [GrammarReviewSandbox] 无法识别的 articlesResponse 格式:', articlesResponse)
    }

    // 按标题字母顺序排序
    if (articles.length > 0) {
      const sorted = articles.sort((a, b) => {
        const titleA = (a.title || a.text_title || '').toLowerCase()
        const titleB = (b.title || b.text_title || '').toLowerCase()
        return titleA.localeCompare(titleB)
      })
      console.log('🔍 [GrammarReviewSandbox] 排序后的文章:', sorted.length, '篇')
      return sorted
    }
    console.log('⚠️ [GrammarReviewSandbox] 文章列表为空')
    return []
  })()

  console.log(
    '🔍 [GrammarReviewSandbox] 最终文章数据:',
    articlesData.length,
    '篇',
    articlesData.length > 0 ? articlesData[0] : '',
  )

  // 使用API获取语法数据 - 传入 userId、isGuest、language、learnStatus 和 textId
  const { data: grammarData, isLoading, isError, error } = useGrammarList(
    userId,
    isGuest,
    selectedLanguage,
    null,
    textId,
  )
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
  const filteredGrammar = allGrammar.filter((g) =>
    filterText ? (g.rule_name || g.name || '').toLowerCase().includes(filterText.toLowerCase()) : true,
  )

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
  const [reviewItems, setReviewItems] = useState([]) // ReviewExample[]
  const [currentIndex, setCurrentIndex] = useState(0) // index in reviewItems
  const [showExplanations, setShowExplanations] = useState(false)
  // 🔧 缓存预加载的语法详情
  const [grammarDetailCache, setGrammarDetailCache] = useState(new Map())

  // 🔧 从 URL 参数初始化 selectedGrammarId（用于新标签页打开）
  // 🔧 修复问题1：只在URL中明确包含grammarId时才设置（用于新标签页打开），而不是每次组件挂载都设置
  useEffect(() => {
    const urlGrammarId = getGrammarIdFromURL()
    // 🔧 如果URL中有grammarId，说明是从新标签页打开，应该显示详情页
    // 如果URL中没有grammarId，但selectedGrammarId有值，说明是用户点击了列表项，保持当前状态
    if (urlGrammarId && urlGrammarId !== selectedGrammarId) {
      console.log(`🔍 [GrammarReviewSandbox] URL中有grammarId=${urlGrammarId}，设置详情页`)
      setSelectedGrammarId(urlGrammarId)
      // 计算当前语法在列表中的索引（等待 allGrammar 加载完成）
      if (allGrammar.length > 0) {
        const index = allGrammar.findIndex((g) => g.rule_id === urlGrammarId)
        if (index >= 0) {
          setSelectedGrammarIndex(index)
        }
      }
    } else if (!urlGrammarId && selectedGrammarId) {
      // 🔧 如果URL中没有grammarId，但selectedGrammarId有值，说明用户点击了导航栏的"语法"按钮
      // 应该清除selectedGrammarId，显示列表页
      console.log(`🔍 [GrammarReviewSandbox] URL中没有grammarId，清除selectedGrammarId，显示列表页`)
      setSelectedGrammarId(null)
      setSelectedGrammarIndex(-1)
      setSelectedGrammar(null)
    }
  }, []) // 只在组件挂载时执行一次

  // 🔧 当 allGrammar 加载完成后，如果 URL 中有 grammarId，设置索引
  useEffect(() => {
    const urlGrammarId = getGrammarIdFromURL()
    if (urlGrammarId && allGrammar.length > 0 && selectedGrammarIndex === -1) {
      const index = allGrammar.findIndex((g) => g.rule_id === urlGrammarId)
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
        console.log(`✅ [GrammarReviewSandbox] 使用缓存的语法详情: ${selectedGrammarId}`)
        setSelectedGrammar(cached)
        setIsLoadingDetail(false)
        setShowLoadingUI(false)
        setPreviousGrammar(cached)
        return
      }

      // 🔧 如果缓存中没有，先尝试从列表数据中获取
      const listItem = allGrammar.find((g) => g.rule_id === selectedGrammarId)
      if (listItem && listItem.examples && Array.isArray(listItem.examples) && listItem.examples.length > 0) {
        // 列表数据中已有完整数据，直接使用并缓存
        setSelectedGrammar(listItem)
        setIsLoadingDetail(false)
        setShowLoadingUI(false)
        setPreviousGrammar(listItem)
        setDetailPageCache((prev) => new Map(prev).set(selectedGrammarId, listItem))
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

      console.log(`🔍 [GrammarReviewSandbox] Fetching grammar detail for ID: ${selectedGrammarId}`)

      // 先从列表中找到对应的语法规则作为后备
      if (listItem) {
        setPreviousGrammar(listItem)
      }

      apiService
        .getGrammarById(selectedGrammarId)
        .then((response) => {
          console.log(`✅ [GrammarReviewSandbox] Grammar detail fetched:`, response)
          // 处理API响应格式：后端返回 { success: true, data: {...} }
          const grammarData = response?.data?.data || response?.data || response
          if (grammarData) {
            setSelectedGrammar(grammarData)
            setPreviousGrammar(grammarData)
            // 🔧 缓存数据
            setDetailPageCache((prev) => new Map(prev).set(selectedGrammarId, grammarData))
          } else if (listItem) {
            // 如果 API 返回的数据格式不对，使用列表中的数据
            console.warn(`⚠️ [GrammarReviewSandbox] API response format unexpected, using list data`)
            setSelectedGrammar(listItem)
            setPreviousGrammar(listItem)
            setDetailPageCache((prev) => new Map(prev).set(selectedGrammarId, listItem))
          }
          setIsLoadingDetail(false)
          setShowLoadingUI(false)
          clearTimeout(loadingUITimer)
        })
        .catch((error) => {
          console.error(`❌ [GrammarReviewSandbox] Error fetching grammar detail:`, error)
          // 如果 API 失败，使用列表中的数据
          if (listItem) {
            console.log(`🔄 [GrammarReviewSandbox] Using list data as fallback`)
            setSelectedGrammar(listItem)
            setPreviousGrammar(listItem)
            setDetailPageCache((prev) => new Map(prev).set(selectedGrammarId, listItem))
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

  /**
   * ReviewExample 数据（UI 层构建）：
   * - 句子（sentence）
   * - 知识点名称（ruleName）
   * - 句子语法解读（exampleExplanation = explanation_context）
   * - 语法知识点解读（grammarExplanation = rule_summary）
   *
   * 注意：按“句子”为单位展示；若同一句子有多个知识点，会在同一句子下依次出现（通过展开后的队列实现）。
   */
  const buildReviewExamples = async ({ sortedRules }) => {
    const concurrency = 4
    const flatItems = []

    for (let i = 0; i < sortedRules.length; i += concurrency) {
      const batch = sortedRules.slice(i, i + concurrency)
      const batchDetails = await Promise.all(
        batch.map(async (rule) => {
          try {
            const resp = await apiService.getGrammarById(rule.rule_id)
            return resp?.data?.data || resp?.data || resp
          } catch (e) {
            console.warn('⚠️ [GrammarReviewSandbox] 获取语法详情失败:', rule?.rule_id, e)
            return null
          }
        }),
      )

      batchDetails.forEach((detail) => {
        if (!detail) return
        const ruleId = detail.rule_id
        const ruleName = detail.rule_name || detail.name || ''
        const grammarExplanation = detail.rule_summary || detail.explanation || ''
        const examples = Array.isArray(detail.examples) ? detail.examples : []
        examples.forEach((ex) => {
          const sentence = ex?.original_sentence
          if (!sentence || !String(sentence).trim()) return
          flatItems.push({
            sentenceKey: `${ex?.text_id ?? ''}-${ex?.sentence_id ?? ''}`,
            textId: ex?.text_id ?? null,
            sentenceId: ex?.sentence_id ?? null,
            sentence: String(sentence),
            ruleId,
            ruleName,
            exampleExplanation: ex?.explanation_context || '',
            grammarExplanation,
          })
        })
      })
    }

    // 句子优先：按 sentenceKey 分组，构建 { sentence, entries: [...] }
    const order = []
    const grouped = new Map()
    flatItems.forEach((item) => {
      const key = item.sentenceKey || item.sentence
      if (!grouped.has(key)) {
        grouped.set(key, {
          sentenceKey: key,
          textId: item.textId,
          sentenceId: item.sentenceId,
          sentence: item.sentence,
          entries: [],
        })
        order.push(key)
      }
      grouped.get(key).entries.push({
        ruleId: item.ruleId,
        ruleName: item.ruleName,
        exampleExplanation: item.exampleExplanation,
        grammarExplanation: item.grammarExplanation,
      })
    })
    return order.map((key) => grouped.get(key)).filter(Boolean)
  }

  const startReview = async () => {
    // 以当前过滤/排序后的语法规则为集合，构建「句子 + 知识点」队列
    const allGrammar = grammarData?.data || []
    const filteredGrammarRules = allGrammar.filter((g) =>
      filterText ? (g.rule_name || g.name || '').toLowerCase().includes(filterText.toLowerCase()) : true,
    )

    // 按时间排序（保持与原 GrammarDemo 一致）
    const sortedRules = [...filteredGrammarRules].sort((a, b) => {
      const timeA = a.updated_at || a.created_at
      const timeB = b.updated_at || b.created_at
      if (timeA && timeB) {
        const dateA = new Date(timeA).getTime()
        const dateB = new Date(timeB).getTime()
        return sortOrder === 'desc' ? dateB - dateA : dateA - dateB
      }
      const idA = a.rule_id || 0
      const idB = b.rule_id || 0
      return sortOrder === 'desc' ? idB - idA : idA - idB
    })

    if (sortedRules.length === 0) {
      window.confirm(t('当前筛选条件下没有语法规则，请更改筛选选项后再试'))
      return
    }

    setIsReviewMode(true)
    setCurrentIndex(0)
    setShowExplanations(false)

    const reviewExamples = await buildReviewExamples({ sortedRules })
    if (reviewExamples.length === 0) {
      window.confirm(t('当前筛选条件下没有语法规则，请更改筛选选项后再试'))
      setIsReviewMode(false)
      return
    }

    setReviewItems(reviewExamples)
  }

  const handleNext = () => {
    setShowExplanations(false)
    if (currentIndex < reviewItems.length - 1) {
      setCurrentIndex((v) => {
        const next = v + 1
        return next < reviewItems.length ? next : v
      })
    } else {
      setIsReviewMode(false)
    }
  }

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((v) => v - 1)
    }
  }

  const handleFilterChange = (filterId, value) => {
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
      const item = reviewItems[currentIndex]
      const progressPct = reviewItems.length > 0 ? Math.round(((currentIndex + 1) / reviewItems.length) * 100) : 0

      const handleShowExplanations = () => {
        setShowExplanations(true)
      }

      return (
        <div className="h-full bg-white p-8">
          <div className="max-w-6xl mx-auto">
            <BaseCard padding="lg" className="w-full max-w-2xl mx-auto">
              <div className="space-y-6">
                {/* 顶部导航 + 进度（对齐 vocab review） */}
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setIsReviewMode(false)}
                    className="p-1 rounded hover:bg-gray-100 transition-colors"
                    aria-label="Close"
                  >
                    <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>

                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-300 bg-emerald-400" style={{ width: `${progressPct}%` }} />
                  </div>

                  <span className="text-sm text-gray-600 whitespace-nowrap">
                    {currentIndex + 1}/{reviewItems.length}
                  </span>

                  <div className="flex items-center gap-1">
                    {currentIndex > 0 && (
                      <button
                        type="button"
                        onClick={() => {
                          setShowExplanations(false)
                          setCurrentIndex((v) => (v > 0 ? v - 1 : v))
                        }}
                        className="p-1 rounded hover:bg-gray-100 transition-colors"
                        aria-label="Previous"
                      >
                        <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </button>
                    )}
                    {currentIndex < reviewItems.length - 1 && (
                      <button
                        type="button"
                        onClick={() => {
                          setShowExplanations(false)
                          setCurrentIndex((v) => (v < reviewItems.length - 1 ? v + 1 : v))
                        }}
                        className="p-1 rounded hover:bg-gray-100 transition-colors"
                        aria-label="Next"
                      >
                        <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>

                {/* 句子区域 */}
                <div className="bg-white rounded-lg p-4 border border-gray-200">
                  <div className="flex flex-col items-center gap-4">
                    <div className="text-center text-xl font-normal leading-relaxed text-gray-900">
                      {item.sentence}
                    </div>

                    {Array.isArray(item.entries) && item.entries.length > 0 && (
                      <div className="flex flex-wrap justify-center gap-2">
                        {item.entries.map((entry, idx) => (
                          <span
                            key={`${entry.ruleId || entry.ruleName || idx}`}
                            className="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs text-emerald-700"
                          >
                            {entry.ruleName}
                          </span>
                        ))}
                      </div>
                    )}

                    {showExplanations && (
                      <>
                        <div className="h-px w-full bg-gray-200" />
                        <div className="w-full space-y-3">
                          {Array.isArray(item.entries) &&
                            item.entries.map((entry, idx) => (
                              <div key={`exp-${entry.ruleId || idx}`}>
                                <button
                                  type="button"
                                  className="mb-1 inline text-left text-sm font-medium text-emerald-700 underline decoration-emerald-300 decoration-2 underline-offset-4 hover:text-emerald-800"
                                  onClick={() => {
                                    if (entry.ruleId) {
                                      const currentParams = new URLSearchParams(window.location.search)
                                      const detailParams = new URLSearchParams()
                                      const apiParam = currentParams.get('api')
                                      if (apiParam) {
                                        detailParams.set('api', apiParam)
                                      }
                                      detailParams.set('page', 'grammarDemo')
                                      detailParams.set('grammarId', String(entry.ruleId))
                                      const detailUrl = `${window.location.origin}${window.location.pathname}?${detailParams.toString()}`
                                      window.open(detailUrl, '_blank', 'noopener,noreferrer')
                                    }
                                  }}
                                >
                                  {entry.ruleName}
                                </button>
                                <div className="whitespace-pre-wrap text-sm text-gray-700">
                                  {entry.exampleExplanation || t('暂无记录') || '暂无记录'}
                                </div>
                              </div>
                            ))}
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* 底部操作 */}
                <div className="flex justify-center">
                  {!showExplanations ? (
                    <button
                      type="button"
                      onClick={handleShowExplanations}
                      className="h-14 w-1/2 rounded-2xl border border-gray-200 bg-gray-100 text-lg font-semibold text-gray-800 hover:bg-gray-200"
                    >
                      {t('查看例句解释') || '查看例句解释'}
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleNext}
                      className="h-14 w-1/2 rounded-2xl bg-emerald-400 text-lg font-semibold text-white hover:bg-emerald-500"
                    >
                      {t('下一个') || '下一个'}
                    </button>
                  )}
                </div>
              </div>
            </BaseCard>
          </div>
        </div>
      )
    }
    return null
  }

  // 详情页
  if (selectedGrammarId) {
    // 计算当前过滤和排序后的列表
    const allGrammar = grammarData?.data || []
    const filteredGrammar = allGrammar.filter((g) =>
      filterText ? (g.rule_name || g.name || '').toLowerCase().includes(filterText.toLowerCase()) : true,
    )

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
    const currentIndex = sortedList.findIndex((g) => g.rule_id === selectedGrammarId)

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
    const shouldShowLoading =
      isLoadingDetail && !detailPageCache.has(selectedGrammarId) && (showLoadingUI || !previousGrammar)

    return (
      <div className="h-full bg-white p-8" style={{ backgroundColor: 'white', minHeight: '100%' }}>
        <div className="max-w-6xl mx-auto">
          <GrammarDetailCard
            grammar={displayGrammar}
            loading={shouldShowLoading}
            onPrevious={currentIndex > 0 ? handlePreviousGrammar : null}
            onNext={currentIndex < sortedList.length - 1 ? handleNextGrammar : null}
            onBack={() => {
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
  console.log('🔍 [GrammarReviewSandbox] 文章数据:', articles.length, '篇', articles.length > 0 ? articles[0] : '')

  const articleOptions = [
    { value: 'all', label: t('全部文章') },
    ...articles
      .filter((article) => article && (article.id || article.text_id)) // 过滤掉无效的文章
      .map((article) => {
        const fallbackLabel = `${t('文章')} ${article.id || article.text_id}`
        return {
          value: String(article.id || article.text_id),
          label: article.title || article.text_title || fallbackLabel,
        }
      }),
  ]

  console.log('🔍 [GrammarReviewSandbox] 文章选项:', articleOptions.length, '个', articleOptions.map((opt) => opt.label))

  const filters = [
    {
      id: 'text_id',
      label: t('文章'),
      options: articleOptions,
      placeholder: t('选择文章'),
      value: textId,
    },
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
          <div className="text-red-500">
            {t('加载语法数据失败')}: {error?.message}
          </div>
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
            const index = list.findIndex((item) => item.rule_id === g.rule_id)
            setSelectedGrammarIndex(index)
          }}
          onToggleStar={handleToggleStar}
        />
      ))}
    </LearnPageLayout>
  )
}

export default GrammarReviewSandbox

