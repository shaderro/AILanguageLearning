import { useState, useRef } from 'react'

/**
 * Custom hook to manage sentence-level interaction states (hover, click)
 */
export function useSentenceInteraction() {
  const [hoveredSentenceIndex, setHoveredSentenceIndex] = useState(null)
  const [clickedSentenceIndex, setClickedSentenceIndex] = useState(null)
  const sentenceRefs = useRef({})

  /**
   * Handle mouse enter on sentence area
   * @param {number} sentenceIndex - Index of the sentence
   */
  const handleSentenceMouseEnter = (sentenceIndex) => {
    setHoveredSentenceIndex(sentenceIndex)
  }

  /**
   * Handle mouse leave on sentence area
   */
  const handleSentenceMouseLeave = () => {
    setHoveredSentenceIndex(null)
  }

  /**
   * Handle click on sentence area (not on specific token)
   * @param {number} sentenceIndex - Index of the sentence
   */
  const handleSentenceClick = (sentenceIndex) => {
    setClickedSentenceIndex(sentenceIndex)
  }

  /**
   * Clear sentence interaction states
   */
  const clearSentenceInteraction = () => {
    setHoveredSentenceIndex(null)
    setClickedSentenceIndex(null)
  }

  /**
   * Get sentence background style based on interaction state
   * @param {number} sentenceIndex - Index of the sentence
   * @returns {string} CSS classes for background styling
   */
  const getSentenceBackgroundStyle = (sentenceIndex) => {
    const isHovered = hoveredSentenceIndex === sentenceIndex
    const isClicked = clickedSentenceIndex === sentenceIndex

    if (isClicked) {
      return 'bg-gray-200 border border-gray-400 rounded-md'
    } else if (isHovered) {
      return 'bg-gray-100 rounded-md'
    }
    
    return ''
  }

  /**
   * Check if a sentence is in any interaction state
   * @param {number} sentenceIndex - Index of the sentence
   * @returns {boolean} Whether the sentence is hovered or clicked
   */
  const isSentenceInteracting = (sentenceIndex) => {
    return hoveredSentenceIndex === sentenceIndex || clickedSentenceIndex === sentenceIndex
  }

  return {
    hoveredSentenceIndex,
    clickedSentenceIndex,
    sentenceRefs,
    handleSentenceMouseEnter,
    handleSentenceMouseLeave,
    handleSentenceClick,
    clearSentenceInteraction,
    getSentenceBackgroundStyle,
    isSentenceInteracting
  }
}
