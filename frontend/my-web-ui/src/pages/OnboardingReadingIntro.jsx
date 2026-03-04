import { useMemo } from 'react'
import { useLanguage } from '../contexts/LanguageContext'
import { useUser } from '../contexts/UserContext'
import { useArticles } from '../hooks/useApi'
import { useUIText } from '../i18n/useUIText'
import { BaseBadge } from '../components/base'
import { colors } from '../design-tokens'

const OnboardingReadingIntro = ({ onStartReading, onUploadOwn }) => {
  const t = useUIText()
  const { selectedLanguage } = useLanguage()
  const { userId, isGuest } = useUser()

  // 使用真实的文章列表（已根据 onboarding 选择的语言导入预置文章）
  const { data, isLoading } = useArticles(userId, selectedLanguage, isGuest)

  const articles = useMemo(() => {
    if (!data) return []
    // 兼容多种返回格式（与 ArticleSelection 中的逻辑一致的精简版）
    if (Array.isArray(data)) return data
    if (Array.isArray(data.data)) return data.data
    if (data?.data && Array.isArray(data.data.texts)) return data.data.texts
    if (Array.isArray(data.texts)) return data.texts
    return []
  }, [data])

  // 只展示前 3 篇，作为推荐阅读入口
  const presets = useMemo(
    () =>
      articles.slice(0, 3).map((a) => {
        const id = a.text_id || a.article_id || a.id
        const title = a.text_title || a.title || `Article ${id}`
        const preview =
          a.preview_text ||
          a.preview ||
          a.summary ||
          a.description ||
          a.snippet ||
          a.first_sentence ||
          ''
        return {
          id,
          title,
          preview,
        }
      }),
    [articles],
  )

  const handlePresetClick = (articleId) => {
    if (onStartReading && articleId) {
      onStartReading(articleId)
    }
  }

  const handleUploadClick = () => {
    if (onUploadOwn) {
      onUploadOwn()
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl border border-gray-200 shadow-sm px-6 py-8 sm:px-8 sm:py-10">
        <div className="text-center space-y-2">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            {t('开始阅读吧！')}
          </h1>
          <p className="text-sm sm:text-base text-gray-500">
            {t('选择一篇文章开始学习，或上传你自己的文章')}
          </p>
        </div>

        <div className="mt-8 space-y-3">
          {isLoading && presets.length === 0 && (
            <div className="text-sm text-gray-500">{t('加载中...') || '加载中...'}</div>
          )}
          {!isLoading && presets.length === 0 && (
            <div className="text-sm text-gray-500">{t('暂时没有可用的文章，请稍后在阅读页中查看。') || '暂时没有可用的文章，请稍后在阅读页中查看。'}</div>
          )}
          {presets.map((article) => (
            <button
              key={article.id}
              type="button"
              onClick={() => handlePresetClick(article.id)}
              className="w-full text-left rounded-xl border border-gray-200 bg-white px-4 py-4 sm:px-5 sm:py-5 hover:border-primary-200 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-2">
                  <h2 className="text-base sm:text-lg font-semibold text-gray-900">
                    {article.title}
                  </h2>
                  {article.preview && (
                    <p className="text-sm text-gray-500 line-clamp-2">
                      {article.preview}
                    </p>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-8">
          <button
            type="button"
            onClick={handleUploadClick}
            className="w-full flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 px-4 py-6 text-sm sm:text-base text-gray-600 hover:border-primary-300 hover:bg-primary-50 transition-colors"
          >
            <div
              className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-full"
              style={{ backgroundColor: colors.primary[50], color: colors.primary[600] }}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M16 12l-4-4m0 0l-4 4m4-4v12"
                />
              </svg>
            </div>
            <span className="font-medium">{t('上传自己的文章')}</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default OnboardingReadingIntro

