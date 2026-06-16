import { useCallback, useState } from 'react'
import SimulationBanner from '../billing/SimulationBanner'
import SandboxControlPanel from './SandboxControlPanel'
import ProductionVocabPreview from './ProductionVocabPreview'
import {
  DEFAULT_SANDBOX_LAYOUT,
  MOCK_VOCAB_LIST_LENGTH,
} from './mockVocabData'

export default function UISandboxPage() {
  const [uiMode, setUiMode] = useState(DEFAULT_SANDBOX_LAYOUT.uiMode)
  const [maxWidth, setMaxWidth] = useState(DEFAULT_SANDBOX_LAYOUT.maxWidth)
  const [sections, setSections] = useState({ ...DEFAULT_SANDBOX_LAYOUT.sections })
  const [currentIndex, setCurrentIndex] = useState(0)

  const handleSectionToggle = useCallback((sectionId) => {
    setSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }))
  }, [])

  const handleReset = useCallback(() => {
    setUiMode(DEFAULT_SANDBOX_LAYOUT.uiMode)
    setMaxWidth(DEFAULT_SANDBOX_LAYOUT.maxWidth)
    setSections({ ...DEFAULT_SANDBOX_LAYOUT.sections })
    setCurrentIndex(0)
  }, [])

  const handlePrevious = currentIndex > 0
    ? () => setCurrentIndex((index) => Math.max(0, index - 1))
    : null

  const handleNext = currentIndex < MOCK_VOCAB_LIST_LENGTH - 1
    ? () => setCurrentIndex((index) => Math.min(MOCK_VOCAB_LIST_LENGTH - 1, index + 1))
    : null

  return (
    <div className="min-h-screen bg-white">
      <div className="border-b border-slate-200 bg-white px-4 py-3 lg:px-6">
        <SimulationBanner subtitle="复刻正式词汇详情页（VocabDetailCard）— mock 数据，不调用 API，不影响生产流程。" />
      </div>

      <div className="flex flex-col lg:flex-row lg:items-start">
        <SandboxControlPanel
          uiMode={uiMode}
          maxWidth={maxWidth}
          sections={sections}
          onUiModeChange={setUiMode}
          onMaxWidthChange={setMaxWidth}
          onSectionToggle={handleSectionToggle}
          onReset={handleReset}
        />

        <main className="min-w-0 flex-1">
          <ProductionVocabPreview
            uiMode={uiMode}
            maxWidth={maxWidth}
            sections={sections}
            currentIndex={currentIndex}
            totalCount={MOCK_VOCAB_LIST_LENGTH}
            onPrevious={handlePrevious}
            onNext={handleNext}
          />
        </main>
      </div>
    </div>
  )
}
