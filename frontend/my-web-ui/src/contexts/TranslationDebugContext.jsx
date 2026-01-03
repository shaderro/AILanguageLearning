import { createContext, useContext, useState, useCallback, useRef } from 'react'

const TranslationDebugContext = createContext()

/**
 * 翻译调试日志提供者
 * 用于收集和显示翻译相关的调试信息
 */
export const TranslationDebugProvider = ({ children }) => {
  const [logs, setLogs] = useState([])
  const [isVisible, setIsVisible] = useState(true) // 🔧 默认显示，方便调试
  const maxLogs = useRef(200) // 最多保留200条日志（增加以容纳更多调试信息）

  /**
   * 添加日志
   * @param {string} level - 日志级别: 'info', 'success', 'warning', 'error'
   * @param {string} message - 日志消息
   * @param {object} data - 附加数据（可选）
   */
  const addLog = useCallback((level, message, data = null) => {
    const timestamp = new Date().toLocaleTimeString('zh-CN', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    })
    
    setLogs(prev => {
      const newLog = {
        id: Date.now() + Math.random(),
        timestamp,
        level,
        message,
        data
      }
      const updated = [newLog, ...prev]
      // 限制日志数量
      return updated.slice(0, maxLogs.current)
    })
  }, [])

  /**
   * 清除所有日志
   */
  const clearLogs = useCallback(() => {
    setLogs([])
  }, [])

  /**
   * 切换面板可见性
   */
  const toggleVisibility = useCallback(() => {
    setIsVisible(prev => !prev)
  }, [])

  const value = {
    logs,
    isVisible,
    addLog,
    clearLogs,
    toggleVisibility,
    setIsVisible
  }

  return (
    <TranslationDebugContext.Provider value={value}>
      {children}
    </TranslationDebugContext.Provider>
  )
}

/**
 * 使用翻译调试上下文
 */
export const useTranslationDebug = () => {
  const context = useContext(TranslationDebugContext)
  if (!context) {
    // 如果不在Provider中，返回一个no-op实现
    return {
      logs: [],
      isVisible: false,
      addLog: () => {},
      clearLogs: () => {},
      toggleVisibility: () => {},
      setIsVisible: () => {}
    }
  }
  return context
}

