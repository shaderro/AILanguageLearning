import { useMemo } from 'react'
import VocabDetailCard from '../../components/features/vocab/VocabDetailCard'
import { buildMockVocab } from './mockVocabData'
import './uiSandboxPreview.css'

const OUTER_WIDTH_CLASS = {
  production: 'max-w-[650px]',
  full: 'max-w-none',
  '900px': 'max-w-[900px]',
  '650px': 'max-w-[650px]',
}

export default function ProductionVocabPreview({
  uiMode,
  maxWidth,
  sections,
  currentIndex,
  totalCount,
  onPrevious,
  onNext,
}) {
  const vocab = useMemo(
    () => buildMockVocab(currentIndex, sections),
    [currentIndex, sections],
  )

  const outerWidthClass = OUTER_WIDTH_CLASS[maxWidth] ?? OUTER_WIDTH_CLASS.production

  return (
    <div
      className={`ui-sandbox-preview h-full bg-white p-8 ${outerWidthClass} mx-auto`}
      data-ui-mode={uiMode}
      style={{ backgroundColor: 'white', minHeight: '100%' }}
    >
      <VocabDetailCard
        vocab={vocab}
        loading={false}
        onPrevious={onPrevious}
        onNext={onNext}
        onBack={() => {}}
        currentIndex={currentIndex}
        totalCount={totalCount}
      />
    </div>
  )
}
