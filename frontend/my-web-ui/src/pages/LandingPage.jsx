import { useMemo, useState, useEffect, useRef } from 'react'
import { useUser } from '../contexts/UserContext'
import { useLanguage } from '../contexts/LanguageContext'
import { useUiLanguage } from '../contexts/UiLanguageContext'
import { useArticles, useVocabList, useGrammarList } from '../hooks/useApi'
import { useUIText } from '../i18n/useUIText'
import { apiService } from '../services/api'
import { colors, radius, shadow, transition } from '../design-tokens'
import ArticlePreviewCardLanding from '../components/features/article/ArticlePreviewCardLanding'
import QuickReviewCard from '../components/features/review/QuickReviewCard'

const PREVIEW_CACHE_KEY = 'articlePreviewCache'
const previewCache = new Map()
let previewCacheLoaded = false

const ensurePreviewCacheLoaded = () => {
  if (previewCacheLoaded || typeof window === 'undefined') {
    return
  }
  try {
    const raw = window.localStorage.getItem(PREVIEW_CACHE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      Object.entries(parsed).forEach(([id, value]) => {
        if (typeof value === 'string' && value.trim()) {
          previewCache.set(id, value)
        }
      })
    }
  } catch (err) {
    console.warn('⚠️ [LandingPage] 读取摘要缓存失败:', err)
  } finally {
    previewCacheLoaded = true
  }
}

const persistPreviewCache = () => {
  if (typeof window === 'undefined') {
    return
  }
  try {
    const serialized = JSON.stringify(Object.fromEntries(previewCache))
    window.localStorage.setItem(PREVIEW_CACHE_KEY, serialized)
  } catch (err) {
    console.warn('⚠️ [LandingPage] 保存摘要缓存失败:', err)
  }
}

const extractArray = (response) => {
  if (!response) {
    return []
  }
  if (Array.isArray(response)) {
    return response
  }
  if (Array.isArray(response.data)) {
    return response.data
  }
  if (Array.isArray(response.texts)) {
    return response.texts
  }
  if (response.data && Array.isArray(response.data.texts)) {
    return response.data.texts
  }
  return []
}

const normalizeArticle = (article, fallbackPreview) => {
  const textId = article.text_id || article.article_id || article.id
  const textTitle = article.text_title || article.title || `Article ${textId}`
  const wordCount = article.total_tokens || article.wordCount || article.token_count || 0
  const noteCount =
    article.note_count ??
    article.notes_count ??
    article.total_notes ??
    article.grammar_notes_count ??
    article.vocab_notes_count ??
    0
  const preview =
    article.preview_text ||
    article.preview ||
    article.summary ||
    article.description ||
    article.snippet ||
    article.first_sentence ||
    fallbackPreview

  return {
    id: textId,
    title: textTitle,
    wordCount,
    noteCount,
    preview,
  }
}

