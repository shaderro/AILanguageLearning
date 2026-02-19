import React from 'react'
import { componentTokens } from '../../design-tokens/design-tokens'
import { useUIText } from '../../i18n/useUIText'

/**
 * 统一的返回按钮组件
 * 样式：黑色圆角细边框、灰色底、黑色字
 */
const BackButton = ({ 
  onClick, 
  className = '', 
  children,
  ariaLabel,
  ...props 
}) => {
  const t = useUIText()
  const backButtonStyles = componentTokens.backButton
  
  const defaultClassName = 'inline-flex items-center justify-center transition-colors'
  const combinedClassName = `${defaultClassName} ${className}`.trim()
  
  const style = {
    backgroundColor: backButtonStyles.background,
    color: backButtonStyles.text,
    border: `${backButtonStyles.borderWidth} solid ${backButtonStyles.border}`,
    borderRadius: backButtonStyles.radius,
    paddingLeft: backButtonStyles.paddingX,
    paddingRight: backButtonStyles.paddingX,
    paddingTop: backButtonStyles.paddingY,
    paddingBottom: backButtonStyles.paddingY,
    fontSize: backButtonStyles.fontSize,
    fontWeight: backButtonStyles.fontWeight,
    transition: backButtonStyles.transition,
  }
  
  const hoverStyle = {
    backgroundColor: backButtonStyles.backgroundHover,
  }
  
  return (
    <button
      onClick={onClick}
      className={combinedClassName}
      style={style}
      onMouseEnter={(e) => {
        Object.assign(e.currentTarget.style, hoverStyle)
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = backButtonStyles.background
      }}
      aria-label={ariaLabel || t('返回')}
      {...props}
    >
      {children || t('返回')}
    </button>
  )
}

export default BackButton

