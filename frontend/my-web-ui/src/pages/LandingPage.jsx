import { useMemo } from 'react'
import { useUser } from '../contexts/UserContext'
import { useLanguage } from '../contexts/LanguageContext'
import { useArticles, useVocabList, useGrammarList } from '../hooks/useApi'
import { useUIText } from '../i18n/useUIText'
import ArticlePreviewCardLanding from '../components/features/article/ArticlePreviewCardLanding'
import QuickReviewCard from '../components/features/review/QuickReviewCard'

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
}) => {
  const { userId, isGuest, isAuthenticated } = useUser()
  const { selectedLanguage } = useLanguage()
  const t = useUIText()

  const effectiveUserId = isAuthenticated ? userId : null

  const { data: articleResponse } = useArticles(effectiveUserId, selectedLanguage, isGuest)
  const { data: vocabResponse } = useVocabList(effectiveUserId, isGuest, selectedLanguage)
  const { data: grammarResponse } = useGrammarList(effectiveUserId, isGuest, selectedLanguage)

  const articles = useMemo(() => {
    if (!isAuthenticated) {
      return []
    }
    const normalized = extractArray(articleResponse)
    return normalized.map((article) => normalizeArticle(article, t('暂无摘要')))
  }, [articleResponse, isAuthenticated, t])

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

  if (!isAuthenticated) {
    return <div className="min-h-[calc(100vh-64px)] bg-white" />
  }

  const hasArticles = articles.length > 0
  const vocabCount = vocabList.length
  const grammarCount = grammarList.length
  const noReviewData = vocabCount === 0 && grammarCount === 0
  const hideContent = !hasArticles || noReviewData

  const recentArticles = articles.slice(0, 3)

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

