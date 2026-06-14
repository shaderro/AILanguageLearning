import { MAX_WIDTH_OPTIONS, UI_MODES } from './layoutVariants'

const SECTION_CONTROLS = [
  { id: 'definition', label: 'Definition / 释义' },
  { id: 'wordFeatures', label: 'Word Features / 词汇特征' },
  { id: 'rareSense', label: 'Rare Sense / 少见义' },
  { id: 'collocations', label: 'Collocations / 搭配' },
  { id: 'grammarNotes', label: 'Grammar Notes / 语法说明' },
  { id: 'examples', label: 'Examples / 例句' },
]

function SegmentedControl({ options, value, onChange, name }) {
  return (
    <div className="flex flex-wrap gap-1" role="group" aria-label={name}>
      {options.map((option) => {
        const active = value === option.id
        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onChange(option.id)}
            className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors ${
              active
                ? 'bg-slate-800 text-white'
                : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50'
            }`}
            aria-pressed={active}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}

export default function SandboxControlPanel({
  uiMode,
  maxWidth,
  sections,
  onUiModeChange,
  onMaxWidthChange,
  onSectionToggle,
  onReset,
}) {
  return (
    <aside
      className="sticky top-0 z-20 flex h-fit max-h-screen flex-col gap-5 overflow-y-auto border-r border-slate-200 bg-slate-50 p-4 lg:w-72 lg:shrink-0"
      aria-label="UI sandbox controls"
    >
      <div>
        <p className="font-mono text-[10px] uppercase tracking-widest text-slate-400">/ui-sandbox</p>
        <h2 className="mt-1 text-sm font-semibold text-slate-900">Layout Controls</h2>
        <p className="mt-1 text-xs text-slate-500">
          使用正式 VocabDetailCard 组件 + mock 数据，Default 模式为 1:1 复刻。
        </p>
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          UI Mode
        </label>
        <SegmentedControl
          name="UI mode"
          options={UI_MODES}
          value={uiMode}
          onChange={onUiModeChange}
        />
        {uiMode !== 'default' ? (
          <p className="text-xs text-slate-500">
            非 Default 模式仅应用 sandbox CSS 覆盖，用于快速对比密度与层级。
          </p>
        ) : null}
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Max Width
        </label>
        <SegmentedControl
          name="Max width"
          options={MAX_WIDTH_OPTIONS}
          value={maxWidth}
          onChange={onMaxWidthChange}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Section Visibility
        </label>
        <div className="space-y-2">
          {SECTION_CONTROLS.map(({ id, label }) => (
            <label
              key={id}
              className="flex cursor-pointer items-center gap-2 rounded-md bg-white px-2 py-1.5 text-sm text-slate-700 ring-1 ring-slate-200"
            >
              <input
                type="checkbox"
                className="rounded border-slate-300 text-slate-800 focus:ring-slate-500"
                checked={sections[id]}
                onChange={() => onSectionToggle(id)}
              />
              {label}
            </label>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={onReset}
        className="rounded-md bg-white px-3 py-2 text-sm font-medium text-slate-700 ring-1 ring-slate-200 hover:bg-slate-100"
      >
        Reset layout
      </button>

      <div className="mt-auto rounded-md border border-dashed border-slate-300 bg-white p-3 text-xs text-slate-500">
        <p className="font-medium text-slate-700">Extend here</p>
        <p className="mt-1">
          修改 <code className="text-[11px]">mockVocabData.js</code> 换样本；在{' '}
          <code className="text-[11px]">uiSandboxPreview.css</code> 加新实验样式。
        </p>
      </div>
    </aside>
  )
}
