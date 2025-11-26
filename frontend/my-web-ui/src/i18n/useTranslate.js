import localeEn from './localeEn.json'
import { useUiLanguage } from '../contexts/UiLanguageContext'

/**
 * Translation helper that uses the Chinese text as the lookup key.
 * Example: t('登录') -> 'Login' when UI language is English.
 */
export const useTranslate = () => {
  const { uiLanguage } = useUiLanguage()

  const translate = (text, fallback) => {
    if (!text) return ''
    if (uiLanguage === 'en') {
      return localeEn[text] || fallback || text
    }
    return text
  }

  return translate
}

