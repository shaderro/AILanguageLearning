import { colors } from '../../design-tokens';
import { cx, mergeStyle } from './utils/classNames';

const sizeMap = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-sm px-3 py-1',
};

const variantTokens = {
  default: {
    '--badge-bg': colors.gray[100],
    '--badge-text': colors.gray[700],
    '--badge-border': colors.gray[200],
  },
  primary: {
    '--badge-bg': colors.primary[50],
    '--badge-text': colors.primary[700],
    '--badge-border': colors.primary[200],
  },
  success: {
    '--badge-bg': colors.success[50],
    '--badge-text': colors.success[700],
    '--badge-border': colors.success[200],
  },
  warning: {
    '--badge-bg': colors.warning[50],
    '--badge-text': colors.warning[700],
    '--badge-border': colors.warning[200],
  },
  danger: {
    '--badge-bg': colors.danger[50],
    '--badge-text': colors.danger[700],
    '--badge-border': colors.danger[200],
  },
  info: {
    '--badge-bg': colors.semantic?.bg?.secondary ?? colors.gray[100],
    '--badge-text': colors.primary[700],
    '--badge-border': colors.primary[200],
  },
};

const baseClasses =
  'inline-flex items-center gap-1 rounded-full border bg-[var(--badge-bg)] text-[var(--badge-text)] border-[var(--badge-border)] font-medium';

export function BaseBadge({
  children,
  variant = 'default',
  size = 'md',
  className,
  leadingIcon,
  trailingIcon,
  style,
  ...rest
}) {
  const activeVariant = variantTokens[variant] ? variant : 'default';
  const activeSize = sizeMap[size] ? size : 'md';
  const mergedStyle = mergeStyle(variantTokens[activeVariant], style);

  return (
    <span
      className={cx(baseClasses, sizeMap[activeSize], className)}
      style={mergedStyle}
      {...rest}
    >
      {leadingIcon}
      <span className="whitespace-nowrap">{children}</span>
      {trailingIcon}
    </span>
  );
}

