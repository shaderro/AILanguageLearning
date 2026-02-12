import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { colors, radius } from '../../design-tokens';
import { cx, mergeStyle } from './utils/classNames';

const sizeMap = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

export function BaseModal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  size = 'md',
  closeOnOverlay = true,
  closeOnEscape = true,
  className,
  style,
}) {
  const dialogRef = useRef(null);
  const selectedSize = sizeMap[size] ? size : 'md';

  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && closeOnEscape) {
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    const { overflow } = document.body.style;
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = overflow;
    };
  }, [isOpen, onClose, closeOnEscape]);

  if (!isOpen || typeof document === 'undefined') {
    return null;
  }

  const handleOverlayClick = (event) => {
    if (!closeOnOverlay) {
      return;
    }

    if (dialogRef.current && event.target === dialogRef.current) {
      onClose?.();
    }
  };

  const mergedStyle = mergeStyle(
    {
      '--modal-bg': colors.semantic?.bg?.primary ?? '#ffffff',
      '--modal-border': colors.semantic?.border?.default ?? colors.gray[200],
    },
    style,
  );

  return createPortal(
    <div
      ref={dialogRef}
      className="fixed inset-0 z-[var(--modal-z,1050)] flex items-center justify-center bg-black/40 px-4 py-8"
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
    >
      <div
        className={cx(
          'w-full rounded-2xl border bg-[var(--modal-bg)] border-[var(--modal-border)] shadow-xl',
          sizeMap[selectedSize],
          className,
        )}
        style={mergedStyle}
      >
        {(title || subtitle) && (
          <div className="border-b border-[var(--modal-border)] px-6 py-4">
            {title && <h2 className="text-xl font-semibold text-gray-900">{title}</h2>}
            {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
          </div>
        )}

        <div className="px-6 py-4">{children}</div>

        {footer && (
          <div className="border-t border-[var(--modal-border)] px-6 py-4 flex items-center justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
}

