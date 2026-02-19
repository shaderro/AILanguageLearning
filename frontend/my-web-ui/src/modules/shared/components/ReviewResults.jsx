import { useUIText } from '../../../i18n/useUIText'
import { useTranslate } from '../../../i18n/useTranslate'

const ReviewResults = ({
  results = [],              // 复习结果数组：可为 { isCorrect: boolean } 或 { choice: 'know'|'fuzzy'|'unknown' }
  type = 'vocab',            // 'vocab' | 'grammar'（仅用于文案/扩展）
  onBack,                    // 返回主页面回调
  customSummary = null,      // 自定义统计摘要渲染
  customList = null,         // 自定义结果列表渲染
}) => {
  const t = useUIText()
  const tTranslate = useTranslate()
  // 兼容两种结果格式：isCorrect 或 choice
  const counts = results.reduce(
    (acc, r) => {
      if (typeof r?.isCorrect === 'boolean') {
        if (r.isCorrect) acc.know += 1; else acc.unknown += 1;
      } else if (typeof r?.choice === 'string') {
        if (r.choice === 'know') acc.know += 1;
        if (r.choice === 'fuzzy') acc.fuzzy += 1;
        if (r.choice === 'unknown') acc.unknown += 1;
      }
      acc.total += 1;
      return acc;
    },
    { total: 0, know: 0, fuzzy: 0, unknown: 0 }
  );

  // 🔧 只保留统计数据：总题数、认识、不认识（已去掉模糊选项）
  const summary = customSummary ?? (
    <div className="grid grid-cols-3 gap-3">
      <div className="bg-white rounded-lg p-3 shadow-sm">
        <div className="text-xs text-gray-500 mb-1">{tTranslate('总题数', 'Total Questions')}</div>
        <div className="text-xl font-bold text-gray-900">{counts.total}</div>
      </div>
      <div className="bg-white rounded-lg p-3 shadow-sm">
        <div className="text-xs text-gray-500 mb-1">{tTranslate('认识', 'Known')}</div>
        <div className="text-xl font-bold text-green-600">{counts.know}</div>
      </div>
      <div className="bg-white rounded-lg p-3 shadow-sm">
        <div className="text-xs text-gray-500 mb-1">{tTranslate('不认识', 'Unknown')}</div>
        <div className="text-xl font-bold text-red-600">{counts.unknown}</div>
      </div>
    </div>
  );

  return (
    <div className="w-full max-w-2xl mx-auto space-y-3">
      {/* 复习完成提示 */}
      <div className="bg-white rounded-lg p-5 shadow-sm text-center">
        <div className="text-xl font-bold text-gray-900 mb-1">{tTranslate('复习完成', 'Review Completed')}</div>
        <div className="text-sm text-gray-500">{tTranslate('恭喜完成本次复习！', 'Congratulations on completing this review!')}</div>
      </div>
      
      {/* 统计数据 */}
      {summary}
      
      {/* 返回按钮 */}
      <div className="flex justify-end pt-1">
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition-colors text-sm"
          >
            {tTranslate('返回', 'Back')}
          </button>
        )}
      </div>
    </div>
  );
};

export default ReviewResults; 