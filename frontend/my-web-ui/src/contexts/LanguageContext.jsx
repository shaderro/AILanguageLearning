import { createContext, useContext, useState } from 'react'

const LanguageContext = createContext()

/**
 * 将中文语言名转换为语言代码
 * @param {string} languageName - 语言名称（'中文', '英文', '德文'）
 * @returns {string} 语言代码（'zh', 'en', 'de'）
 */
export const languageNameToCode = (languageName) => {
  const map = {
    '中文': 'zh',
    '英文': 'en',
    '德文': 'de',
    'Chinese': 'zh',
    'English': 'en',
    'German': 'de',
  }
  return map[languageName] || 'de' // 默认返回 'de'
}

/**
 * 将语言代码转换为 BCP 47 标签（用于语音合成）
 * @param {string} langCode - 语言代码（'zh', 'en', 'de'）
 * @returns {string} BCP 47 标签（'zh-CN', 'en-US', 'de-DE'）
 */
export const languageCodeToBCP47 = (langCode) => {
  const map = {
    'zh': 'zh-CN',
    'en': 'en-US',
    'de': 'de-DE',
    'fr': 'fr-FR',
    'es': 'es-ES',
    'it': 'it-IT',
    'ja': 'ja-JP',
    'ko': 'ko-KR',
  }
  return map[langCode] || langCode
}

export const LanguageProvider = ({ children }) => {
  // 🔧 默认值改为具体语言，禁止 'all'
  const [selectedLanguage, setSelectedLanguage] = useState('德文') // '中文', '英文', '德文'

  return (
    <LanguageContext.Provider value={{ selectedLanguage, setSelectedLanguage }}>
      {children}
    </LanguageContext.Provider>
  )
}

export const useLanguage = () => {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}