const LandingPage = ({
  onArticleSelect,
  onNavigateToArticles,
  onStartVocabReview,
  onStartGrammarReview,
  onRegister,
}) => {
  const { userId, isGuest, isAuthenticated } = useUser()
  const { selectedLanguage } = useLanguage()
  const { uiLanguage, setUiLanguage } = useUiLanguage()
  const t = useUIText()
  const featureStepRefs = useRef([])
  const [visibleFeatureSteps, setVisibleFeatureSteps] = useState({})

  const effectiveUserId = isAuthenticated ? userId : null

  const { data: articleResponse } = useArticles(effectiveUserId, selectedLanguage, isGuest)
  const { data: vocabResponse } = useVocabList(effectiveUserId, isGuest, selectedLanguage)
  const { data: grammarResponse } = useGrammarList(effectiveUserId, isGuest, selectedLanguage)

  const fallbackPreview = t('暂无摘要')
  
  ensurePreviewCacheLoaded()

  const articles = useMemo(() => {
    if (!isAuthenticated) {
      return []
    }
    const normalized = extractArray(articleResponse)
    return normalized.map((article) => {
      const normalized = normalizeArticle(article, fallbackPreview)
      // 如果缓存中有预览，使用缓存的预览
      const cachedPreview = previewCache.get(normalized.id)
      return {
        ...normalized,
        preview: cachedPreview || normalized.preview,
      }
    })
  }, [articleResponse, isAuthenticated, t, fallbackPreview])

  const [previewOverrides, setPreviewOverrides] = useState(() => {
    const initial = {}
    articles.forEach((article) => {
      if (previewCache.has(article.id)) {
        initial[article.id] = previewCache.get(article.id)
      }
    })
    return initial
  })

  // 异步加载缺失的预览
  useEffect(() => {
    let cancelled = false
    const CONCURRENCY = 3
    
    const fetchMissingPreviews = async () => {
      const pending = articles.filter(
        (article) =>
          (!article.preview || article.preview === fallbackPreview) &&
          !previewCache.has(article.id),
      )
      if (pending.length === 0) {
        return
      }

      for (let i = 0; i < pending.length && !cancelled; i += CONCURRENCY) {
        const batch = pending.slice(i, i + CONCURRENCY)
        await Promise.all(
          batch.map(async (article) => {
            try {
              const resp = await apiService.getArticleSentences(article.id, { limit: 1 })
              const sentences =
                resp?.data?.data?.sentences ||
                resp?.data?.sentences ||
                resp?.data ||
                resp?.sentences ||
                []
              const firstSentence = Array.isArray(sentences) && sentences.length > 0
                ? sentences[0]?.sentence_body || sentences[0]?.text || sentences[0]?.sentence
                : null
              if (firstSentence && !cancelled) {
                previewCache.set(article.id, firstSentence)
                persistPreviewCache()
                setPreviewOverrides((prev) => {
                  if (prev[article.id] === firstSentence) {
                    return prev
                  }
                  return {
                    ...prev,
                    [article.id]: firstSentence,
                  }
                })
              }
            } catch (err) {
              console.warn('⚠️ [LandingPage] 获取文章首句失败:', article.id, err)
            }
          }),
        )
      }
    }

    fetchMissingPreviews()

    return () => {
      cancelled = true
    }
  }, [articles, fallbackPreview])

  const enrichedArticles = useMemo(
    () =>
      articles.map((article) => ({
        ...article,
        preview: previewOverrides[article.id] ?? previewCache.get(article.id) ?? article.preview,
      })),
    [articles, previewOverrides],
  )

  const vocabList = useMemo(() => {
    if (!isAuthenticated) {
      return []
    }
    return extractArray(vocabResponse)
  }, [isAuthenticated, vocabResponse])

  const grammarList = useMemo(() => {
    if (!isAuthenticated) {
      return []
    }
    return extractArray(grammarResponse)
  }, [grammarResponse, isAuthenticated])

  const featureSteps = useMemo(
    () => [
      {
        key: 'readAsk',
        number: 1,
        title: t('Read & Ask'),
        mock: 'readAsk',
      },
      {
        key: 'aiExplainsAnnotates',
        number: 2,
        title: t('AI Explains & Annotates'),
        mock: 'aiExplainsAnnotates',
      },
      {
        key: 'buildsKnowledge',
        number: 3,
        title: t('Builds Knowledge'),
        mock: 'buildsKnowledge',
      },
      {
        key: 'growsSystem',
        number: 4,
        title: t('Grows Your System'),
        mock: 'growsSystem',
      },
    ],
    [t],
  )

  useEffect(() => {
    if (isAuthenticated) return
    if (typeof window === 'undefined') return
    const nodes = featureStepRefs.current
      .map((el, idx) => ({ el, idx }))
      .filter((x) => Boolean(x.el))
    if (nodes.length === 0) return

    const observer = new IntersectionObserver(
      (entries) => {
        setVisibleFeatureSteps((prev) => {
          const next = { ...prev }
          for (const entry of entries) {
            const idx = Number(entry.target.getAttribute('data-step-index'))
            if (!Number.isFinite(idx)) continue
            next[idx] = Boolean(entry.isIntersecting && entry.intersectionRatio >= 0.35)
          }
          return next
        })
      },
      { root: null, threshold: [0, 0.2, 0.35, 0.55] },
    )

    nodes.forEach(({ el }) => observer.observe(el))
    return () => observer.disconnect()
  }, [isAuthenticated, featureSteps.length])

  if (!isAuthenticated) {
    const borderColor = colors.gray[200]
    const dashedColor = colors.gray[300]
    const containerMaxWidth = '72rem' // ~1152px, matches max-w-6xl

    const WireBox = ({ children, className, active: isActive, style }) => (
      <div
        className={className}
        style={{
          border: `1px dashed ${dashedColor}`,
          borderRadius: radius.xl,
          background: colors.semantic.bg.primary,
          opacity: isActive ? 1 : 0.2,
          transform: isActive ? 'translateY(0px)' : 'translateY(8px)',
          transition: `opacity ${transition.slow} ease, transform ${transition.slow} ease`,
          ...style,
        }}
      >
        {children}
      </div>
    )

    const DrawLine = ({ active: isActive, d, style }) => {
      const length = 400
      return (
        <svg
          viewBox="0 0 400 140"
          className="w-full h-full"
          style={{ overflow: 'visible', ...style }}
          aria-hidden="true"
        >
          <path
            d={d}
            fill="none"
            stroke={colors.gray[300]}
            strokeWidth="2"
            strokeDasharray={length}
            strokeDashoffset={isActive ? 0 : length}
            style={{
              transition: `stroke-dashoffset ${transition.slow} ease, opacity ${transition.slow} ease`,
              opacity: isActive ? 1 : 0,
            }}
          />
        </svg>
      )
    }

    // NOTE: demo sentence must stay English (not i18n).
    const SentenceLine = ({ highlight }) => (
      <div className="text-sm sm:text-base text-gray-800">
        <span className="text-gray-700">The book </span>
        <span
          className="px-1 rounded"
          style={{
            backgroundColor: colors.warning[100],
            boxShadow: `inset 0 -2px 0 ${colors.warning[300]}`,
          }}
        >
          {highlight}
        </span>{' '}
        <span className="text-gray-700">is very interesting.</span>
      </div>
    )

    const MockPanel = ({ stepKey, isActive }) => {
      const baseCard = {
        border: `1px solid ${borderColor}`,
        borderRadius: radius['2xl'],
        background: colors.semantic.bg.primary,
        boxShadow: shadow.md,
      }

      if (stepKey === 'readAsk') {
        return (
          <div style={baseCard} className="p-4 sm:p-6">
            <WireBox active={isActive} className="p-3 sm:p-4">
              <div className="h-3 w-24 rounded bg-gray-100 mb-4" />
              <SentenceLine highlight="that I bought yesterday" />
              <div className="h-3 w-64 rounded bg-gray-100 mt-4 opacity-60" />
            </WireBox>

            <div className="mt-4 rounded-xl border border-gray-200 bg-white p-3.5 sm:p-4">
              <div className="text-xs font-semibold tracking-wide text-gray-400">{t('YOUR QUESTION')}</div>
              <div className="mt-2 text-sm sm:text-base text-gray-700">
                “{t('What is the structure of this sentence?')}”
              </div>
            </div>
          </div>
        )
      }

      if (stepKey === 'aiExplainsAnnotates') {
        return (
          <div style={baseCard} className="p-4 sm:p-6">
            {/* Sentence + highlight */}
            <div className="relative">
              <WireBox active={isActive} className="p-3 sm:p-4">
                <div className="h-3 w-24 rounded bg-gray-100 mb-4" />
                <SentenceLine highlight="that I bought yesterday" />
                <div className="h-3 w-64 rounded bg-gray-100 mt-4 opacity-60" />
              </WireBox>

              {/* Inline annotation attached to sentence */}
              <div
                className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-xl border border-gray-900 bg-white px-4 py-2 text-xs font-medium"
                style={{
                  boxShadow: shadow.sm,
                  opacity: isActive ? 1 : 0,
                  transform: isActive ? 'translate(-50%, 0px)' : 'translate(-50%, 6px)',
                  transition: `opacity ${transition.slow} ease ${transition.fast}, transform ${transition.slow} ease ${transition.fast}`,
                }}
              >
                {t('Relative clause — modifies "the book"')}
              </div>
            </div>

            {/* Optional expanded explanation (fades in after annotation) */}
            <div
              className="mt-4 rounded-2xl border bg-white px-4 py-3.5"
              style={{
                borderColor: colors.gray[200],
                borderRadius: radius['2xl'],
                boxShadow: shadow.sm,
                opacity: isActive ? 1 : 0,
                transform: isActive ? 'translateY(0px)' : 'translateY(8px)',
                transition: `opacity ${transition.slow} ease ${transition.base}, transform ${transition.slow} ease ${transition.base}`,
              }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="text-xs font-semibold text-gray-400">{t('AI')}</div>
                <div className="text-xs font-semibold" style={{ color: colors.primary[600] }}>
                  {t('Annotation')}
                </div>
              </div>
              <div className="mt-2 text-sm sm:text-base text-gray-800 leading-relaxed">
                {t(
                  'This sentence contains a relative clause: "that I bought yesterday". It modifies "the book".',
                )}
              </div>
            </div>
          </div>
        )
      }

      if (stepKey === 'buildsKnowledge') {
        return (
          <div style={baseCard} className="p-4 sm:p-6">
            <div className="grid gap-4 md:grid-cols-2 md:items-center">
              <WireBox active={isActive} className="p-3 sm:p-4">
                <SentenceLine highlight="that I bought yesterday" />
              </WireBox>

              <div
                className="rounded-2xl border border-gray-200 bg-white overflow-hidden"
                style={{ boxShadow: shadow.sm, borderRadius: radius['2xl'] }}
              >
                <div className="px-5 py-4 border-b border-gray-100">
                  <div className="text-xs font-semibold tracking-wide text-gray-400">{t('KNOWLEDGE CARD')}</div>
                  <div className="mt-1 text-lg font-bold text-gray-900">{t('Relative Clause')}</div>
                </div>
                <div className="p-5 space-y-3">
                  <div className="text-sm text-gray-700">
                    <span className="font-semibold">{t('Function')}:</span> {t('modifies a noun')}
                  </div>
                  <div className="text-sm text-gray-700">
                    <span className="font-semibold">{t('Examples')}:</span>
                    <ul className="mt-2 list-disc pl-5 text-gray-600 space-y-1">
                      <li>{t('The book that I bought yesterday...')}</li>
                      <li>{t('The man who lives next door...')}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )
      }

      // growsSystem
      return (
        <div style={baseCard} className="p-4 sm:p-6">
          <div className="grid gap-4 md:grid-cols-2 md:items-center">
            <div className="relative">
              <WireBox active={isActive} className="p-6 h-[180px] sm:h-[210px]" style={{ position: 'relative' }}>
                <div
                  className="absolute top-6 left-1/2 -translate-x-1/2 rounded-full px-4 py-2 text-xs font-semibold text-white"
                  style={{ backgroundColor: colors.gray[900] }}
                >
                  {t('Relative Clause')}
                </div>
                <div className="absolute bottom-6 left-8 flex gap-6 text-xs text-gray-700">
                  {['that', 'who', 'which', 'where'].map((w) => (
                    <span
                      key={w}
                      className="rounded-full px-3 py-1 border bg-white"
                      style={{ borderColor: colors.gray[300] }}
                    >
                      {w}
                    </span>
                  ))}
                </div>
                <div className="absolute left-0 top-0 w-full h-full pointer-events-none">
                  <DrawLine
                    active={isActive}
                    d="M200 54 C 160 76, 130 86, 95 108"
                    style={{ position: 'absolute', left: 0, top: 0 }}
                  />
                  <DrawLine
                    active={isActive}
                    d="M200 54 C 180 80, 175 88, 165 108"
                    style={{ position: 'absolute', left: 0, top: 0 }}
                  />
                  <DrawLine
                    active={isActive}
                    d="M200 54 C 220 80, 230 88, 235 108"
                    style={{ position: 'absolute', left: 0, top: 0 }}
                  />
                  <DrawLine
                    active={isActive}
                    d="M200 54 C 260 76, 275 86, 300 108"
                    style={{ position: 'absolute', left: 0, top: 0 }}
                  />
                </div>
              </WireBox>
            </div>

            <div
              className="rounded-2xl border border-gray-200 bg-white overflow-hidden"
              style={{ boxShadow: shadow.sm, borderRadius: radius['2xl'] }}
            >
              <div className="px-5 py-4 border-b border-gray-100">
                <div className="text-xs font-semibold tracking-wide text-gray-400">{t('KNOWLEDGE SYSTEM')}</div>
                <div className="mt-2 text-sm font-semibold text-gray-900">{t('5 examples collected')}</div>
              </div>
              <div className="p-5">
                <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                  <li>{t('The book that I bought...')}</li>
                  <li>{t('The man who lives next door...')}</li>
                  <li>{t('The car which was parked...')}</li>
                  <li>{t('The city where I grew up...')}</li>
                </ul>
                <div className="mt-4 flex flex-wrap gap-2">
                  {['that', 'who', 'which', 'where', 'whom'].map((w) => (
                    <span
                      key={w}
                      className="text-xs rounded-md px-2 py-1 border bg-gray-50"
                      style={{ borderColor: colors.gray[200] }}
                    >
                      {w}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* removed tagline */}
        </div>
      )
    }

    return (
      <div
        className="bg-white"
        style={{
          backgroundImage: `radial-gradient(circle at 20% 0%, ${colors.primary[50]}, transparent 40%),
                            radial-gradient(circle at 90% 10%, ${colors.primary[100]}, transparent 45%)`,
        }}
      >
        {/* Hero */}
        <div className="pt-12 pb-12 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto" style={{ maxWidth: containerMaxWidth }}>
            <div className="grid gap-10 lg:grid-cols-12 lg:items-center">
              {/* Left (full-width) */}
              <div className="lg:col-span-12">
                <h1 className="mt-6 text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 leading-[1.05]">
                  {t('Learn from real content')}
                  <span className="block mt-2" style={{ color: colors.primary[600] }}>
                    {t('Turn questions into structured knowledge')}
                  </span>
                </h1>

                <p className="mt-5 text-base sm:text-lg text-gray-600 leading-relaxed max-w-3xl">
                  <span className="font-semibold text-gray-900">LinkText</span>{' '}
                  {t(
                    'helps you understand vocabulary and grammar directly from real articles — and automatically builds your personal knowledge system as you learn.',
                  )}
                </p>

                {onRegister && (
                  <div className="mt-7 flex flex-col sm:flex-row sm:items-center gap-4">
                    <button
                      onClick={onRegister}
                      className="px-9 py-3.5 text-base font-semibold text-white"
                      style={{
                        borderRadius: radius.lg,
                        backgroundColor: colors.primary[500],
                        boxShadow: shadow.sm,
                        transition: `background-color ${transition.base} ease, box-shadow ${transition.base} ease, transform ${transition.base} ease`,
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = colors.primary[600]
                        e.currentTarget.style.transform = 'translateY(-1px)'
                        e.currentTarget.style.boxShadow = shadow.md
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = colors.primary[500]
                        e.currentTarget.style.transform = 'translateY(0px)'
                        e.currentTarget.style.boxShadow = shadow.sm
                      }}
                    >
                      {t('立即注册')}
                    </button>
                    <button
                      onClick={() => setUiLanguage(uiLanguage === 'zh' ? 'en' : 'zh')}
                      className="text-sm text-gray-500 hover:text-gray-700 transition-colors underline bg-transparent border-none cursor-pointer"
                    >
                      {t('中文')} / {t('英文')}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Scroll steps */}
        <div className="px-4 sm:px-6 lg:px-8 pb-12">
          <div className="mx-auto" style={{ maxWidth: containerMaxWidth }}>
            <div className="space-y-8">
              {featureSteps.map((step, idx) => {
                const isVisible = Boolean(visibleFeatureSteps[idx])
                const isRight = idx % 2 === 1
                return (
                  <section
                    key={step.key}
                    ref={(el) => {
                      featureStepRefs.current[idx] = el
                    }}
                    data-step-index={idx}
                    className="scroll-mt-24"
                    style={{
                      opacity: isVisible ? 1 : 0.25,
                      transform: isVisible ? 'translateY(0px)' : 'translateY(14px)',
                      transition: `opacity ${transition.slow} ease, transform ${transition.slow} ease`,
                    }}
                  >
                    <div
                      style={{
                        maxWidth: '56rem',
                        marginLeft: isRight ? 'auto' : undefined,
                        marginRight: isRight ? undefined : 'auto',
                      }}
                    >
                      <div className="flex items-center gap-4 mb-4">
                        <div
                          className="shrink-0 h-9 w-9 rounded-full flex items-center justify-center text-sm font-bold"
                          style={{
                            background: isVisible ? colors.gray[900] : colors.gray[200],
                            color: isVisible ? 'white' : colors.gray[700],
                            transition: `background ${transition.base} ease, color ${transition.base} ease`,
                          }}
                        >
                          {step.number}
                        </div>
                        <div className="text-xl sm:text-2xl font-bold text-gray-900">{step.title}</div>
                      </div>

                      <MockPanel stepKey={step.key} isActive={isVisible} />
                    </div>
                  </section>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    )
  }

  const hasArticles = articles.length > 0
  const vocabCount = vocabList.length
  const grammarCount = grammarList.length
  const noReviewData = vocabCount === 0 && grammarCount === 0
  const hideContent = !hasArticles || noReviewData

  const recentArticles = enrichedArticles.slice(0, 3)

  return (
    <div className="py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-10">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{t('欢迎回来! 👋')}</h1>
          <p className="text-gray-600">{t('继续你的语言学习旅程')}</p>
        </div>

        {!hideContent && (
          <>
            {hasArticles && (
              <section className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-semibold text-gray-900">{t('最近文章')}</h2>
                    <p className="text-sm text-gray-500">
                      {t('共显示 {count} 篇文章').replace('{count}', String(articles.length))}
                    </p>
                  </div>
                  {onNavigateToArticles && (
                    <button
                      type="button"
                      onClick={onNavigateToArticles}
                      className="text-sm font-medium text-primary-600 hover:text-primary-700"
                    >
                      {t('查看全部')} →
                    </button>
                  )}
                </div>

                <div className="grid gap-6 md:grid-cols-3">
                  {recentArticles.map((article) => (
                    <ArticlePreviewCardLanding
                      key={article.id}
                      title={article.title}
                      wordCount={article.wordCount}
                      noteCount={article.noteCount}
                      preview={article.preview}
                      processingStatus="completed"
                      onRead={() => onArticleSelect?.(article.id)}
                      width="100%"
                      height="auto"
                      className="h-full"
                    />
                  ))}
                </div>
              </section>
            )}

            {!noReviewData && (
              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-gray-900">{t('快速复习')}</h2>
                <div className="grid gap-4 md:grid-cols-2">
                  {vocabCount > 0 && (
                    <QuickReviewCard
                      title={t('词汇复习')}
                      count={vocabCount}
                      description={t('复习你保存的词汇')}
                      buttonLabel={t('开始复习')}
                      onAction={onStartVocabReview}
                    />
                  )}
                  {grammarCount > 0 && (
                    <QuickReviewCard
                      title={t('语法复习')}
                      count={grammarCount}
                      description={t('练习你掌握的语法')}
                      buttonLabel={t('开始复习')}
                      onAction={onStartGrammarReview}
                    />
                  )}
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default LandingPage

