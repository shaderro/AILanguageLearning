/**
 * Design Tokens - 设计令牌系统
 * 统一管理颜色、间距、圆角、字体等设计变量
 */

export const tokens = {
  // 颜色
  colors: {
    // 主色（蓝色）
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',  // 主要使用
      600: '#2563eb',  // hover 状态
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },
    
    // 成功色（绿色）
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',  // 主要使用
      700: '#15803d',
      800: '#166534',
      900: '#14532d',
    },
    
    // 警告色（黄色）
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f',
    },
    
    // 危险色（红色）
    danger: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',  // 主要使用
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d',
    },
    
    // 灰色
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',  // 背景色
      200: '#e5e7eb',  // 边框色
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',  // 次要文本
      600: '#4b5563',  // 正文
      700: '#374151',  // 标题
      800: '#1f2937',
      900: '#111827',  // 主要文本
    },
    
    // 语义化颜色（快捷访问）
    semantic: {
      text: {
        primary: '#111827',      // gray-900
        secondary: '#6b7280',    // gray-500
        tertiary: '#9ca3af',     // gray-400
        disabled: '#d1d5db',     // gray-300
      },
      bg: {
        primary: '#ffffff',
        secondary: '#f9fafb',    // gray-50
        tertiary: '#f3f4f6',     // gray-100
      },
      border: {
        default: '#e5e7eb',      // gray-200
        hover: '#d1d5db',        // gray-300
        focus: '#3b82f6',        // primary-500
      },
    },
  },
  
  // 间距（基于 4px 网格）
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
    '3xl': '4rem',   // 64px
  },
  
  // 圆角
  radius: {
    none: '0',
    sm: '0.25rem',   // 4px
    md: '0.375rem',  // 6px
    lg: '0.5rem',    // 8px
    xl: '0.75rem',   // 12px
    '2xl': '1rem',   // 16px
    full: '9999px',
  },
  
  // 字体大小
  fontSize: {
    xs: '0.75rem',   // 12px
    sm: '0.875rem',  // 14px
    base: '1rem',    // 16px
    lg: '1.125rem',  // 18px
    xl: '1.25rem',   // 20px
    '2xl': '1.5rem', // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
  },
  
  // 字体粗细
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  
  // 行高
  lineHeight: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },
  
  // 阴影
  shadow: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
  
  // 过渡时间
  transition: {
    fast: '150ms',
    base: '200ms',
    slow: '300ms',
  },
  
  // Z-index 层级
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
  },
  
  // 断点（响应式）
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
}

// 导出常用快捷方式
export const colors = tokens.colors
export const spacing = tokens.spacing
export const radius = tokens.radius
export const fontSize = tokens.fontSize
export const fontWeight = tokens.fontWeight
export const lineHeight = tokens.lineHeight
export const shadow = tokens.shadow
export const transition = tokens.transition
export const zIndex = tokens.zIndex
export const breakpoints = tokens.breakpoints

// 导出默认值
export default tokens

