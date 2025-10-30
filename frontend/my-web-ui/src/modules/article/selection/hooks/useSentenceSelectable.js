import { useMemo, useCallback } from 'react'
import { useSelection } from './useSelection'

export function useSentenceSelectable({ textId, sentenceId }) {
  const { currentSelection, hoverState, setHoverSentence, clearHover, selectSentence } = useSelection()

  const isHovered = !!hoverState && hoverState.type === 'sentence' && hoverState.textId === textId && hoverState.sentenceId === sentenceId
  const isSelected = !!currentSelection && currentSelection.type === 'sentence' && currentSelection.textId === textId && currentSelection.sentenceId === sentenceId
  const isTokenSelectedInSentence = !!currentSelection && currentSelection.type === 'token' && currentSelection.textId === textId && currentSelection.sentenceId === sentenceId

  const className = useMemo(() => {
    if (isSelected) return 'bg-gray-100 border border-gray-300 rounded-md'
    if (isTokenSelectedInSentence) return 'border border-gray-300 rounded-md'
    if (isHovered) return 'bg-gray-100'
    return ''
  }, [isHovered, isSelected, isTokenSelectedInSentence])

  const onMouseEnter = useCallback(() => setHoverSentence(textId, sentenceId), [setHoverSentence, textId, sentenceId])
  const onMouseLeave = useCallback(() => clearHover(), [clearHover])
  const onClick = useCallback(() => selectSentence(textId, sentenceId), [selectSentence, textId, sentenceId])

  return { isHovered, isSelected, isTokenSelectedInSentence, className, onMouseEnter, onMouseLeave, onClick }
}


