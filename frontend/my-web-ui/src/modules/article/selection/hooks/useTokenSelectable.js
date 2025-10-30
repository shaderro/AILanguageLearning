import { useMemo, useCallback } from 'react'
import { useSelection } from './useSelection'

export function useTokenSelectable({ textId, sentenceId, tokenId }) {
  const { currentSelection, hoverState, setHoverToken, clearHover, selectToken } = useSelection()

  const isHovered = !!hoverState && hoverState.type === 'token' && hoverState.textId === textId && hoverState.sentenceId === sentenceId && hoverState.tokenId === tokenId
  const isSelected = !!currentSelection && currentSelection.type === 'token' && currentSelection.textId === textId && currentSelection.sentenceId === sentenceId && Array.isArray(currentSelection.tokenIds) && currentSelection.tokenIds.includes(tokenId)

  const className = useMemo(() => {
    if (isSelected) return 'bg-yellow-300'
    if (isHovered) return 'bg-yellow-200'
    return ''
  }, [isHovered, isSelected])

  const onMouseEnter = useCallback(() => setHoverToken(textId, sentenceId, tokenId), [setHoverToken, textId, sentenceId, tokenId])
  const onMouseLeave = useCallback(() => clearHover(), [clearHover])
  const onClick = useCallback(() => selectToken(textId, sentenceId, tokenId), [selectToken, textId, sentenceId, tokenId])

  return { isHovered, isSelected, className, onMouseEnter, onMouseLeave, onClick }
}


