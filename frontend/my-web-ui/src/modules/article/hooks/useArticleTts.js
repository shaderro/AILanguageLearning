/* @refresh reset */
import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Chromium / Edge：过长 utterance 易中断；按长度拆段顺序朗读。
 */
function choosePunctuationCutIndex(slice) {
  const punctuationRegex = /[.!?;,:。，！？；：、]/g
  const matches = Array.from(slice.matchAll(punctuationRegex))
  if (matches.length === 0) return -1
  const mid = Math.floor(slice.length / 2)
  let best = matches[0].index ?? -1
  let bestDist = Math.abs(best - mid)
  for (const m of matches) {
    const idx = m.index ?? -1
    if (idx < 0) continue
    const dist = Math.abs(idx - mid)
    if (dist < bestDist) {
      best = idx
      bestDist = dist
    }
  }
  return best >= 0 ? best + 1 : -1
}

function chooseWhitespaceCutIndex(slice) {
  const whitespaceRegex = /\s+/g
  const matches = Array.from(slice.matchAll(whitespaceRegex))
  if (matches.length === 0) return -1
  const mid = Math.floor(slice.length / 2)
  let best = -1
  let bestDist = Number.POSITIVE_INFINITY
  for (const m of matches) {
    const idx = m.index ?? -1
    if (idx < 0) continue
    // Cut after whitespace run to avoid chopping a word.
    const cut = idx + m[0].length
    const dist = Math.abs(cut - mid)
    if (dist < bestDist) {
      best = cut
      bestDist = dist
    }
  }
  return best
}

function adjustCutToWordBoundary(text, proposedCut) {
  const len = text.length
  if (proposedCut <= 0 || proposedCut >= len) return Math.floor(len / 2)

  const isLetterOrNumber = (ch) => /[\p{L}\p{N}]/u.test(ch || '')
  const isConnector = (ch) => ch === '\'' || ch === '’' || ch === '-'
  const isWordLike = (ch) => isLetterOrNumber(ch) || isConnector(ch)
  const isSplitInsideWord = (s, cut) => {
    const l = s[cut - 1]
    const r = s[cut]
    if (!l || !r) return false
    if (isLetterOrNumber(l) && isLetterOrNumber(r)) return true
    // don't / mother-in-law: avoid splitting around connector when both sides are word chars.
    if (isConnector(l) && cut - 2 >= 0 && isLetterOrNumber(s[cut - 2]) && isLetterOrNumber(r)) return true
    if (isConnector(r) && cut + 1 < s.length && isLetterOrNumber(l) && isLetterOrNumber(s[cut + 1])) return true
    return false
  }

  // If not splitting in the middle of a word-like token, keep it.
  if (!isSplitInsideWord(text, proposedCut)) {
    return proposedCut
  }

  // Walk outward to nearest non-word boundary.
  let left = proposedCut
  while (left > 0 && isWordLike(text[left - 1])) left -= 1

  let right = proposedCut
  while (right < len && isWordLike(text[right])) right += 1

  // Prefer boundary closer to midpoint; fallback to left then right.
  const distLeft = Math.abs(proposedCut - left)
  const distRight = Math.abs(right - proposedCut)
  if (left > 0 && right < len) {
    return distLeft <= distRight ? left : right
  }
  if (left > 0) return left
  if (right < len) return right
  return Math.floor(len / 2)
}

function splitByPunctuationOrHalving(text, maxChunk, baseOffset = 0) {
  if (!text || text.length <= maxChunk) {
    return [{ text, charOffset: baseOffset }]
  }
  const punctuationCut = choosePunctuationCutIndex(text)
  const whitespaceCut = punctuationCut > 0 ? -1 : chooseWhitespaceCutIndex(text)
  const fallbackHalf = Math.floor(text.length / 2)
  const rawCut = punctuationCut > 0
    ? punctuationCut
    : whitespaceCut > 0
      ? whitespaceCut
      : fallbackHalf
  const cut = adjustCutToWordBoundary(text, rawCut)

  const left = text.slice(0, cut)
  const right = text.slice(cut)
  return [
    ...splitByPunctuationOrHalving(left, maxChunk, baseOffset),
    ...splitByPunctuationOrHalving(right, maxChunk, baseOffset + cut),
  ]
}

function fixBrokenWordBoundaries(segments) {
  if (!Array.isArray(segments) || segments.length <= 1) return segments
  const isWordHead = (ch) => /[\p{L}\p{N}]/u.test(ch || '')
  const isWordTail = (ch) => /[\p{L}\p{N}]/u.test(ch || '')
  const isWhitespace = (ch) => /\s/.test(ch || '')

  const fixed = segments.map((s) => ({ ...s }))
  for (let i = 1; i < fixed.length; i++) {
    const prev = fixed[i - 1]
    const curr = fixed[i]
    if (!prev?.text || !curr?.text) continue
    const prevLast = prev.text[prev.text.length - 1]
    const currFirst = curr.text[0]
    const brokenInsideWord = isWordTail(prevLast) && isWordHead(currFirst)
    if (!brokenInsideWord) continue

    // Move trailing word-fragment from previous segment to current segment.
    let boundary = -1
    for (let j = prev.text.length - 1; j >= 0; j--) {
      if (isWhitespace(prev.text[j])) {
        boundary = j
        break
      }
    }
    if (boundary < 0) {
      // no safe boundary in previous part; keep as-is
      continue
    }
    const moved = prev.text.slice(boundary + 1)
    prev.text = prev.text.slice(0, boundary + 1)
    curr.text = `${moved}${curr.text}`
  }

  // Recompute char offsets from final segment texts.
  let offset = 0
  for (let i = 0; i < fixed.length; i++) {
    fixed[i].charOffset = offset
    offset += fixed[i].text.length
  }
  return fixed
}

