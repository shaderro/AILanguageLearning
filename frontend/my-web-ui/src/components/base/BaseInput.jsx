import { forwardRef } from 'react';
import { colors } from '../../design-tokens';
import { cx, mergeStyle } from './utils/classNames';

const sizeMap = {
  sm: 'text-sm px-3 py-2',
  md: 'text-sm px-4 py-2.5',
  lg: 'text-base px-4 py-3',
};

const variantClasses = {
  outline:
    'border border-[var(--input-border)] bg-[var(--input-bg)] focus:border-[var(--input-border-focus)] focus:ring-2 focus:ring-[var(--input-border-focus)]',
  filled:
    'border border-transparent bg-[var(--input-bg)] focus:border-[var(--input-border-focus)] focus:ring-2 focus:ring-[var(--input-border-focus)]',
};

const variantTokens = {
  outline: {
    '--input-bg': colors.semantic?.bg?.primary ?? '#ffffff',
    '--input-border': colors.semantic?.border?.default ?? colors.gray[200],
  },
  filled: {
    '--input-bg': colors.semantic?.bg?.secondary ?? colors.gray[50],
    '--input-border': 'transparent',
  },
};

export const BaseInput = forwardRef(function BaseInput(
  {
    label,
    helperText,
    error,
    prefix,
    suffix,
    size = 'md',
    variant = 'outline',
    fullWidth = true,
    className,
    inputClassName,
    style,
    id,
    ...rest
  },
  ref,
) {
  const activeVariant = variantClasses[variant] ? variant : 'outline';
  const activeSize = sizeMap[size] ? size : 'md';
  const inputId = id ?? `input-${Math.random().toString(36).slice(2, 9)}`;

  const mergedStyle = mergeStyle(
    {
      '--input-border-focus': colors.primary[500],
    },
    mergeStyle(variantTokens[activeVariant], style),
  );

  const helperId = helperText ? `${inputId}-helper` : undefined;
  const errorMessage = typeof error === 'string' ? error : undefined;

  return (
    <label
      className={cx('flex flex-col gap-1 text-left', fullWidth && 'w-full', className)}
      htmlFor={inputId}
      style={mergedStyle}
    >
      {label && <span className="text-sm font-medium text-gray-700">{label}</span>}
      <div
        className={cx(
          'flex items-center gap-2 rounded-lg text-gray-900 focus-within:ring-offset-0',
          variantClasses[activeVariant],
          error && 'ring-2 ring-inset ring-red-200',
        )}
      >
        {prefix && <span className="pl-3 text-gray-500">{prefix}</span>}
        <input
          id={inputId}
          ref={ref}
          className={cx(
            'flex-1 bg-transparent placeholder:text-gray-400 focus:outline-none',
            sizeMap[activeSize],
            inputClassName,
          )}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? helperId : helperText ? helperId : undefined}
          {...rest}
        />
        {suffix && <span className="pr-3 text-gray-500">{suffix}</span>}
      </div>
      {error ? (
        <span id={helperId} className="text-sm text-red-600">
          {errorMessage ?? helperText ?? '输入有误'}
        </span>
      ) : (
        helperText && (
          <span id={helperId} className="text-sm text-gray-500">
            {helperText}
          </span>
        )
      )}
    </label>
  );
});

