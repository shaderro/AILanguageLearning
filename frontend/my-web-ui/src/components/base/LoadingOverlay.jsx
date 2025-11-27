import { colors } from '../../design-tokens';
import { cx, mergeStyle } from './utils/classNames';
import { BaseSpinner } from './BaseSpinner';

const variantTokens = {
  light: {
    '--overlay-bg': 'rgba(255,255,255,0.8)',
    '--overlay-text': colors.gray[700],
  },
  dark: {
    '--overlay-bg': 'rgba(15,23,42,0.7)',
    '--overlay-text': '#f8fafc',
  },
};

export function LoadingOverlay({
  isActive,
  children,
  text = '加载中...',
  fullScreen = false,
  variant = 'light',
  className,
  style,
}) {
  const activeVariant = variantTokens[variant] ? variant : 'light';
  const mergedStyle = mergeStyle(variantTokens[activeVariant], style);

  return (
    <div className={cx(fullScreen ? 'relative' : 'relative', className)} style={mergedStyle}>
      {children}
      {isActive && (
        <div
          className={cx(
            fullScreen ? 'fixed inset-0 z-50' : 'absolute inset-0 z-40',
            'flex items-center justify-center bg-[var(--overlay-bg)] backdrop-blur-sm',
          )}
        >
          <BaseSpinner
            label={text}
            variant={activeVariant === 'dark' ? 'neutral' : 'primary'}
            className="border-[var(--overlay-text)]/40 border-t-[var(--overlay-text)]"
          />
        </div>
      )}
    </div>
  );
}

