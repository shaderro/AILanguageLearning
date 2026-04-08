import { useState, useMemo } from 'react'
import { useLanguage, languageNameToCode } from '../contexts/LanguageContext'
import { useUIText } from '../i18n/useUIText'
import { colors } from '../design-tokens'
import { useUser } from '../contexts/UserContext'
import { authService } from '../modules/auth/services/authService'

const LANGUAGE_CODE_TO_NAME = {
  zh: '中文',
  en: '英文',
  de: '德文',
  es: '西班牙语',
  fr: '法语',
  ja: '日语',
  ko: '韩语',
  ar: '阿拉伯语',
  ru: '俄语',
}

const languageOptions = [
  {
    code: 'zh',
    countryCode: 'CN',
    nativeName: '中文',
  },
  {
    code: 'en',
    countryCode: 'GB',
    nativeName: 'English',
  },
  {
    code: 'es',
    countryCode: 'ES',
    nativeName: 'Español',
  },
  {
    code: 'fr',
    countryCode: 'FR',
    nativeName: 'Français',
  },
  {
    code: 'ja',
    countryCode: 'JP',
    nativeName: '日本語',
  },
  {
    code: 'ko',
    countryCode: 'KR',
    nativeName: '한국어',
  },
  {
    code: 'de',
    countryCode: 'DE',
    nativeName: 'Deutsch',
  },
  {
    code: 'ar',
    countryCode: 'AE',
    nativeName: 'العربية',
  },
  {
    code: 'ru',
    countryCode: 'RU',
    nativeName: 'Русский',
  },
]

const OnboardingLanguage = ({ onContinue }) => {
  const t = useUIText()
  const { selectedLanguage, setSelectedLanguage } = useLanguage()
  const { token } = useUser()

  const initialCode = useMemo(
    () => languageNameToCode(selectedLanguage),
    [selectedLanguage],
  )

  const [selectedCode, setSelectedCode] = useState(initialCode)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleContinue = async () => {
    if (!selectedCode || isSubmitting) return
    setIsSubmitting(true)
    const languageName = LANGUAGE_CODE_TO_NAME[selectedCode] || LANGUAGE_CODE_TO_NAME.de
    setSelectedLanguage(languageName)
    // 首次选择内容语言时，同步到后端偏好（仅在已登录且有 token 时）
    const syncPreferences = async () => {
      if (!token) return
      try {
        await authService.updatePreferences({
          content_language: selectedCode,
          languages_list: [selectedCode],
        })
      } catch (e) {
        console.warn('⚠️ [OnboardingLanguage] 同步语言偏好失败:', e)
      }
    }
    try {
      await syncPreferences()
    } finally {
      setIsSubmitting(false)
    }
    if (onContinue) {
      onContinue(selectedCode)
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-xl bg-white rounded-2xl border border-gray-200 shadow-sm px-6 py-8 sm:px-8 sm:py-10">
        <div className="flex flex-col items-center text-center space-y-4">
          <div
            className="flex h-14 w-14 items-center justify-center rounded-full"
            style={{ backgroundColor: colors.primary[50], color: colors.primary[600] }}
          >
            <span className="text-2xl">文</span>
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
              {t('想阅读什么语言？')}
            </h1>
            <p className="text-sm sm:text-base text-gray-500">
              {t('选择你想要学习的语言')}
            </p>
          </div>
        </div>

        {/* 可滚动语言列表，方便未来扩展更多语言 */}
        <div className="mt-8">
          <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
            {languageOptions.map((option) => {
              const isActive = selectedCode === option.code
              const displayName = t(LANGUAGE_CODE_TO_NAME[option.code] || option.nativeName)
              return (
                <button
                  key={option.code}
                  type="button"
                  onClick={() => setSelectedCode(option.code)}
                  className={[
                    'w-full flex items-center justify-between rounded-xl border px-4 py-4 sm:px-5 sm:py-5 bg-white transition-all',
                    'focus:outline-none focus:ring-2 focus:ring-offset-1',
                    isActive
                      ? 'border-primary-500 ring-2 ring-primary-200 shadow-sm'
                      : 'border-gray-200 hover:border-primary-200 hover:bg-gray-50',
                  ].join(' ')}
                  style={{
                    '--tw-ring-color': colors.primary[300],
                  }}
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 text-sm font-semibold text-gray-700">
                      {option.countryCode}
                    </div>
                    <div className="flex flex-col items-start">
                      <span className="text-base sm:text-lg font-semibold text-gray-900">
                        {displayName}
                      </span>
                      <span className="text-xs sm:text-sm text-gray-500">
                        {option.nativeName}
                      </span>
                    </div>
                  </div>
                  {isActive && (
                    <div
                      className="hidden sm:flex h-7 w-7 items-center justify-center rounded-full"
                      style={{
                        backgroundColor: colors.primary[50],
                        color: colors.primary[600],
                      }}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        </div>

        <div className="mt-8">
          <button
            type="button"
            onClick={handleContinue}
            disabled={!selectedCode || isSubmitting}
            className="w-full inline-flex items-center justify-center rounded-xl px-4 py-3 text-sm sm:text-base font-medium text-white shadow-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            style={{
              backgroundColor: colors.primary[500],
            }}
            onMouseEnter={(e) => {
              if (e.currentTarget.disabled) return
              e.currentTarget.style.backgroundColor = colors.primary[600]
            }}
            onMouseLeave={(e) => {
              if (e.currentTarget.disabled) return
              e.currentTarget.style.backgroundColor = colors.primary[500]
            }}
          >
            {isSubmitting ? t('处理中...') : t('继续')} →
          </button>
        </div>
      </div>
    </div>
  )
}

export default OnboardingLanguage

