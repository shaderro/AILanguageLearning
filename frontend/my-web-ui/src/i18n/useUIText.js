import { useCallback } from 'react'
import zhTexts from './texts_zh.json'
import enTexts from './texts_en.json'
import { useUiLanguage } from '../contexts/UiLanguageContext'

const TEXT_MAP = {
  zh: zhTexts,
  en: enTexts
}

export const useUIText = () => {
  const { uiLanguage } = useUiLanguage()
  const lang = TEXT_MAP[uiLanguage] ? uiLanguage : 'zh'

  return useCallback(
    (key) => {
      if (!key) return ''
      const value = TEXT_MAP[lang][key] ?? TEXT_MAP.zh[key]
      return value ?? key
    },
    [lang],
  )
}

export const translateText = (key, language = 'zh') => {
  const lang = TEXT_MAP[language] ? language : 'zh'
  return TEXT_MAP[lang][key] ?? TEXT_MAP.zh[key] ?? key
}


