import { colors } from '../../design-tokens';
import { cx, mergeStyle } from './utils/classNames';

const sizeMap = {
  sm: 'h-4 w-4 border-2',
  md: 'h-6 w-6 border-2',
  lg: 'h-8 w-8 border-4',
};

const variantTokens = {
  primary: {
    '--spinner-border': colors.primary[100],
    '--spinner-top': colors.primary[600],
  },
  neutral: {
    '--spinner-border': colors.gray[200],
    '--spinner-top': colors.gray[500],
  },
  success: {
    '--spinner-border': colors.success[100],
    '--spinner-top': colors.success[500],
  },
};

export function BaseSpinner({
  size = 'md',
  variant = 'primary',
  className,
  style,
  label = '加载中...',
  ...rest
}) {
  const activeSize = sizeMap[size] ? size : 'md';
  const activeVariant = variantTokens[variant] ? variant : 'primary';
  const mergedStyle = mergeStyle(variantTokens[activeVariant], style);

  return (
    <span
      role="status"
      aria-live="polite"
      className="inline-flex items-center gap-2 text-sm text-gray-600"
      {...rest}
    >
      <span
        className={cx(
          'inline-block animate-spin rounded-full border-solid border-[var(--spinner-border)] border-t-[var(--spinner-top)]',
          sizeMap[activeSize],
          className,
        )}
        style={mergedStyle}
      />
      {label && <span>{label}</span>}
    </span>
  );
}

