import { BaseSpinner } from './BaseSpinner';

export function BaseSpinnerDemo() {
  return (
    <div className="space-y-6 text-gray-700">
      <div className="flex items-center gap-6">
        <BaseSpinner size="sm" label="Small" />
        <BaseSpinner size="md" label="Medium" />
        <BaseSpinner size="lg" label="Large" />
      </div>

      <div className="flex items-center gap-6">
        <BaseSpinner variant="primary" label="蓝色主题" />
        <BaseSpinner variant="neutral" label="灰色主题" />
        <BaseSpinner variant="success" label="绿色主题" />
      </div>

      <div className="space-y-2 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <p className="text-sm text-gray-500">可自定义文案或隐藏文字：</p>
        <div className="flex items-center gap-4">
          <BaseSpinner label="同步数据中..." />
          <BaseSpinner label="" className="text-primary-600" />
        </div>
      </div>
    </div>
  );
}


