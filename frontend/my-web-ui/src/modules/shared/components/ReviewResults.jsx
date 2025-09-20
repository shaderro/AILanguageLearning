const ReviewResults = ({
  results = [],              // 复习结果数组：可为 { isCorrect: boolean } 或 { choice: 'know'|'fuzzy'|'unknown' }
  type = 'vocab',            // 'vocab' | 'grammar'（仅用于文案/扩展）
  onBack,                    // 返回主页面回调
  customSummary = null,      // 自定义统计摘要渲染
  customList = null,         // 自定义结果列表渲染
}) => {
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

  const accuracy = counts.total > 0 ? Math.round((counts.know / counts.total) * 100) : 0;

  const summary = customSummary ?? (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-white rounded-lg p-4 shadow-sm">
        <div className="text-sm text-gray-500 mb-1">总题数</div>
        <div className="text-2xl font-bold text-gray-900">{counts.total}</div>
      </div>
      <div className="bg-white rounded-lg p-4 shadow-sm">
        <div className="text-sm text-gray-500 mb-1">认识</div>
        <div className="text-2xl font-bold text-green-600">{counts.know}</div>
      </div>
      <div className="bg-white rounded-lg p-4 shadow-sm">
        <div className="text-sm text-gray-500 mb-1">模糊</div>
        <div className="text-2xl font-bold text-yellow-600">{counts.fuzzy}</div>
      </div>
      <div className="bg-white rounded-lg p-4 shadow-sm">
        <div className="text-sm text-gray-500 mb-1">不认识</div>
        <div className="text-2xl font-bold text-red-600">{counts.unknown}</div>
      </div>
      <div className="bg-white rounded-lg p-4 shadow-sm col-span-2 md:col-span-4">
        <div className="text-sm text-gray-500 mb-1">正确率</div>
        <div className="flex items-center gap-3">
          <div className="text-2xl font-bold text-blue-600">{accuracy}%</div>
          <div className="flex-1 h-2 bg-gray-200 rounded">
            <div className="h-2 bg-blue-500 rounded" style={{ width: `${accuracy}%` }} />
          </div>
        </div>
      </div>
    </div>
  );

  const list = customList ?? (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">复习记录</h3>
      {results.length === 0 ? (
        <div className="text-gray-500 text-sm">暂无记录</div>
      ) : (
        <ul className="divide-y divide-gray-100">
          {results.map((r, i) => (
            <li key={i} className="py-2 flex items-center justify-between">
              <span className="text-gray-800 text-sm">第 {i + 1} 题</span>
              {'choice' in r ? (
                <span className={
                  r.choice === 'know'
                    ? 'text-green-600 text-sm'
                    : r.choice === 'fuzzy'
                    ? 'text-yellow-600 text-sm'
                    : 'text-red-600 text-sm'
                }>
                  {r.choice === 'know' ? '认识' : r.choice === 'fuzzy' ? '模糊' : '不认识'}
                </span>
              ) : (
                <span className={r.isCorrect ? 'text-green-600 text-sm' : 'text-red-600 text-sm'}>
                  {r.isCorrect ? '正确' : '错误'}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {summary}
      {list}
      <div className="flex justify-end">
        {onBack && (
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition-colors"
          >
            返回
          </button>
        )}
      </div>
    </div>
  );
};

export default ReviewResults; 