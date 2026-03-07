import { useState } from 'react'
import { getQuickTranslation, getSystemLanguage } from '../services/translationService'
import { colors } from '../design-tokens'

/**
 * 测试翻译 API 页面（本地调试用）
 *
 * 访问方式：
 *   http://localhost:5173/?page=testTranslationAPI
 */
const TestTranslationAPI = () => {
  const [sourceLang, setSourceLang] = useState('de') // 源语言
  const [targetLang, setTargetLang] = useState(getSystemLanguage() || 'zh') // 目标语言
  const [text, setText] = useState('')
  const [result, setResult] = useState('')
  const [source, setSource] = useState('') // 翻译来源说明
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleQuery = async () => {
    setError('')
    setResult('')
    setSource('')

    const trimmed = text.trim()
    if (!trimmed) {
      setError('请输入要翻译的单词或句子。')
      return
    }

    setIsLoading(true)
    try {
      const translationResult = await getQuickTranslation(trimmed, sourceLang, targetLang, {
        useDictionary: false,
        returnWithSource: true
      })

      if (!translationResult) {
        setResult('(未从翻译 API 获取到结果)')
      } else if (typeof translationResult === 'object') {
        setResult(translationResult.text || '')
        setSource(translationResult.source === 'translation' ? '外部翻译 API' : translationResult.source || 'unknown')
      } else {
        setResult(translationResult)
        setSource('外部翻译 API')
      }
    } catch (e) {
      console.error('❌ [TestTranslationAPI] 翻译查询失败:', e)
      setError(e?.message || '查询失败')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-5xl bg-white rounded-2xl border border-gray-200 shadow-sm px-6 py-8 sm:px-8 sm:py-10">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">TestTranslationAPI（翻译 API 测试页）</h1>
          <span className="text-xs text-gray-400">本地调试用：测试 getQuickTranslation / MyMemory / LibreTranslate 效果</span>
        </div>

        <div className="flex flex-col sm:flex-row gap-6">
          {/* 左侧：输入区域 */}
          <div className="w-full sm:w-1/2 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">源语言</label>
                <select
                  value={sourceLang}
                  onChange={(e) => setSourceLang(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2"
                  style={{ '--tw-ring-color': colors.primary[300] }}
                >
                  <option value="de">德语 (de)</option>
                  <option value="en">英语 (en)</option>
                  <option value="zh">中文 (zh)</option>
                  <option value="fr">法语 (fr)</option>
                  <option value="es">西班牙语 (es)</option>
                  <option value="ja">日语 (ja)</option>
                  <option value="ko">韩语 (ko)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">目标语言</label>
                <select
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2"
                  style={{ '--tw-ring-color': colors.primary[300] }}
                >
                  <option value="zh">中文 (zh)</option>
                  <option value="en">英语 (en)</option>
                  <option value="de">德语 (de)</option>
                  <option value="fr">法语 (fr)</option>
                  <option value="es">西班牙语 (es)</option>
                  <option value="ja">日语 (ja)</option>
                  <option value="ko">韩语 (ko)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">要翻译的文本（单词或句子）</label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="例如：Der Klimawandel ist eine der größten Herausforderungen unserer Zeit."
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 resize-none"
                style={{ '--tw-ring-color': colors.primary[300] }}
              />
            </div>

            <button
              type="button"
              onClick={handleQuery}
              disabled={isLoading}
              className="inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium text-white shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
              style={{ backgroundColor: colors.primary[500] }}
              onMouseEnter={(e) => {
                if (e.currentTarget.disabled) return
                e.currentTarget.style.backgroundColor = colors.primary[600]
              }}
              onMouseLeave={(e) => {
                if (e.currentTarget.disabled) return
                e.currentTarget.style.backgroundColor = colors.primary[500]
              }}
            >
              {isLoading ? '查询中...' : '测试翻译'}
            </button>

            {error && (
              <div className="mt-2 text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="mt-4 text-xs text-gray-500 space-y-1">
              <p>说明：</p>
              <p>- 使用与 ChatView / hover 翻译相同的 getQuickTranslation 函数。</p>
              <p>- 当前阶段关闭词典，仅测试外部翻译 API（MyMemory → LibreTranslate）。</p>
            </div>
          </div>

          {/* 右侧：结果区域 */}
          <div className="w-full sm:w-1/2 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-800">翻译结果</h2>
              {source && (
                <span className="text-xs text-gray-500">{source}</span>
              )}
            </div>

            <div className="min-h-[160px] max-h-[360px] border border-gray-200 rounded-md bg-gray-50 p-3 overflow-auto">
              {isLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                  <span>正在从翻译 API 获取数据...</span>
                </div>
              ) : result ? (
                <pre className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed">
{result}
                </pre>
              ) : (
                <div className="text-sm text-gray-400">
                  结果区域：点击左侧「测试翻译」后将在这里显示翻译结果（若无结果会显示占位提示）。
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TestTranslationAPI