export function splitSentenceTextForTts(fullText, maxChunk = 200) {
  if (!fullText || typeof fullText !== 'string') {
    return []
  }
  const text = fullText
  const raw = splitByPunctuationOrHalving(text, maxChunk, 0).filter((s) => s.text && s.text.length > 0)
  const segments = fixBrokenWordBoundaries(raw)
  return segments.length > 0 ? segments : [{ text: fullText, charOffset: 0 }]
}

async function ensureVoicesLoaded() {
  if (typeof window === 'undefined' || !window.speechSynthesis) {
    return false
  }
  let voices = window.speechSynthesis.getVoices()
  if (voices.length > 0) return true

  return new Promise((resolve) => {
    window.speechSynthesis.getVoices()
    let resolved = false
    const timeout = setTimeout(() => {
      if (!resolved) {
        resolved = true
        voices = window.speechSynthesis.getVoices()
        resolve(voices.length > 0)
      }
    }, 2000)

    const onVoicesChanged = () => {
      if (!resolved) {
        voices = window.speechSynthesis.getVoices()
        if (voices.length > 0) {
          resolved = true
          clearTimeout(timeout)
          window.speechSynthesis.onvoiceschanged = null
          resolve(true)
        }
      }
    }

    window.speechSynthesis.onvoiceschanged = onVoicesChanged
  })
}

function pickVoiceForBcp47(bcp47) {
  const available =
    typeof window !== 'undefined' && window.speechSynthesis ? window.speechSynthesis.getVoices() : []
  if (!available.length) return null

  const byLang = available.filter((v) => {
    if (!v?.lang) return false
    return v.lang === bcp47 || v.lang.toLowerCase().startsWith(String(bcp47).split('-')[0].toLowerCase())
  })
  const pool = byLang.length > 0 ? byLang : available

  const localPreferred = pool.find((v) => v.localService)
  if (localPreferred) return localPreferred

  const nonOnlinePreferred = pool.find((v) => !/online/i.test(String(v?.name || '')))
  if (nonOnlinePreferred) return nonOnlinePreferred

  const exact = pool.find((v) => v.lang === bcp47)
  if (exact) return exact
  const prefix = String(bcp47).split('-')[0].toLowerCase()
  return pool.find((v) => v.lang && v.lang.toLowerCase().startsWith(prefix)) || pool[0] || available[0]
}

function isOnlineVoice(voice) {
  const name = String(voice?.name || '')
  return /online/i.test(name)
}

function isNonWhitespaceLanguage(sentence) {
  if (sentence?.is_non_whitespace === true) return true
  const lc = String(sentence?.language_code || sentence?.language || '').toLowerCase()
  return lc.startsWith('zh') || lc.startsWith('ja') || lc.startsWith('ko')
}

