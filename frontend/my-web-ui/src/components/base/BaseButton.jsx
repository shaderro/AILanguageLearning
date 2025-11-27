import { forwardRef } from 'react';
import { colors } from '../../design-tokens';
import { cx, mergeStyle } from './utils/classNames';

const sizeClasses = {
  sm: 'text-sm px-3 py-1.5',
  md: 'text-sm px-4 py-2.5',
  lg: 'text-base px-5 py-3',
};

const variantClasses = {
  primary:
    'font-semibold text-[var(--btn-text)] bg-[var(--btn-bg)] hover:bg-[var(--btn-bg-hover)] focus-visible:ring-[var(--btn-ring)] shadow-sm',
  secondary:
    'text-[var(--btn-text)] bg-[var(--btn-bg)] hover:bg-[var(--btn-bg-hover)] border border-[var(--btn-border)] focus-visible:ring-[var(--btn-ring)]',
  ghost:
    'text-[var(--btn-text)] bg-transparent hover:bg-[var(--btn-bg-hover)] focus-visible:ring-[var(--btn-ring)]',
  danger:
    'text-[var(--btn-text)] bg-[var(--btn-bg)] hover:bg-[var(--btn-bg-hover)] focus-visible:ring-[var(--btn-ring)] shadow-sm',
  link: 'text-[var(--btn-text)] underline-offset-4 hover:underline focus-visible:ring-[var(--btn-ring)] bg-transparent',
};

const variantTokens = {
  primary: {
    '--btn-bg': colors.primary[600],
    '--btn-bg-hover': colors.primary[700],
    '--btn-ring': colors.primary[300],
    '--btn-text': '#ffffff',
    '--btn-spinner': '#ffffff',
  },
  secondary: {
    '--btn-bg': colors.semantic?.bg?.secondary ?? colors.gray[50],
    '--btn-bg-hover': colors.gray[200],
    '--btn-ring': colors.primary[200],
    '--btn-border': colors.semantic?.border?.default ?? colors.gray[200],
    '--btn-text': colors.semantic?.text?.primary ?? colors.gray[900],
    '--btn-spinner': colors.primary[600],
  },
  ghost: {
    '--btn-bg-hover': colors.gray[100],
    '--btn-ring': colors.primary[200],
    '--btn-text': colors.primary[600],
    '--btn-spinner': colors.primary[600],
  },
  danger: {
    '--btn-bg': colors.danger[600],
    '--btn-bg-hover': colors.danger[700],
    '--btn-ring': colors.danger[300],
    '--btn-text': '#ffffff',
    '--btn-spinner': '#ffffff',
  },
  link: {
    '--btn-ring': colors.primary[200],
    '--btn-text': colors.primary[600],
    '--btn-spinner': colors.primary[600],
  },
};

const spinnerBase =
  'inline-block h-4 w-4 animate-spin rounded-full border-2 border-transparent';

export const BaseButton = forwardRef(function BaseButton(
  {
    variant = 'primary',
    size = 'md',
    fullWidth = false,
    loading = false,
    disabled = false,
    leftIcon,
    rightIcon,
    children,
    className,
    style,
    type = 'button',
    ...rest
  },
  ref,
) {
  const activeVariant = variantClasses[variant] ? variant : 'primary';
  const activeSize = sizeClasses[size] ? size : 'md';
  const isDisabled = disabled || loading;
  const tokenStyle = mergeStyle(variantTokens[activeVariant], style);

  return (
    <button
      ref={ref}
      type={type}
      className={cx(
        'inline-flex items-center justify-center gap-2 rounded-[10px] font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60',
        sizeClasses[activeSize],
        variantClasses[activeVariant],
        fullWidth && 'w-full',
        className,
      )}
      style={tokenStyle}
      disabled={isDisabled}
      aria-busy={loading}
      {...rest}
    >
      {loading ? (
        <span
          className={cx(
            spinnerBase,
            'border-t-[var(--btn-spinner)] border-[var(--btn-spinner)]/30',
          )}
        />
      ) : (
        leftIcon
      )}
      <span className="truncate">{children}</span>
      {!loading && rightIcon}
    </button>
  );
});

