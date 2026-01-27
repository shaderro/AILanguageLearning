export default function GrammarNoteBadge({
  className = '',
  style = {},
  label = 'grammar note',
  onMouseEnter,
  onMouseLeave,
  onClick
}) {
  return (
    <div
      className={[
        'z-10 inline-flex items-center gap-1 px-2 py-0.5 text-gray-600 bg-white/80 border border-gray-300 rounded-sm cursor-pointer',
        className
      ].join(' ')}
      style={style}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={(e) => { e.stopPropagation(); onClick && onClick(e) }}
      // 🔧 移除 title 属性，避免浏览器显示默认 tooltip（已有自定义的 grammar notation card）
    >
      <span className="leading-none">{label}</span>
      <span className="leading-none">▾</span>
    </div>
  )
}