function buildTtsPayloadFromSentence(sentence, fallbackGetSentenceText) {
  if (!sentence) return { text: '', tokenOffsets: [] }
  const tokens = Array.isArray(sentence?.tokens) ? sentence.tokens : null
  if (!tokens || tokens.length === 0) {
    if (typeof sentence?.sentence_body === 'string' && sentence.sentence_body.trim()) {
      return { text: sentence.sentence_body.trim(), tokenOffsets: [] }
    }
    const fallback = fallbackGetSentenceText?.(sentence)
    return { text: typeof fallback === 'string' ? fallback.trim() : '', tokenOffsets: [] }
  }

  const parts = tokens
    .map((tk, tokenIndex) => ({ tokenIndex, text: typeof tk === 'string' ? tk : tk?.token_body || '' }))
    .filter((x) => typeof x.text === 'string' && x.text.length > 0)

  if (parts.length === 0) return { text: '', tokenOffsets: [] }

  if (isNonWhitespaceLanguage(sentence)) {
    let text = ''
    const tokenOffsets = []
    for (const part of parts) {
      const start = text.length
      text += part.text
      const end = text.length
      if (part.text.trim()) tokenOffsets.push({ tokenIndex: part.tokenIndex, start, end })
    }
    return { text, tokenOffsets }
  }

  let text = ''
  const tokenOffsets = []
  const isWordLikeHead = (s) => /^[\p{L}\p{N}]/u.test(s || '')
  const isWordLikeTail = (s) => /[\p{L}\p{N}]$/u.test(s || '')
  const isPunctuationToken = (s) => /^[,.;:!?)\]}”’%]+$/.test(s || '')
  const isOpeningPunctuationToken = (s) => /^[([{“‘]+$/.test(s || '')

  for (const part of parts) {
    const cur = part.text
    if (!cur) continue
    const prev = text
    const needSpace =
      prev.length > 0 &&
      !isPunctuationToken(cur) &&
      !isOpeningPunctuationToken(cur) &&
      isWordLikeTail(prev) &&
      isWordLikeHead(cur)

    if (needSpace) text += ' '
    const start = text.length
    text += cur
    const end = text.length
    if (cur.trim()) tokenOffsets.push({ tokenIndex: part.tokenIndex, start, end })
  }

  return { text, tokenOffsets }
}

function mapCharOffsetToTokenIndex(tokenOffsets, charOffset) {
  if (!Array.isArray(tokenOffsets) || tokenOffsets.length === 0) return null
  for (let i = 0; i < tokenOffsets.length; i++) {
    const t = tokenOffsets[i]
    if (charOffset >= t.start && charOffset < t.end) return t.tokenIndex
  }
  let nearest = tokenOffsets[0].tokenIndex
  for (let i = 0; i < tokenOffsets.length; i++) {
    if (tokenOffsets[i].start <= charOffset) nearest = tokenOffsets[i].tokenIndex
    else break
  }
  return nearest
}

function resolveUtteranceLang(sentence, selectedLanguage, languageNameToCode, languageCodeToBCP47) {
  const lc = sentence?.language_code
  if (lc && typeof lc === 'string') {
    const lower = lc.trim().toLowerCase()
    const two = lower.length === 2 ? lower : lower.split(/[-_]/)[0]
    return languageCodeToBCP47(two) || lc
  }
  if (sentence?.language) {
    const code = languageNameToCode(sentence.language)
    return languageCodeToBCP47(code)
  }
  const code = languageNameToCode(selectedLanguage)
  return languageCodeToBCP47(code)
}

/**
 * 起始句索引：
 * - 新选择：整句 / 词汇 → 对应该 sentenceId
 * - 旧交互：selectedSentenceIndex、或仅有 token 选区时的 activeSentenceIndex
 * - 否则：无效（返回 null）
 */
export function resolveTtsStartSentenceIndex(
  sentences,
  {
    currentSelection,
    selectedSentenceIndex,
    selectedSentenceIndexFromSelectionContext,
    activeSentenceIndex,
    selectedTokenIds,
  }
) {
  if (!Array.isArray(sentences) || sentences.length === 0) return null
  const selectedTokenCount =
    selectedTokenIds instanceof Set
      ? selectedTokenIds.size
      : Array.isArray(selectedTokenIds)
        ? selectedTokenIds.length
        : 0

  const bySentenceId = (sid) => {
    const idx = sentences.findIndex((s) => {
      const id = s?.sentence_id ?? s?.id
      return id === sid || String(id) === String(sid)
    })
    return idx >= 0 ? idx : null
  }

  if (currentSelection?.type === 'token' && currentSelection.sentenceId != null) {
    return bySentenceId(currentSelection.sentenceId)
  }
  if (selectedTokenCount > 0 && typeof activeSentenceIndex === 'number' && activeSentenceIndex >= 0 && activeSentenceIndex < sentences.length) {
    return activeSentenceIndex
  }
  if (currentSelection?.type === 'sentence' && currentSelection.sentenceId != null) {
    return bySentenceId(currentSelection.sentenceId)
  }
  if (
    typeof selectedSentenceIndex === 'number' &&
    selectedSentenceIndex >= 0 &&
    selectedSentenceIndex < sentences.length
  ) {
    return selectedSentenceIndex
  }
  if (
    typeof selectedSentenceIndexFromSelectionContext === 'number' &&
    selectedSentenceIndexFromSelectionContext >= 0 &&
    selectedSentenceIndexFromSelectionContext < sentences.length
  ) {
    return selectedSentenceIndexFromSelectionContext
  }
  return null
}

function buildSelectedTokenSpeechSegments(sentence, sentenceIndex, selectedTokenIds, currentSelection) {
  const tokens = Array.isArray(sentence?.tokens) ? sentence.tokens : []
  if (!tokens.length) return []
  const selectedSet =
    selectedTokenIds instanceof Set
      ? selectedTokenIds
      : new Set(Array.isArray(selectedTokenIds) ? selectedTokenIds : [])
  if (currentSelection?.type === 'token' && Array.isArray(currentSelection.tokenIds)) {
    currentSelection.tokenIds.forEach((id) => {
      selectedSet.add(String(id))
      selectedSet.add(id)
    })
  }
  if (selectedSet.size === 0) return []

  const selected = []
  for (let i = 0; i < tokens.length; i++) {
    const tk = tokens[i]
    if (!tk || typeof tk !== 'object') continue
    const sentenceTokenId = tk?.sentence_token_id
    if (sentenceTokenId == null) continue
    const composite = `${sentenceIndex}-${sentenceTokenId}`
    const plain = String(sentenceTokenId)
    if (!selectedSet.has(composite) && !selectedSet.has(plain) && !selectedSet.has(sentenceTokenId)) continue
    const text = String(tk?.token_body ?? tk?.token ?? '')
    if (!text) continue
    selected.push({ sentenceTokenId: Number(sentenceTokenId), tokenIndex: i, text })
  }
  if (!selected.length) return []
  selected.sort((a, b) => a.sentenceTokenId - b.sentenceTokenId)

  const chunks = []
  let current = null
  for (const item of selected) {
    if (!current) {
      current = {
        prevId: item.sentenceTokenId,
        text: item.text,
        tokenIndex: item.tokenIndex,
      }
      continue
    }
    if (item.sentenceTokenId === current.prevId + 1) {
      current.text += item.text
      current.prevId = item.sentenceTokenId
      continue
    }
    chunks.push({ text: current.text, tokenIndex: current.tokenIndex, charOffset: 0 })
    current = {
      prevId: item.sentenceTokenId,
      text: item.text,
      tokenIndex: item.tokenIndex,
    }
  }
  if (current) chunks.push({ text: current.text, tokenIndex: current.tokenIndex, charOffset: 0 })
  return chunks.filter((c) => c.text && c.text.trim())
}

function speakUtterance(text, bcp47, voice, shouldAbort, rate = 1, onBoundary = null) {
  return new Promise((resolve) => {
    if (shouldAbort()) {
      resolve({ status: 'aborted' })
      return
    }

    let utteranceDidStart = false
    const u = new SpeechSynthesisUtterance(text)
    u.lang = bcp47
    if (voice) u.voice = voice
    u.rate = rate
    u.pitch = 1

    const finalize = (status, error = null) => {
      u.onstart = null
      u.onend = null
      u.onerror = null
      resolve({ status, error, utteranceDidStart })
    }

    u.onstart = () => {
      utteranceDidStart = true
    }
    u.onboundary = (e) => {
      if (typeof onBoundary !== 'function') return
      if (shouldAbort()) return
      const charIndex = Number(e?.charIndex)
      if (Number.isNaN(charIndex)) return
      onBoundary(charIndex)
    }
    u.onend = () => finalize('ended')
    u.onerror = (e) => {
      if (shouldAbort()) {
        finalize('aborted')
        return
      }
      const interrupted = e?.error === 'interrupted'
      if (interrupted && utteranceDidStart) {
        finalize('interrupted_after_start', e)
        return
      }
      finalize('failed', e)
    }
    window.speechSynthesis.speak(u)
  })
}

async function waitForSynthIdle(shouldAbort, timeoutMs = 1200) {
  if (typeof window === 'undefined' || !window.speechSynthesis) return true
  const syn = window.speechSynthesis
  const start = Date.now()
  while (!shouldAbort()) {
    if (!syn.speaking && !syn.pending) {
      return true
    }
    if (Date.now() - start > timeoutMs) {
      return false
    }
    await new Promise((r) => setTimeout(r, 30))
  }
  return false
}

function ttsLog(event, payload) {
  if (payload === undefined) {
    console.log(`[TTS] ${event}`)
    return
  }
  console.log(`[TTS] ${event}`, payload)
}

function ttsWarn(event, payload) {
  if (payload === undefined) {
    console.warn(`[TTS] ${event}`)
    return
  }
  console.warn(`[TTS] ${event}`, payload)
}

/**
 * 文章朗读：仅使用 window.speechSynthesis。
 * | Hook | `useArticleTts.js` |
 * | UI | `ArticleViewer.jsx` → `SentenceContainer.jsx` |
 */
export function useArticleTts({
  sentences,
  sentencesRef,
  selectedLanguage,
  languageNameToCode,
  languageCodeToBCP47,
  getSentenceText,
  scrollContainerRef,
  getFirstVisibleSentenceIndex: _getFirstVisibleSentenceIndex,
  selectedSentenceIndex,
  selectedSentenceIndexFromSelectionContext,
  currentSelection,
  activeSentenceIndex,
  selectedTokenIds,
  t,
}) {
  void _getFirstVisibleSentenceIndex

  const speechSupported = typeof window !== 'undefined' && !!window.speechSynthesis

  const [ttsPhase, setTtsPhase] = useState('idle')
  const ttsPhaseRef = useRef('idle')
  const setPhase = useCallback((p) => {
    ttsPhaseRef.current = p
    setTtsPhase(p)
  }, [])

  const [ttsUiReading, setTtsUiReading] = useState(false)
  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return
    const tick = () => {
      const syn = window.speechSynthesis
      const engineOn = syn.speaking || syn.pending
      const p = ttsPhaseRef.current
      const phaseShows = p === 'playing' || p === 'betweenSentences' || p === 'stopping'
      setTtsUiReading(Boolean(engineOn || phaseShows))
    }
    const id = setInterval(tick, 120)
    tick()
    return () => clearInterval(id)
  }, [])

  const [currentReadingToken, setCurrentReadingToken] = useState(null)
  const setGlobalTtsActive = useCallback((active) => {
    if (typeof window === 'undefined') return
    window.__ARTICLE_TTS_ACTIVE__ = Boolean(active)
    window.__ARTICLE_TTS_OWNER__ = active ? 'article' : null
  }, [])
  const setGlobalTtsHighlight = useCallback((sentenceIndex, tokenIndex) => {
    if (typeof window === 'undefined') return
    if (sentenceIndex === null || sentenceIndex === undefined) {
      window.__ARTICLE_TTS_HIGHLIGHT__ = null
      return
    }
    window.__ARTICLE_TTS_HIGHLIGHT__ = {
      sentenceIndex,
      tokenIndex: typeof tokenIndex === 'number' ? tokenIndex : null,
    }
  }, [])

  const [currentReadingSentenceIndex, setCurrentReadingSentenceIndex] = useState(null)
  const clearHighlightTimeoutRef = useRef(null)
  const currentReadingSentenceIndexRef = useRef(null)
  const currentReadingTokenRef = useRef(null)
  useEffect(() => {
    currentReadingSentenceIndexRef.current = currentReadingSentenceIndex
    currentReadingTokenRef.current = currentReadingToken
  }, [currentReadingSentenceIndex, currentReadingToken])
  const lastHighlightSentenceRef = useRef(null)
  const lastHighlightTokenRef = useRef(null)
  const readingPositionRef = useRef({ sentenceIndex: null, tokenIndex: null })
  const applyReadingHighlight = useCallback((sentenceIndex, tokenIndex = null) => {
    ttsLog('highlight_apply', {
      sentenceIndex,
      tokenIndex: typeof tokenIndex === 'number' ? tokenIndex : null,
    })
    lastHighlightSentenceRef.current = sentenceIndex
    lastHighlightTokenRef.current = typeof tokenIndex === 'number' ? tokenIndex : null
    readingPositionRef.current = {
      sentenceIndex,
      tokenIndex: typeof tokenIndex === 'number' ? tokenIndex : null,
    }
    setGlobalTtsHighlight(sentenceIndex, tokenIndex)
    setCurrentReadingSentenceIndex(sentenceIndex)
    setCurrentReadingToken(
      typeof tokenIndex === 'number' ? { sentenceIndex, tokenIndex } : null
    )
  }, [setGlobalTtsHighlight])
  const clearReadingHighlight = useCallback(() => {
    if (clearHighlightTimeoutRef.current) {
      clearTimeout(clearHighlightTimeoutRef.current)
      clearHighlightTimeoutRef.current = null
    }
    ttsLog('highlight_clear', {
      lastSentence: lastHighlightSentenceRef.current,
      lastToken: lastHighlightTokenRef.current,
      readingPosition: readingPositionRef.current,
    })
    lastHighlightSentenceRef.current = null
    lastHighlightTokenRef.current = null
    readingPositionRef.current = { sentenceIndex: null, tokenIndex: null }
    setGlobalTtsHighlight(null, null)
    setCurrentReadingSentenceIndex(null)
    setCurrentReadingToken(null)
  }, [setGlobalTtsHighlight])
  const scheduleClearReadingHighlight = useCallback((delayMs = 900) => {
    if (clearHighlightTimeoutRef.current) {
      clearTimeout(clearHighlightTimeoutRef.current)
    }
    clearHighlightTimeoutRef.current = setTimeout(() => {
      clearHighlightTimeoutRef.current = null
      clearReadingHighlight()
    }, delayMs)
  }, [clearReadingHighlight])

  const isReadingRef = useRef(false)
  const playGenerationRef = useRef(0)
  const getSentenceTextRef = useRef(getSentenceText)
  getSentenceTextRef.current = getSentenceText
  const sentenceSegmentsCacheRef = useRef(new Map())

  useEffect(() => {
    const source = Array.isArray(sentences) ? sentences : []
    if (source.length === 0) {
      sentenceSegmentsCacheRef.current.clear()
      return
    }
    let cancelled = false
    let index = 0
    const run = () => {
      if (cancelled) return
      const sliceCount = 4
      const end = Math.min(index + sliceCount, source.length)
      for (let i = index; i < end; i++) {
        const s = source[i]
        const sid = s?.sentence_id ?? s?.id ?? i
        const payload = buildTtsPayloadFromSentence(s, getSentenceTextRef.current)
        const sentenceText = payload.text
        if (!sentenceText || !sentenceText.trim()) continue
        sentenceSegmentsCacheRef.current.set(sid, {
          text: sentenceText,
          tokenOffsets: payload.tokenOffsets,
          normal: splitSentenceTextForTts(sentenceText, 110),
          online: splitSentenceTextForTts(sentenceText, 80),
        })
      }
      index = end
      if (index < source.length) {
        setTimeout(run, 0)
      }
    }
    setTimeout(run, 0)
    return () => {
      cancelled = true
    }
  }, [sentences])

  // 已由下方统一同步器负责高亮恢复，避免多个恢复通道互相覆盖。

  useEffect(() => {
    if (typeof window === 'undefined') return
    const restore = window.__ARTICLE_TTS_HIGHLIGHT__
    if (window.__ARTICLE_TTS_ACTIVE__ && restore && restore.sentenceIndex !== undefined && restore.sentenceIndex !== null) {
      applyReadingHighlight(restore.sentenceIndex, restore.tokenIndex)
    }
  }, [applyReadingHighlight])

  useEffect(() => {
    const id = window.setInterval(() => {
      if (!isReadingRef.current) return
      const pos = readingPositionRef.current
      if (pos.sentenceIndex === null || pos.sentenceIndex === undefined) return
      ttsLog('highlight_sync_tick', {
        sentenceIndex: pos.sentenceIndex,
        tokenIndex: pos.tokenIndex,
        currentReadingSentenceIndex: currentReadingSentenceIndexRef.current,
        currentReadingToken: currentReadingTokenRef.current,
      })
      const nextTokenIndex = typeof pos.tokenIndex === 'number' ? pos.tokenIndex : null
      const currentSentence = currentReadingSentenceIndexRef.current
      const currentToken = currentReadingTokenRef.current?.tokenIndex ?? null
      if (currentSentence !== pos.sentenceIndex || currentToken !== nextTokenIndex) {
        applyReadingHighlight(pos.sentenceIndex, nextTokenIndex)
      }
    }, 120)
    return () => window.clearInterval(id)
  }, [applyReadingHighlight])

  useEffect(() => {
    const id = window.setInterval(() => {
      if (typeof window === 'undefined') return
      if (!window.__ARTICLE_TTS_ACTIVE__) return
      const g = window.__ARTICLE_TTS_HIGHLIGHT__
      if (!g || g.sentenceIndex === null || g.sentenceIndex === undefined) return
      const currentSentence = currentReadingSentenceIndexRef.current
      const currentToken = currentReadingTokenRef.current?.tokenIndex ?? null
      const nextToken = typeof g.tokenIndex === 'number' ? g.tokenIndex : null
      if (currentSentence === g.sentenceIndex && currentToken === nextToken) return
      applyReadingHighlight(g.sentenceIndex, g.tokenIndex)
    }, 120)
    return () => window.clearInterval(id)
  }, [applyReadingHighlight])

  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return
    const id = window.setInterval(() => {
      try {
        const syn = window.speechSynthesis
        if (isReadingRef.current && syn.paused) {
          syn.resume()
        }
      } catch {
        /* ignore */
      }
    }, 250)
    return () => window.clearInterval(id)
  }, [])

  useEffect(() => {
    return () => {
      if (clearHighlightTimeoutRef.current) {
        clearTimeout(clearHighlightTimeoutRef.current)
        clearHighlightTimeoutRef.current = null
      }
      // 注意：不要在组件卸载时自动 cancel。
      // 选词/选句会触发 ArticleViewer 临时 remount，自动 cancel 会中断正在进行的整句朗读。
      // 朗读停止由显式 stop、会话结束和异常处理路径负责。
    }
  }, [])

  useEffect(() => {
    if (typeof document === 'undefined') return
    const onVisibilityChange = () => {
      if (!document.hidden) return
      if (!isReadingRef.current) return
      setPhase('stopping')
      playGenerationRef.current += 1
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
      isReadingRef.current = false
      setPhase('idle')
      clearReadingHighlight()
    }
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => document.removeEventListener('visibilitychange', onVisibilityChange)
  }, [setPhase, clearReadingHighlight])

  const scrollSentenceIntoView = useCallback((sentenceIndex) => {
    const root = scrollContainerRef?.current
    if (!root) return
    const el = root.querySelector(`[data-sentence-index="${sentenceIndex}"]`)
    el?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [scrollContainerRef])

  const handleReadAloud = useCallback(async () => {
    if (isReadingRef.current) {
      ttsLog('stop_clicked')
      setPhase('stopping')
      playGenerationRef.current += 1
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
      isReadingRef.current = false
      setGlobalTtsActive(false)
      setPhase('idle')
      clearReadingHighlight()
      return
    }

    if (!speechSupported) {
      ttsWarn('speech_not_supported')
      window.alert?.('您的浏览器不支持语音合成功能')
      return
    }

    const sentences = sentencesRef.current || []
    if (sentences.length === 0) {
      ttsWarn('no_readable_sentences')
      window.alert?.(t('没有可朗读的内容'))
      return
    }

    const playId = ++playGenerationRef.current
    ttsLog('play_session_start', { playId, totalSentences: sentences.length })
    isReadingRef.current = true
    setGlobalTtsActive(true)
    setPhase('playing')

    const shouldAbort = () => playGenerationRef.current !== playId || !isReadingRef.current

    await ensureVoicesLoaded()
    if (shouldAbort()) {
      ttsLog('play_aborted_after_voice_load', { playId })
      isReadingRef.current = false
      setGlobalTtsActive(false)
      setPhase('idle')
      clearReadingHighlight()
      return
    }

    const startIdx = resolveTtsStartSentenceIndex(sentences, {
      currentSelection,
      selectedSentenceIndex,
      selectedSentenceIndexFromSelectionContext,
      activeSentenceIndex,
      selectedTokenIds,
    })
    if (startIdx === null || startIdx === undefined) {
      ttsWarn('no_sentence_selected_for_tts')
      isReadingRef.current = false
      setGlobalTtsActive(false)
      setPhase('idle')
      clearReadingHighlight()
      return
    }
    ttsLog('start_index_resolved', { playId, startIdx })

    try {
      for (let si = startIdx; si <= startIdx && si < sentences.length; si++) {
        if (shouldAbort()) break

        const sentence = sentences[si]
        const sid = sentence?.sentence_id ?? sentence?.id ?? si
        const cached = sentenceSegmentsCacheRef.current.get(sid)
        const payload = cached || buildTtsPayloadFromSentence(sentence, getSentenceTextRef.current)
        const fullText = payload.text
        if (!fullText || !fullText.trim()) continue
        ttsLog('sentence_start', {
          playId,
          sentenceIndex: si,
          sentenceId: sentence?.sentence_id ?? sentence?.id ?? null,
          textLength: fullText.length,
        })

        scrollSentenceIntoView(si)

        const bcp47 = resolveUtteranceLang(sentence, selectedLanguage, languageNameToCode, languageCodeToBCP47)
        const voice = pickVoiceForBcp47(bcp47)
        ttsLog('sentence_voice_selected', {
          playId,
          sentenceIndex: si,
          bcp47,
          voice: voice?.name || null,
          voiceLang: voice?.lang || null,
          localService: Boolean(voice?.localService),
        })

        const voiceIsOnline = isOnlineVoice(voice)
        const maxChunk = voiceIsOnline ? 80 : 110
        const selectedTokenSegments = buildSelectedTokenSpeechSegments(sentence, si, selectedTokenIds, currentSelection)
        const tokenMode = selectedTokenSegments.length > 0
        const segments =
          tokenMode
            ? selectedTokenSegments
            : (voiceIsOnline ? cached?.online : cached?.normal) || splitSentenceTextForTts(fullText, maxChunk)
        ttsLog('sentence_segments_built', { playId, sentenceIndex: si, count: segments.length })
        if (segments.length > 0) {
          if (tokenMode) {
            // Token 朗读模式下只保留整句高亮，不显示 token 级绿色高亮
            applyReadingHighlight(si, null)
          } else {
            const firstMappedTokenIdx =
              typeof segments[0]?.tokenIndex === 'number'
                ? segments[0].tokenIndex
                : mapCharOffsetToTokenIndex(payload.tokenOffsets, segments[0].charOffset)
            const firstTokenIdx =
              firstMappedTokenIdx === null && Array.isArray(sentence?.tokens) && sentence.tokens.length > 0
                ? 0
                : firstMappedTokenIdx
            applyReadingHighlight(si, firstTokenIdx)
          }
        } else {
          applyReadingHighlight(si, null)
        }
        for (let seg = 0; seg < segments.length; seg++) {
          if (shouldAbort()) break

          if (seg > 0) setPhase('betweenSentences')

          const { text: segText, charOffset, tokenIndex: segmentTokenIndex } = segments[seg]
          ttsLog('segment_start', {
            playId,
            sentenceIndex: si,
            segmentIndex: seg,
            textLength: segText.length,
            charOffset,
            preview: segText.slice(0, 80),
          })
          const mappedTokenIdx =
            typeof segmentTokenIndex === 'number'
              ? segmentTokenIndex
              : mapCharOffsetToTokenIndex(payload.tokenOffsets, charOffset)
          const tokenCount = Array.isArray(sentence?.tokens) ? sentence.tokens.length : 0
          let tokenIdx = null
          if (!tokenMode) {
            tokenIdx = mappedTokenIdx
            if (tokenCount > 0) {
              if (tokenIdx === null || tokenIdx === undefined || Number.isNaN(tokenIdx)) {
                tokenIdx = 0
              } else {
                tokenIdx = Math.min(Math.max(Number(tokenIdx), 0), tokenCount - 1)
              }
            } else {
              tokenIdx = null
            }
          }
          applyReadingHighlight(si, tokenIdx)

          if (seg > 0) setPhase('playing')

          let segmentAccepted = false
          const maxRetries = 2
          let interruptedStreak = 0
          let speakRate = 1
          for (let attempt = 0; attempt <= maxRetries; attempt++) {
            if (shouldAbort()) break
            // interrupted/retry 后强制重申高亮，避免状态被异步事件冲掉。
            applyReadingHighlight(si, tokenIdx)
            setPhase('playing')
            const idleOk = await waitForSynthIdle(shouldAbort)
            if (!idleOk && typeof window !== 'undefined' && window.speechSynthesis) {
              ttsWarn('segment_wait_idle_timeout_cancel', { playId, sentenceIndex: si, segmentIndex: seg, attempt })
              // 仅在明显卡住时再强制清队列，降低自触发 interrupted 的概率。
              window.speechSynthesis.cancel()
              await new Promise((r) => setTimeout(r, 60))
            }
            const result = await speakUtterance(
              segText,
              bcp47,
              voice,
              shouldAbort,
              speakRate,
              (boundaryCharIndex) => {
                if (tokenMode) return
                const liveTokenIdx = mapCharOffsetToTokenIndex(
                  payload.tokenOffsets,
                  charOffset + boundaryCharIndex
                )
                if (typeof liveTokenIdx === 'number') {
                  applyReadingHighlight(si, liveTokenIdx)
                }
              }
            )
            ttsLog('segment_result', {
              playId,
              sentenceIndex: si,
              segmentIndex: seg,
              attempt,
              rate: speakRate,
              status: result.status,
              utteranceDidStart: Boolean(result?.utteranceDidStart),
              error: result?.error?.error || null,
              message: result?.error?.message || null,
              highlightState: {
                readingPosition: readingPositionRef.current,
                currentReadingSentenceIndex: currentReadingSentenceIndexRef.current,
                currentReadingToken: currentReadingTokenRef.current,
              },
            })
            // 保守模式：仅 onend 认为该段完成，才允许推进。
            if (result.status === 'ended') {
              segmentAccepted = true
              interruptedStreak = 0
              speakRate = 1
              ttsLog('segment_accepted', { playId, sentenceIndex: si, segmentIndex: seg, attempt })
              break
            }
            if (result.status === 'aborted') {
              ttsLog('segment_aborted', { playId, sentenceIndex: si, segmentIndex: seg, attempt })
              break
            }
            if (result.status === 'interrupted_after_start') {
              interruptedStreak += 1
              if (voiceIsOnline && interruptedStreak >= 1) {
                speakRate = Math.max(0.8, 1 - 0.1 * interruptedStreak)
              }
            }
            if (attempt < maxRetries) {
              const retryDelay = voiceIsOnline ? (attempt + 1) * 300 : 100
              ttsWarn('segment_retry_scheduled', { playId, sentenceIndex: si, segmentIndex: seg, attempt, retryDelay, nextRate: speakRate })
              // 失败后先等待自然恢复；仅在引擎仍忙时才 cancel，避免频繁人为 interrupted。
              await new Promise((r) => setTimeout(r, retryDelay))
              applyReadingHighlight(si, tokenIdx)
              if (typeof window !== 'undefined' && window.speechSynthesis) {
                const syn = window.speechSynthesis
                if (syn.speaking || syn.pending) {
                  window.speechSynthesis.cancel()
                  await new Promise((r) => setTimeout(r, 60))
                }
              }
            }
          }

          if (shouldAbort()) break
          if (!segmentAccepted) {
            // 保守模式下主段失败：再细分为更短子段（仍仅 onend 才推进），尽量避免整篇中止。
            const fallbackSegments = splitSentenceTextForTts(segText, 80)
            ttsWarn('segment_fallback_split', {
              playId,
              sentenceIndex: si,
              segmentIndex: seg,
              fallbackCount: fallbackSegments.length,
            })
            let fallbackAccepted = true
            for (let f = 0; f < fallbackSegments.length; f++) {
              if (shouldAbort()) {
                fallbackAccepted = false
                break
              }
              const childText = fallbackSegments[f]?.text || ''
              if (!childText.trim()) continue
              let childOk = false
              for (let attempt = 0; attempt <= 1; attempt++) {
                if (shouldAbort()) break
                await waitForSynthIdle(shouldAbort)
                const childResult = await speakUtterance(
                  childText,
                  bcp47,
                  voice,
                  shouldAbort,
                  1,
                  (boundaryCharIndex) => {
                    if (tokenMode) return
                    const liveTokenIdx = mapCharOffsetToTokenIndex(
                      payload.tokenOffsets,
                      charOffset + boundaryCharIndex
                    )
                    if (typeof liveTokenIdx === 'number') {
                      applyReadingHighlight(si, liveTokenIdx)
                    }
                  }
                )
                ttsLog('fallback_segment_result', {
                  playId,
                  sentenceIndex: si,
                  segmentIndex: seg,
                  fallbackIndex: f,
                  attempt,
                  status: childResult.status,
                  utteranceDidStart: Boolean(childResult?.utteranceDidStart),
                  error: childResult?.error?.error || null,
                  message: childResult?.error?.message || null,
                })
                if (childResult.status === 'ended') {
                  childOk = true
                  break
                }
                if (childResult.status === 'aborted') break
                if (attempt < 1) {
                  await new Promise((r) => setTimeout(r, 80))
                }
              }
              if (!childOk) {
                ttsWarn('fallback_segment_failed', {
                  playId,
                  sentenceIndex: si,
                  segmentIndex: seg,
                  fallbackIndex: f,
                })
                fallbackAccepted = false
                break
              }
            }

            if (!fallbackAccepted) {
              throw new Error('tts_segment_not_completed')
            }
          }

          if (!shouldAbort() && voiceIsOnline) {
            await new Promise((r) => setTimeout(r, 80))
          }
        }
        ttsLog('sentence_completed', { playId, sentenceIndex: si })
      }
    } catch (err) {
      if (!shouldAbort()) {
        ttsWarn('stop_reading_due_to_incomplete_segment', { playId, error: err?.message || String(err) })
        if (typeof window !== 'undefined' && window.speechSynthesis) {
          window.speechSynthesis.cancel()
        }
      }
    } finally {
      if (playGenerationRef.current === playId) {
        ttsLog('play_session_end', { playId })
        isReadingRef.current = false
        setGlobalTtsActive(false)
        setPhase('idle')
        // 自然结束时稍作停留，避免视觉上“刚重试成功就瞬间丢高亮”。
        scheduleClearReadingHighlight(900)
      }
    }
  }, [
    speechSupported,
    t,
    sentencesRef,
    currentSelection,
    selectedSentenceIndex,
    selectedSentenceIndexFromSelectionContext,
    activeSentenceIndex,
    selectedTokenIds,
    selectedLanguage,
    languageNameToCode,
    languageCodeToBCP47,
    setPhase,
    scrollSentenceIntoView,
    applyReadingHighlight,
    clearReadingHighlight,
    scheduleClearReadingHighlight,
    setGlobalTtsActive,
  ])

  return {
    ttsPhase,
    ttsUiReading,
    speechSupported,
    handleReadAloud,
    currentReadingToken,
    currentReadingSentenceIndex,
  }
}
