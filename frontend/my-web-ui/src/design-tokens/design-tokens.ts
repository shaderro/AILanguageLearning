/**
 * Auto-generated design tokens collected from the existing Tailwind UI.
 * 请先确认这些 token，再进行全局样式改造。
 */

export const designTokens = {
  color: {
    primary: {
      surface: '#14b8a6', // teal-500
      hover: '#0d9488', // teal-600
      subtle: '#ccfbf1', // teal-100
      foreground: '#ffffff',
    },
    success: {
      surface: '#22c55e', // bg-green-500
      hover: '#16a34a', // hover:bg-green-600
      subtle: '#dcfce7',
      foreground: '#ffffff',
    },
    warning: {
      surface: '#f59e0b',
      hover: '#d97706',
      subtle: '#fef3c7',
      foreground: '#78350f',
    },
    danger: {
      surface: '#ef4444',
      hover: '#dc2626',
      subtle: '#fee2e2',
      foreground: '#7f1d1d',
    },
    neutral: {
      canvas: '#f3f4f6', // page background
      surface: '#ffffff',
      border: '#e5e7eb',
      borderStrong: '#d1d5db',
    },
    text: {
      primary: '#111827',
      secondary: '#374151',
      muted: '#6b7280',
      placeholder: '#9ca3af',
      inverted: '#ffffff',
    },
    state: {
      info: '#0ea5e9',
      accent: '#7c3aed',
      badgeBg: 'rgba(255, 255, 255, 0.8)',
    },
    shadow: {
      soft: 'rgba(0, 0, 0, 0.05)',
      medium: 'rgba(0, 0, 0, 0.1)',
      overlay: 'rgba(15, 23, 42, 0.45)',
    },
  },
  font: {
    family: "'Inter', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif",
    size: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
    },
    weight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.25,
      comfy: 1.4,
      normal: 1.5,
      relaxed: 1.75,
    },
  },
  radius: {
    none: '0px',
    sm: '4px', // rounded-sm
    md: '6px', // rounded-md
    lg: '12px', // rounded-lg
    pill: '9999px', // rounded-full
  },
  space: {
    '0': '0px',
    '1': '0.25rem', // 4px
    '2': '0.5rem', // 8px
    '3': '0.75rem', // 12px
    '4': '1rem', // 16px
    '5': '1.25rem', // 20px
    '6': '1.5rem', // 24px
    '8': '2rem', // 32px
    '10': '2.5rem', // 40px
  },
  shadow: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px rgba(15, 23, 42, 0.1)',
    lg: '0 10px 15px rgba(15, 23, 42, 0.12)',
    xl: '0 20px 25px rgba(15, 23, 42, 0.18)',
  },
} as const

