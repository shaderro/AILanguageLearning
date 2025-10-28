import { useState, useRef } from 'react'

/**
 * Custom hook to manage sentence-level interaction states (hover, click)
 */
export function useSentenceInteraction() {
  const [hoveredSentenceIndex, setHoveredSentenceIndex] = useState(null)
  const [clickedSentenceIndex, setClickedSentenceIndex] = useState(null)
  const [selectedSentenceIndex, setSelectedSentenceIndex] = useState(null)
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
    // 切换句子选择状态
    if (selectedSentenceIndex === sentenceIndex) {
      setSelectedSentenceIndex(null) // 取消选择
    } else {
      setSelectedSentenceIndex(sentenceIndex) // 选择句子
    }
  }

  /**
   * Clear sentence interaction states
   */
  const clearSentenceInteraction = () => {
    setHoveredSentenceIndex(null)
    setClickedSentenceIndex(null)
    setSelectedSentenceIndex(null)
  }

  /**
   * Clear only sentence selection (keep hover/click states)
   */
  const clearSentenceSelection = () => {
    setSelectedSentenceIndex(null)
  }

  /**
   * Get sentence background style based on interaction state
   * @param {number} sentenceIndex - Index of the sentence
   * @returns {string} CSS classes for background styling
   */
  const getSentenceBackgroundStyle = (sentenceIndex) => {
    const isHovered = hoveredSentenceIndex === sentenceIndex
    const isClicked = clickedSentenceIndex === sentenceIndex
    const isSelected = selectedSentenceIndex === sentenceIndex

    if (isSelected) {
      return 'bg-blue-100 border border-blue-300 rounded-md' // 选中的句子用蓝色背景
    } else if (isClicked) {
      return 'bg-gray-200 border border-gray-400 rounded-md'
    } else if (isHovered) {
      return 'bg-gray-100 rounded-md'
    }
    
    return ''
  }

  /**
   * Check if a sentence is in any interaction state
   * @param {number} sentenceIndex - Index of the sentence
   * @returns {boolean} Whether the sentence is hovered, clicked, or selected
   */
  const isSentenceInteracting = (sentenceIndex) => {
    return hoveredSentenceIndex === sentenceIndex || clickedSentenceIndex === sentenceIndex || selectedSentenceIndex === sentenceIndex
  }

  /**
   * Check if a sentence is selected
   * @param {number} sentenceIndex - Index of the sentence
   * @returns {boolean} Whether the sentence is selected
   */
  const isSentenceSelected = (sentenceIndex) => {
    return selectedSentenceIndex === sentenceIndex
  }

  return {
    hoveredSentenceIndex,
    clickedSentenceIndex,
    selectedSentenceIndex,
    sentenceRefs,
    handleSentenceMouseEnter,
    handleSentenceMouseLeave,
    handleSentenceClick,
    clearSentenceInteraction,
    clearSentenceSelection,
    getSentenceBackgroundStyle,
    isSentenceInteracting,
    isSentenceSelected
  }
}
