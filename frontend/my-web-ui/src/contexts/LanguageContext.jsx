import { createContext, useContext, useState } from 'react'

const LanguageContext = createContext()

/**
 * 将中文语言名转换为语言代码
 * @param {string} languageName - 语言名称（如 '中文', '英语', '西班牙语', '法语', '日语', '韩语', '德语', '阿拉伯语', '俄语'）
 * @returns {string} 语言代码（如 'zh', 'en', 'es', 'fr', 'ja', 'ko', 'de', 'ar', 'ru'）
 */
export const languageNameToCode = (languageName) => {
  const map = {
    '中文': 'zh',
    '英文': 'en', // 兼容旧值
    '英语': 'en',
    '西班牙语': 'es',
    '法语': 'fr',
    '日文': 'ja', // 兼容旧值
    '日语': 'ja',
    '韩语': 'ko',
    '德文': 'de', // 兼容旧值
    '德语': 'de',
    '阿拉伯语': 'ar',
    '俄语': 'ru',
    'Chinese': 'zh',
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Arabic': 'ar',
    'Russian': 'ru',
    '日本語': 'ja',
  }
  return map[languageName] || 'de' // 默认返回 'de'
}

/**
 * 将语言代码转换为 BCP 47 标签（用于语音合成）
 * @param {string} langCode - 语言代码（'zh', 'en', 'de', 'ja'）
 * @returns {string} BCP 47 标签（'zh-CN', 'en-US', 'de-DE', 'ja-JP'）
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
    'ar': 'ar-SA',
    'ru': 'ru-RU',
  }
  return map[langCode] || langCode
}

export const LanguageProvider = ({ children }) => {
  // 🔧 默认值改为具体语言，禁止 'all'
  const [selectedLanguage, setSelectedLanguage] = useState('德文') // 支持多语言（含旧值：英文/德文）

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

