/** Layout token maps for UI mode experiments — CSS/layout only, no data changes. */

export const UI_MODES = [
  { id: 'default', label: 'Default' },
  { id: 'compact', label: 'Compact' },
  { id: 'reader', label: 'Reader Optimized' },
]

export const MAX_WIDTH_OPTIONS = [
  { id: 'production', label: '650px (Production)', value: '650px' },
  { id: 'full', label: 'Full width', value: '100%' },
  { id: '900px', label: '900px', value: '900px' },
  { id: '650px', label: '650px', value: '650px' },
]

export function getLayoutTokens(uiMode) {
  switch (uiMode) {
    case 'compact':
      return {
        pageGap: 'space-y-3',
        headerGap: 'gap-1',
        titleFontSize: '1.25rem',
        titleFontWeight: 600,
        titleLineHeight: 1.3,
        typeFontSize: '0.75rem',
        progressFontSize: '0.75rem',
        cardPadding: 'p-3',
        cardGap: 'space-y-2',
        sectionHeadingClass: 'text-base font-semibold',
        bodyClass: 'text-sm leading-snug',
        listGap: 'space-y-1',
        definitionGap: 'space-y-2',
        definitionIndexMinWidth: '20px',
        outerSectionGap: 'space-y-4',
      }
    case 'reader':
      return {
        pageGap: 'space-y-8',
        headerGap: 'gap-3',
        titleFontSize: '2rem',
        titleFontWeight: 700,
        titleLineHeight: 1.2,
        typeFontSize: '0.9375rem',
        progressFontSize: '0.875rem',
        cardPadding: 'p-6',
        cardGap: 'space-y-6',
        sectionHeadingClass: 'text-xl font-bold tracking-tight border-b pb-2',
        bodyClass: 'text-base leading-relaxed',
        listGap: 'space-y-3',
        definitionGap: 'space-y-4',
        definitionIndexMinWidth: '28px',
        outerSectionGap: 'space-y-6',
      }
    default:
      return {
        pageGap: 'space-y-6',
        headerGap: 'gap-2',
        titleFontSize: '1.5rem',
        titleFontWeight: 600,
        titleLineHeight: 1.35,
        typeFontSize: '0.875rem',
        progressFontSize: '0.875rem',
        cardPadding: 'p-4',
        cardGap: 'space-y-4',
        sectionHeadingClass: 'text-lg font-semibold',
        bodyClass: 'leading-relaxed',
        listGap: 'space-y-2',
        definitionGap: 'space-y-3',
        definitionIndexMinWidth: '24px',
        outerSectionGap: 'space-y-6',
      }
  }
}
