import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { BaseCard, BaseButton, BaseSpinner } from '../../base';
import { componentTokens } from '../../../design-tokens/design-tokens';
import { useUIText } from '../../../i18n/useUIText';

export function ArticlePreviewCard({
  title,
  wordCount = 0,
  noteCount = 0,
  preview = '',
  processingStatus = 'completed',
  onEdit,
  onDelete,
  onRead,
  className,
  style,
  width = 320,
  height = 170,
  showEditButton = true,
  showDeleteButton = true,
}) {
  const t = useUIText ? useUIText() : (text) => text;
  const widthValue = typeof width === 'number' ? `${width}px` : width;
  const heightValue = typeof height === 'number' ? `${height}px` : height;
  const titleRef = useRef(null);
  const previewRef = useRef(null);
  const [titleOverflow, setTitleOverflow] = useState(false);
  const [overflowDistance, setOverflowDistance] = useState(0);
  const [isTitleHover, setIsTitleHover] = useState(false);
  const [previewLines, setPreviewLines] = useState({
    first: preview || '',
    second: '',
  });
  const canvasRef = useRef(null);
  const isProcessing = processingStatus === 'processing';
  const isFailed = processingStatus === 'failed';
  const canInteract = !(isProcessing || isFailed);

  useEffect(() => {
    const el = titleRef.current;
    if (!el) {
      return;
    }
    const diff = el.scrollWidth - el.clientWidth;
    if (diff > 4) {
      setTitleOverflow(true);
      setOverflowDistance(diff);
    } else {
      setTitleOverflow(false);
      setOverflowDistance(0);
    }
  }, [title, widthValue]);

  useLayoutEffect(() => {
    const container = previewRef.current;
    if (!container) {
      return;
    }
    const fullText = (preview || '').trim();
    if (!fullText) {
      setPreviewLines({ first: '', second: '' });
      return;
    }

    const width = container.clientWidth || container.offsetWidth;
    if (!width) {
      setPreviewLines({ first: fullText, second: '' });
      return;
    }

    const computed = window.getComputedStyle(container);
    const font = computed.font || `${computed.fontWeight} ${computed.fontSize} ${computed.fontFamily}`;

    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }
    const ctx = canvasRef.current.getContext('2d');
    ctx.font = font;

    const measure = (text) => ctx.measureText(text).width;

    const fitSubstring = (text, limit) => {
      if (!text) {
        return 0;
      }
      let low = 0;
      let high = text.length;
      while (low < high) {
        const mid = Math.ceil((low + high) / 2);
        const slice = text.slice(0, mid);
        if (measure(slice) <= limit) {
          low = mid;
        } else {
          high = mid - 1;
        }
      }
      return Math.max(low, 1);
    };

    const firstLen = fitSubstring(fullText, width);
    const firstLine = fullText.slice(0, firstLen).trimEnd();
    let remainder = fullText.slice(firstLen).replace(/^\s+/, '');

    if (!remainder) {
      setPreviewLines((prev) =>
        prev.first === firstLine && !prev.second
          ? prev
          : { first: firstLine, second: '' },
      );
      return;
    }

    const secondLimit = width * 0.5;
    const secondLen = fitSubstring(remainder, secondLimit);
    let secondLine = remainder.slice(0, secondLen).trimEnd();
    const hasMore = secondLen < remainder.length;

    if (hasMore) {
      let candidate = secondLine.endsWith('…') ? secondLine : `${secondLine}…`;
      while (candidate.length > 1 && measure(candidate) > secondLimit) {
        candidate = `${candidate.slice(0, -2).trimEnd()}…`;
      }
      secondLine = candidate || '…';
    }

    setPreviewLines((prev) =>
      prev.first === firstLine && prev.second === secondLine
        ? prev
        : { first: firstLine, second: secondLine },
    );
  }, [preview, widthValue]);

  const titleAnimationStyle =
    titleOverflow && isTitleHover
      ? {
          transform: `translateX(-${overflowDistance}px)`,
          transition: `transform ${Math.min(Math.max(overflowDistance * 20, 4000), 10000)}ms linear`,
        }
      : {
          transform: 'translateX(0)',
          transition: 'transform 400ms ease-out',
        };

  return (
    <BaseCard
      padding="sm"
      interactive="none"
      className={`group shadow-none transition-shadow duration-200 hover:shadow-md ${className ?? ''}`}
      style={{ width: widthValue, height: heightValue, ...style }}
    >
      <div className="flex h-full flex-col space-y-1">
        <div className="relative">
          <div
            className="overflow-hidden"
            onMouseEnter={() => titleOverflow && setIsTitleHover(true)}
            onMouseLeave={() => setIsTitleHover(false)}
          >
            <h3
              ref={titleRef}
              className="pr-12 text-lg font-semibold text-gray-900 whitespace-nowrap"
              style={titleAnimationStyle}
            >
              {title}
            </h3>
          </div>
          {canInteract && showEditButton && onEdit && (
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-start justify-end">
              <button
                type="button"
                onClick={onEdit}
                className="pointer-events-auto hidden rounded-full bg-white/85 p-1 text-gray-500 opacity-0 transition-all duration-200 hover:bg-white hover:text-primary-600 group-hover:inline-flex group-hover:opacity-100"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L7.5 20.5H4v-3.5L16.732 3.732z"
                  />
                </svg>
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-4" style={{
          fontSize: componentTokens.text.cardNote.fontSize,
          color: componentTokens.text.cardNote.color,
          lineHeight: componentTokens.text.cardNote.lineHeight,
          fontWeight: componentTokens.text.cardNote.fontWeight,
        }}>
          <span>{wordCount} words</span>
          <span>{noteCount} notes</span>
        </div>
        {isProcessing && (
          <p className="text-xs font-medium text-yellow-600">{t('处理中...')}</p>
        )}
        {isFailed && (
          <p className="text-xs font-medium text-red-600">{t('处理失败')}</p>
        )}

        <div ref={previewRef} className="text-sm text-gray-700 space-y-1">
          {!preview || preview.trim() === '' || preview === t('暂无摘要') ? (
            <div className="flex items-center gap-2" style={{ minHeight: '3rem', lineHeight: '1.5rem' }}>
              <BaseSpinner size="sm" variant="neutral" label="" />
            </div>
          ) : (
            <>
              <div className="truncate">{previewLines.first}</div>
              {previewLines.second && (
                <div className="overflow-hidden" style={{ maxWidth: '50%' }}>
                  {previewLines.second}
                </div>
              )}
            </>
          )}
        </div>

        <div className="mt-auto pt-2 flex items-center gap-2">
          <div className="flex-1">
            {showDeleteButton && onDelete && (
              <button
                type="button"
                onClick={onDelete}
                disabled={!canInteract}
                className={`pointer-events-none inline-flex items-center rounded-full p-2 opacity-0 transition-all duration-200 ${
                  canInteract
                    ? 'bg-red-50 text-red-500 hover:bg-red-100 group-hover:pointer-events-auto group-hover:opacity-100'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
                aria-label={t('删除')}
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            )}
          </div>
          <div className="ml-auto flex justify-end w-1/3 min-w-[96px]">
            <BaseButton
              variant="primary"
              size="sm"
              onClick={() => canInteract && onRead?.()}
              disabled={!canInteract}
              className="w-full justify-center px-4"
            >
              {isProcessing ? t('处理中...') : isFailed ? t('处理失败') : 'read'}
            </BaseButton>
          </div>
        </div>
      </div>
    </BaseCard>
  );
}


