import { useEffect, useMemo, useState, useCallback, useRef } from 'react'
import {
  VOCAB_NOTATION_DEBUG_EVENT_NAME,
  clearVocabNotationDebug,
  getVocabNotationDebugText,
  isVocabNotationDebugEnabled,
} from '../utils/vocabNotationDebug'

export default function VocabNotationDebugPanel() {
  const enabled = isVocabNotationDebugEnabled()
  const [text, setText] = useState('')
  const textRef = useRef('')

  // 🔧 使用 useCallback 稳定 update 函数，避免无限循环
  const update = useCallback(() => {
    const newText = getVocabNotationDebugText()
    // 🔧 只有当文本真正改变时才更新 state，避免不必要的重新渲染
    if (newText !== textRef.current) {
      textRef.current = newText
      setText(newText)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    // 初始更新
    update()

    window.addEventListener(VOCAB_NOTATION_DEBUG_EVENT_NAME, update)
    return () => window.removeEventListener(VOCAB_NOTATION_DEBUG_EVENT_NAME, update)
  }, [enabled, update])

  const helpText = useMemo(() => {
    return [
      'Vocab Notation Debug Panel（可直接复制）',
      '开启方式：URL 加 `?debugVocabNotation=1` 或 localStorage 设置 `debug_vocab_notation=1`',
      '关注点：hover 时 hasVocabVisual 是否为 true、notations 是否已加载、example 请求是否命中缓存/发起后端',
    ].join('\n')
  }, [])

  if (!enabled) return null

  return (
    <div
      className="fixed bottom-3 right-3 z-[99999] w-[520px] max-w-[calc(100vw-24px)] bg-white border border-gray-300 shadow-lg rounded-md p-3"
      style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace' }}
    >
      <div className="text-xs text-gray-700 whitespace-pre-wrap mb-2">
        {helpText}
      </div>

      <div className="flex items-center gap-2 mb-2">
        <button
          className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
          onClick={async () => {
            try {
              await navigator.clipboard.writeText(text || '')
            } catch {
              // ignore
            }
          }}
        >
          Copy
        </button>
        <button
          className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
          onClick={() => clearVocabNotationDebug()}
        >
          Clear
        </button>
        <div className="text-xs text-gray-500">
          Lines: {(text ? text.split('\n').length : 0)}
        </div>
      </div>

      <textarea
        className="w-full h-56 text-xs p-2 border border-gray-200 rounded bg-gray-50 text-gray-900"
        readOnly
        value={text}
        onFocus={(e) => e.target.select()}
      />
    </div>
  )
}

