import { useState } from 'react';
import { LoadingOverlay } from './LoadingOverlay';
import { BaseButton } from './BaseButton';

export function LoadingOverlayDemo() {
  const [isCardLoading, setIsCardLoading] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);

  const triggerCardLoading = () => {
    setIsCardLoading(true);
    setTimeout(() => setIsCardLoading(false), 1500);
  };

  const triggerFullScreen = () => {
    setIsFullScreen(true);
    setTimeout(() => setIsFullScreen(false), 1200);
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">文章同步</h3>
          <BaseButton variant="secondary" onClick={triggerCardLoading}>
            刷新
          </BaseButton>
        </div>

        <LoadingOverlay isActive={isCardLoading}>
          <ul className="mt-4 space-y-2 text-sm text-gray-600">
            <li>· 最新文章：德语阅读 - 82%</li>
            <li>· 语法卡片：4 条待复习</li>
            <li>· 词汇卡片：12 条待巩固</li>
          </ul>
        </LoadingOverlay>
      </div>

      <div className="space-x-3">
        <BaseButton onClick={triggerFullScreen}>显示全屏 Loading</BaseButton>
      </div>

      {isFullScreen && (
        <LoadingOverlay
          isActive
          fullScreen
          text="加载仪表盘..."
          variant="dark"
        >
          <div className="h-screen" />
        </LoadingOverlay>
      )}
    </div>
  );
}