export const componentTokens = {
  text: {
    cardNote: {
      fontSize: designTokens.font.size.xs,
      color: designTokens.color.primary.hover,
      lineHeight: designTokens.font.lineHeight.comfy,
      fontWeight: designTokens.font.weight.medium,
    },
  },
  card: {
    background: designTokens.color.neutral.surface,
    padding: designTokens.space['6'],
    radius: designTokens.radius.lg,
    shadow: {
      default: designTokens.shadow.md,
      hover: designTokens.shadow.lg,
    },
    border: designTokens.color.neutral.border,
  },
  button: {
    sizes: {
      sm: { px: designTokens.space['3'], py: designTokens.space['2'], radius: designTokens.radius.md },
      md: { px: designTokens.space['4'], py: designTokens.space['2'], radius: designTokens.radius.md },
      lg: { px: designTokens.space['6'], py: designTokens.space['3'], radius: designTokens.radius.pill },
    },
    variants: {
      primary: {
        bg: designTokens.color.primary.surface,
        hover: designTokens.color.primary.hover,
        text: designTokens.color.primary.foreground,
      },
      secondary: {
        bg: '#e5e7eb',
        hover: '#d1d5db',
        text: designTokens.color.text.secondary,
      },
      danger: {
        bg: designTokens.color.danger.surface,
        hover: designTokens.color.danger.hover,
        text: designTokens.color.primary.foreground,
      },
      ghost: {
        bg: 'transparent',
        hover: 'rgba(59, 130, 246, 0.08)',
        text: designTokens.color.primary.surface,
      },
    },
    font: {
      size: designTokens.font.size.base,
      weight: designTokens.font.weight.medium,
      lineHeight: designTokens.font.lineHeight.comfy,
    },
    shadow: {
      default: designTokens.shadow.sm,
      focus: `0 0 0 3px ${designTokens.color.primary.subtle}`,
    },
  },
  input: {
    background: designTokens.color.neutral.surface,
    border: designTokens.color.neutral.border,
    borderHover: designTokens.color.neutral.borderStrong,
    borderFocus: designTokens.color.primary.surface,
    radius: designTokens.radius.md,
    paddingX: designTokens.space['3'],
    paddingY: designTokens.space['2'],
    fontSize: designTokens.font.size.base,
    lineHeight: designTokens.font.lineHeight.comfy,
    shadow: designTokens.shadow.sm,
  },
  tag: {
    paddingX: designTokens.space['2'],
    paddingY: designTokens.space['1'],
    radius: designTokens.radius.pill,
    fontSize: designTokens.font.size.xs,
    fontWeight: designTokens.font.weight.medium,
    variants: {
      default: { bg: '#f3f4f6', text: designTokens.color.text.muted },
      primary: { bg: designTokens.color.primary.subtle, text: '#1d4ed8' },
      success: { bg: designTokens.color.success.subtle, text: '#15803d' },
      warning: { bg: designTokens.color.warning.subtle, text: '#b45309' },
      danger: { bg: designTokens.color.danger.subtle, text: '#b91c1c' },
    },
    shadow: designTokens.shadow.sm,
  },
  tab: {
    height: '2.5rem',
    paddingX: designTokens.space['4'],
    radius: designTokens.radius.md,
    gap: designTokens.space['4'],
    active: {
      text: designTokens.color.primary.surface,
      border: designTokens.color.primary.surface,
      bg: designTokens.color.primary.subtle,
    },
    inactive: {
      text: designTokens.color.text.muted,
      border: designTokens.color.neutral.border,
      bg: 'transparent',
    },
  },
  backButton: {
    // 🔧 统一的返回按钮样式：灰色圆角细边框、灰色底、黑色字（与卡片边框一致）
    background: '#f3f4f6', // gray-100
    backgroundHover: '#e5e7eb', // gray-200
    text: '#111827', // black/gray-900
    border: '#e5e7eb', // gray-200 (与卡片边框一致)
    borderWidth: '1px',
    radius: designTokens.radius.md, // 6px rounded-md
    paddingX: designTokens.space['4'], // 16px
    paddingY: designTokens.space['2'], // 8px
    fontSize: designTokens.font.size.sm, // 0.875rem
    fontWeight: designTokens.font.weight.normal,
    transition: 'all 0.2s ease-in-out',
  },
  grammarVocabTitle: {
    // 🔧 语法、词汇大标题样式：字号为原来的2/3，最大宽度为原来的2/3，允许换行
    fontSize: designTokens.font.size['2xl'], // 1.5rem (text-4xl 是 2.25rem，2/3 约为 1.5rem)
    fontWeight: designTokens.font.weight.bold,
    color: designTokens.color.text.primary, // 保持字体颜色不变
    lineHeight: designTokens.font.lineHeight.tight,
    maxWidth: '66.67%', // 最大宽度为原来的2/3
    textAlign: 'center' as const,
    wordWrap: 'break-word' as const,
    overflowWrap: 'break-word' as const,
  },
} as const

export type DesignTokens = typeof designTokens
export type ComponentTokens = typeof componentTokens

export default {
  designTokens,
  componentTokens,
}

