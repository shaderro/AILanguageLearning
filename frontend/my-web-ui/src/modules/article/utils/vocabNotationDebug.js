// 临时 Debug：Vocab Notation hover / tooltip / example 加载链路
// 目标：不依赖控制台，直接在页面内 Debug Panel 可复制查看

const LS_KEY = 'debug_vocab_notation'
const EVENT_NAME = 'vocab-notation-debug-updated'
const MAX_LINES = 400

export function isVocabNotationDebugEnabled() {
  try {
    const qs = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null
    const param = qs?.get('debugVocabNotation')

    // URL 显式控制优先
    if (param === '1' || param === 'true') return true
    if (param === '0' || param === 'false') return false

    if (typeof window !== 'undefined') {
      const ls = window.localStorage?.getItem(LS_KEY)
      if (ls === '1' || ls === 'true') return true
      if (ls === '0' || ls === 'false') return false
    }

    // 默认关闭（开发环境），可通过 URL 参数 ?debugVocabNotation=1 或 localStorage 设置 debug_vocab_notation=1 开启
    return false
  } catch {
    return false
  }
}

function safeJson(obj) {
  try {
    return JSON.stringify(obj)
  } catch {
    return '[unserializable]'
  }
}

export function logVocabNotationDebug(message, data = null) {
  if (!isVocabNotationDebugEnabled()) return
  if (typeof window === 'undefined') return

  const ts = new Date().toISOString().replace('T', ' ').replace('Z', '')
  const line = data ? `[${ts}] ${message} ${safeJson(data)}` : `[${ts}] ${message}`

  if (!Array.isArray(window.__vocabNotationDebugLines)) {
    window.__vocabNotationDebugLines = []
  }
  window.__vocabNotationDebugLines.push(line)
  if (window.__vocabNotationDebugLines.length > MAX_LINES) {
    window.__vocabNotationDebugLines = window.__vocabNotationDebugLines.slice(-MAX_LINES)
  }

  window.dispatchEvent(new CustomEvent(EVENT_NAME))
}

export function getVocabNotationDebugText() {
  if (typeof window === 'undefined') return ''
  const lines = Array.isArray(window.__vocabNotationDebugLines) ? window.__vocabNotationDebugLines : []
  return lines.join('\n')
}

export function clearVocabNotationDebug() {
  if (typeof window === 'undefined') return
  window.__vocabNotationDebugLines = []
  window.dispatchEvent(new CustomEvent(EVENT_NAME))
}

export const VOCAB_NOTATION_DEBUG_EVENT_NAME = EVENT_NAME

