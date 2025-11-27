import { forwardRef } from 'react';
import { colors } from '../../design-tokens';
import { cx, mergeStyle } from './utils/classNames';

const paddingMap = {
  none: 'p-0',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
};

const elevationMap = {
  none: 'shadow-none',
  sm: 'shadow-none',
  md: 'shadow-none',
  lg: 'shadow-none',
};

const interactiveMap = {
  none: '',
  hover: 'transition-transform hover:-translate-y-0.5',
  clickable: 'transition-transform hover:-translate-y-0.5 cursor-pointer',
};

export const BaseCard = forwardRef(function BaseCard(
  {
    title,
    subtitle,
    header,
    footer,
    actions,
    children,
    padding = 'md',
    elevation = 'md',
    interactive = 'none',
    className,
    style,
    fullHeight = false,
    ...rest
  },
  ref,
) {
  const activePadding = paddingMap[padding] ? padding : 'md';
  const activeElevation = elevationMap[elevation] ? elevation : 'md';
  const activeInteractive = interactiveMap[interactive] ? interactive : 'none';

  const hasHeader = title || subtitle || header || actions;

  const mergedStyle = mergeStyle(
    {
      '--card-bg': colors.semantic?.bg?.primary ?? '#ffffff',
      '--card-border': colors.semantic?.border?.default ?? colors.gray[200],
    },
    style,
  );

  return (
    <div
      ref={ref}
      className={cx(
        'flex flex-col rounded-[5px] border bg-[var(--card-bg)] border-[var(--card-border)] text-[var(--card-text, #111827)]',
        paddingMap[activePadding],
        elevationMap[activeElevation],
        interactiveMap[activeInteractive],
        fullHeight && 'h-full',
        className,
      )}
      style={mergedStyle}
      {...rest}
    >
      {hasHeader && (
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="space-y-1">
            {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
            {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
            {header}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}

      <div className="flex-1">{children}</div>

      {footer && <div className="mt-4 border-t border-[var(--card-border)] pt-4">{footer}</div>}
    </div>
  );
});

