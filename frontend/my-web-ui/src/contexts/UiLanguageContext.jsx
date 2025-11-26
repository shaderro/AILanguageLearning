import { createContext, useContext, useState, useEffect, useRef } from 'react'
import localeEn from '../i18n/localeEn.json'

const UiLanguageContext = createContext(null)

const STORAGE_KEY = 'ui_language'

export const UiLanguageProvider = ({ children }) => {
  const [uiLanguage, setUiLanguage] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved === 'en' ? 'en' : 'zh'
  })
  const originalTextMapRef = useRef(new Map())

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, uiLanguage)
  }, [uiLanguage])

  useEffect(() => {
    if (typeof document === 'undefined') return
    const map = originalTextMapRef.current

    if (uiLanguage === 'en') {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
      while (walker.nextNode()) {
        const node = walker.currentNode
        if (!node || !node.textContent) continue
        const trimmed = node.textContent.trim()
        if (!trimmed) continue
        const translation = localeEn[trimmed]
        if (!translation) continue
        if (!map.has(node)) {
          map.set(node, node.textContent)
        }
        node.textContent = node.textContent.replace(trimmed, translation)
      }
    } else {
      map.forEach((original, node) => {
        if (node && original !== undefined) {
          node.textContent = original
        }
      })
      map.clear()
    }
  }, [uiLanguage])

  const value = { uiLanguage, setUiLanguage }

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


