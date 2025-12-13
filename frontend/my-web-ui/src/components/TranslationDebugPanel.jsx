import { useTranslationDebug } from '../contexts/TranslationDebugContext'

/**
 * 翻译调试面板组件
 * 显示翻译服务的调试日志，方便定位问题
 */
export default function TranslationDebugPanel() {
  const { logs, isVisible, clearLogs, toggleVisibility } = useTranslationDebug()

  // 获取日志级别的样式
  const getLogLevelStyle = (level) => {
    switch (level) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'info':
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200'
    }
  }

  // 获取日志级别的图标
  const getLogLevelIcon = (level) => {
    switch (level) {
      case 'success':
        return '✅'
      case 'warning':
        return '⚠️'
      case 'error':
        return '❌'
      case 'info':
      default:
        return 'ℹ️'
    }
  }

  // 格式化数据对象
  const formatData = (data) => {
    if (!data) return null
    try {
      return JSON.stringify(data, null, 2)
    } catch (e) {
      return String(data)
    }
  }

  if (!isVisible) {
    return (
      <button
        onClick={toggleVisibility}
        className="fixed bottom-4 right-4 z-50 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        title="打开翻译调试面板"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span>调试面板</span>
        {logs.length > 0 && (
          <span className="bg-red-500 text-white text-xs rounded-full px-2 py-0.5">
            {logs.length}
          </span>
        )}
      </button>
    )
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 max-h-[600px] bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="font-semibold text-gray-800">调试面板</h3>
          {logs.length > 0 && (
            <span className="bg-blue-500 text-white text-xs rounded-full px-2 py-0.5">
              {logs.length}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearLogs}
            className="text-gray-500 hover:text-gray-700 text-sm px-2 py-1 rounded hover:bg-gray-200 transition-colors"
            title="清除日志"
          >
            清除
          </button>
          <button
            onClick={toggleVisibility}
            className="text-gray-500 hover:text-gray-700 p-1 rounded hover:bg-gray-200 transition-colors"
            title="关闭面板"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* 日志列表 */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {logs.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>暂无日志</p>
            <p className="text-xs mt-1">hover 单词查看翻译日志</p>
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className={`p-2 rounded border text-sm ${getLogLevelStyle(log.level)}`}
            >
              <div className="flex items-start gap-2">
                <span className="text-base">{getLogLevelIcon(log.level)}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-gray-500 font-mono">{log.timestamp}</span>
                    <span className="text-xs font-semibold uppercase">{log.level}</span>
                  </div>
                  <div className="text-sm font-medium break-words">{log.message}</div>
                  {log.data && (
                    <details className="mt-1">
                      <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800">
                        查看详情
                      </summary>
                      <pre className="mt-1 text-xs bg-white/50 p-2 rounded border border-gray-200 overflow-x-auto">
                        {formatData(log.data)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

