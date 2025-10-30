import { createContext, useCallback, useMemo, useState } from 'react'

export const SelectionContext = createContext(null)

export function SelectionProvider({ children }) {
  const [currentSelection, setCurrentSelection] = useState(null)
  const [hoverState, setHoverState] = useState(null)

  const clearSelection = useCallback(() => setCurrentSelection(null), [])
  const clearHover = useCallback(() => setHoverState(null), [])

  const selectToken = useCallback((textId, sentenceId, tokenId) => {
    setCurrentSelection(prev => {
      // 无选择 → 新建单 token 选择
      if (!prev) return { type: 'token', textId, sentenceId, tokenIds: [tokenId] }

      // 跨句/跨文 → 清空并以当前 token 开始
      if (prev.textId !== textId || prev.sentenceId !== sentenceId) {
        return { type: 'token', textId, sentenceId, tokenIds: [tokenId] }
      }

      // 同句：
      if (prev.type === 'sentence') {
        // 整句 → 降级为 token 选择，从该 token 开始
        return { type: 'token', textId, sentenceId, tokenIds: [tokenId] }
      }

      // 同句 token 多选：点击切换（存在则移除，不存在则添加）
      const set = new Set(prev.tokenIds || [])
      if (set.has(tokenId)) {
        set.delete(tokenId)
      } else {
        set.add(tokenId)
      }
      const next = Array.from(set)
      if (next.length === 0) return null // 全部取消则清空选择
      return { type: 'token', textId, sentenceId, tokenIds: next }
    })
  }, [])

  const selectTokens = useCallback((textId, sentenceId, tokenIds) => {
    setCurrentSelection({ type: 'token', textId, sentenceId, tokenIds: Array.from(new Set(tokenIds)) })
  }, [])

  const selectSentence = useCallback((textId, sentenceId) => {
    setCurrentSelection(prev => {
      // 跨句/无选择 → 直接整句选择
      if (!prev || prev.textId !== textId || prev.sentenceId !== sentenceId) {
        return { type: 'sentence', textId, sentenceId }
      }
      // 同句 token 多选 → 升级为整句
      return { type: 'sentence', textId, sentenceId }
    })
  }, [])

  const setHoverToken = useCallback((textId, sentenceId, tokenId) => {
    setHoverState({ type: 'token', textId, sentenceId, tokenId })
  }, [])

  const setHoverSentence = useCallback((textId, sentenceId) => {
    setHoverState({ type: 'sentence', textId, sentenceId })
  }, [])

  const value = useMemo(() => ({
    currentSelection,
    hoverState,
    // actions
    selectToken,
    selectTokens,
    selectSentence,
    clearSelection,
    setHoverToken,
    setHoverSentence,
    clearHover,
  }), [currentSelection, hoverState, selectToken, selectTokens, selectSentence, clearSelection, setHoverToken, setHoverSentence, clearHover])

  return (
    <SelectionContext.Provider value={value}>
      {children}
    </SelectionContext.Provider>
  )
}


