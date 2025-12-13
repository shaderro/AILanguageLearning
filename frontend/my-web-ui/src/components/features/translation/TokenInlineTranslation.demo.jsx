/**
 * TokenInlineTranslation Demo
 * 演示内联翻译组件的使用
 */
import { useState } from 'react'
import TokenInlineTranslation from './TokenInlineTranslation'
import { useLanguage, languageNameToCode } from '../../../contexts/LanguageContext'
import { getSystemLanguage } from '../../../services/translationService'
import { useTranslationDebug } from '../../../contexts/TranslationDebugContext'
import TranslationDebugPanel from '../../../components/TranslationDebugPanel'

export default function TokenInlineTranslationDemo() {
  const { selectedLanguage } = useLanguage()
  const { addLog: addDebugLog } = useTranslationDebug()
  
  // 计算目标语言
  const sourceLang = 'de'
  const globalLang = languageNameToCode(selectedLanguage)
  const preferredLang = globalLang || getSystemLanguage()
  let targetLang = preferredLang === sourceLang 
    ? (getSystemLanguage() !== sourceLang ? getSystemLanguage() : (sourceLang === 'en' ? 'zh' : 'en'))
    : preferredLang
  
  // 确保 targetLang 不为空
  if (!targetLang) {
    targetLang = getSystemLanguage() || 'en'
  }
  
  // 调试日志
  console.log('🔍 [TokenInlineTranslationDemo] 语言配置:', {
    selectedLanguage,
    globalLang,
    preferredLang,
    sourceLang,
    targetLang,
    systemLang: getSystemLanguage()
  })

  const [translationLog, setTranslationLog] = useState([])

  const handleTranslationStart = (word) => {
    setTranslationLog(prev => [...prev, { type: 'start', word, time: new Date().toLocaleTimeString() }])
  }

  const handleTranslationComplete = (word, translation) => {
    setTranslationLog(prev => [...prev, { 
      type: 'complete', 
      word, 
      translation, 
      time: new Date().toLocaleTimeString() 
    }])
  }

  const debugLogger = (level, message, data) => {
    addDebugLog(level, message, data)
  }

  // 示例文本（德语）
  const sampleTexts = [
    {
      title: '基础用法',
      description: 'Hover 单词查看翻译',
      words: ['Haus', 'Buch', 'Freund', 'Schule']
    },
    {
      title: '句子中的单词',
      description: '在句子中使用内联翻译',
      sentence: 'Der Hund läuft im Park.'
    },
    {
      title: '自定义延迟',
      description: '延迟时间设置为 500ms',
      words: ['Auto', 'Stadt', 'Land'],
      delay: 500
    }
  ]

  return (
    <div className="space-y-8">
      {/* 翻译调试面板 */}
      <TranslationDebugPanel />
      
      {/* 配置信息 */}
      <div className="rounded-lg bg-blue-50 p-4 border border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">当前配置</h3>
        <div className="text-sm text-blue-800 space-y-1">
          <div>源语言: <span className="font-mono">{sourceLang}</span></div>
          <div>目标语言: <span className="font-mono">{targetLang}</span></div>
          <div>全局选择语言: <span className="font-mono">{selectedLanguage}</span></div>
        </div>
      </div>

      {/* 示例 1: 基础用法 */}
      <div className="space-y-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{sampleTexts[0].title}</h3>
          <p className="text-sm text-gray-600">{sampleTexts[0].description}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex flex-wrap gap-4 text-lg">
            {sampleTexts[0].words.map((word, idx) => (
              <TokenInlineTranslation
                key={idx}
                word={word}
                sourceLang={sourceLang}
                targetLang={targetLang}
                debugLogger={debugLogger}
                onTranslationStart={handleTranslationStart}
                onTranslationComplete={handleTranslationComplete}
              >
                <span className="px-2 py-1 bg-white rounded border border-gray-300 hover:border-blue-400 hover:bg-blue-50 transition-colors cursor-pointer">
                  {word}
                </span>
              </TokenInlineTranslation>
            ))}
          </div>
        </div>
      </div>

      {/* 示例 2: 句子中的单词 */}
      <div className="space-y-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{sampleTexts[1].title}</h3>
          <p className="text-sm text-gray-600">{sampleTexts[1].description}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <p className="text-lg leading-relaxed">
            {sampleTexts[1].sentence.split(' ').map((word, idx) => {
              const cleanWord = word.replace(/[.,!?;:]$/, '')
              const punctuation = word.replace(cleanWord, '')
              return (
                <span key={idx}>
                  <TokenInlineTranslation
                    word={cleanWord}
                    sourceLang={sourceLang}
                    targetLang={targetLang}
                    debugLogger={debugLogger}
                    onTranslationStart={handleTranslationStart}
                    onTranslationComplete={handleTranslationComplete}
                  >
                    <span className="hover:bg-blue-100 hover:underline cursor-pointer px-1 rounded">
                      {cleanWord}
                    </span>
                  </TokenInlineTranslation>
                  {punctuation && <span>{punctuation}</span>}
                  {idx < sampleTexts[1].sentence.split(' ').length - 1 && ' '}
                </span>
              )
            })}
          </p>
        </div>
      </div>

      {/* 示例 3: 自定义延迟 */}
      <div className="space-y-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{sampleTexts[2].title}</h3>
          <p className="text-sm text-gray-600">{sampleTexts[2].description}</p>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex flex-wrap gap-4 text-lg">
            {sampleTexts[2].words.map((word, idx) => (
              <TokenInlineTranslation
                key={idx}
                word={word}
                sourceLang={sourceLang}
                targetLang={targetLang}
                hoverDelay={sampleTexts[2].delay}
                debugLogger={debugLogger}
                onTranslationStart={handleTranslationStart}
                onTranslationComplete={handleTranslationComplete}
              >
                <span className="px-2 py-1 bg-white rounded border border-gray-300 hover:border-blue-400 hover:bg-blue-50 transition-colors cursor-pointer">
                  {word}
                </span>
              </TokenInlineTranslation>
            ))}
          </div>
        </div>
      </div>

      {/* 翻译日志 */}
      {translationLog.length > 0 && (
        <div className="space-y-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">翻译日志</h3>
            <p className="text-sm text-gray-600">显示最近的翻译活动</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 max-h-48 overflow-y-auto">
            <div className="space-y-2">
              {translationLog.slice(-10).reverse().map((log, idx) => (
                <div
                  key={idx}
                  className={`text-sm p-2 rounded ${
                    log.type === 'start'
                      ? 'bg-yellow-50 border border-yellow-200'
                      : 'bg-green-50 border border-green-200'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-gray-500">{log.time}</span>
                    <span className="font-semibold">{log.word}</span>
                    {log.type === 'complete' && log.translation && (
                      <span className="text-gray-600">→ {log.translation}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 使用说明 */}
      <div className="rounded-lg bg-gray-50 p-4 border border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-2">使用说明</h3>
        <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
          <li>将鼠标悬停在单词上，等待 250ms（或自定义延迟）后会自动查询翻译</li>
          <li>翻译结果会显示在单词下方的 tooltip 中</li>
          <li>支持自定义源语言和目标语言</li>
          <li>支持自定义 hover 延迟时间</li>
          <li>支持自定义 tooltip 位置（top/bottom/left/right）</li>
          <li>支持提供本地词汇列表和自定义 API 提供者</li>
          <li>支持翻译开始和完成的回调函数</li>
        </ul>
      </div>
    </div>
  )
}

