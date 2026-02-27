import { useMemo } from 'react'
import { useLanguage, languageNameToCode } from '../contexts/LanguageContext'
import { useUIText } from '../i18n/useUIText'
import { BaseBadge } from '../components/base'
import { colors } from '../design-tokens'

const difficultyMeta = {
  beginner: {
    label: '初级',
    badgeVariant: 'success',
  },
  intermediate: {
    label: '中级',
    badgeVariant: 'warning',
  },
  advanced: {
    label: '高级',
    badgeVariant: 'danger',
  },
}

const PRESET_ARTICLES = {
  zh: [
    {
      id: 'little-prince',
      difficulty: 'beginner',
      title: 'The Little Prince',
      preview: 'Once when I was six years old I saw a magnificent picture...',
    },
    {
      id: 'climate-change',
      difficulty: 'intermediate',
      title: 'Climate Change Today',
      preview: 'Climate change is one of the most pressing challenges...',
    },
    {
      id: 'quantum-computing',
      difficulty: 'advanced',
      title: 'Quantum Computing Explained',
      preview: 'Quantum computing harnesses the phenomena of quantum mechanics...',
    },
  ],
  en: [
    {
      id: 'little-prince-en',
      difficulty: 'beginner',
      title: 'Der Kleine Prinz',
      preview: 'Als ich sechs Jahre alt war, sah ich einmal ein prächtiges Bild...',
    },
    {
      id: 'climate-change-en',
      difficulty: 'intermediate',
      title: 'Klimawandel Heute',
      preview: 'Der Klimawandel ist eine der drängendsten Herausforderungen...',
    },
    {
      id: 'quantum-computing-en',
      difficulty: 'advanced',
      title: 'Quantencomputing erklärt',
      preview: 'Quantencomputer nutzen die Phänomene der Quantenmechanik...',
    },
  ],
  de: [
    {
      id: 'little-prince-de',
      difficulty: 'beginner',
      title: 'The Little Prince',
      preview: 'Once when I was six years old I saw a magnificent picture...',
    },
    {
      id: 'climate-change-de',
      difficulty: 'intermediate',
      title: 'Climate Change Today',
      preview: 'Climate change is one of the most pressing challenges...',
    },
    {
      id: 'quantum-computing-de',
      difficulty: 'advanced',
      title: 'Quantum Computing Explained',
      preview: 'Quantum computing harnesses the phenomena of quantum mechanics...',
    },
  ],
}

const OnboardingReadingIntro = ({ onStartReading, onUploadOwn }) => {
  const t = useUIText()
  const { selectedLanguage } = useLanguage()

  const langCode = useMemo(
    () => languageNameToCode(selectedLanguage),
    [selectedLanguage],
  )

  const presets = PRESET_ARTICLES[langCode] || PRESET_ARTICLES.de

  const handlePresetClick = () => {
    if (onStartReading) {
      onStartReading()
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
          {presets.map((article) => {
            const meta = difficultyMeta[article.difficulty]
            return (
              <button
                key={article.id}
                type="button"
                onClick={handlePresetClick}
                className="w-full text-left rounded-xl border border-gray-200 bg-white px-4 py-4 sm:px-5 sm:py-5 hover:border-primary-200 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-2">
                    {meta && (
                      <BaseBadge
                        variant={meta.badgeVariant}
                        size="sm"
                      >
                        {meta.label}
                      </BaseBadge>
                    )}
                    <h2 className="text-base sm:text-lg font-semibold text-gray-900">
                      {article.title}
                    </h2>
                    <p className="text-sm text-gray-500 line-clamp-2">
                      {article.preview}
                    </p>
                  </div>
                </div>
              </button>
            )
          })}
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

