import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react'

const UiLanguageContext = createContext(null)

const STORAGE_KEY = 'ui_language'

export const UiLanguageProvider = ({ children }) => {
  const [uiLanguage, setUiLanguageState] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved === 'en' ? 'en' : 'zh'
  })

  const setUiLanguage = useCallback((next) => {
    setUiLanguageState((prev) => (typeof next === 'function' ? next(prev) : next))
  }, [])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, uiLanguage)
  }, [uiLanguage])

  const value = useMemo(
    () => ({ uiLanguage, setUiLanguage }),
    [uiLanguage, setUiLanguage],
  )

  return (
    <UiLanguageContext.Provider value={value}>
      {children}
    </UiLanguageContext.Provider>
  )
}

export const useUiLanguage = () => {
  const context = useContext(UiLanguageContext)
  if (!context) {
    throw new Error('useUiLanguage must be used within UiLanguageProvider')
  }
  return context
}


