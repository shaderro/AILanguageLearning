import { useState } from 'react';
import { BaseButton } from './BaseButton';

export function BaseButtonDemo() {
  const [loading, setLoading] = useState(false);

  const handleAsync = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 1200);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <BaseButton>主要按钮</BaseButton>
        <BaseButton variant="secondary">次要按钮</BaseButton>
        <BaseButton variant="ghost">幽灵按钮</BaseButton>
        <BaseButton variant="danger">危险操作</BaseButton>
        <BaseButton variant="link">链接样式</BaseButton>
      </div>

      <div className="flex flex-wrap gap-3">
        <BaseButton size="sm">Small</BaseButton>
        <BaseButton size="md">Medium</BaseButton>
        <BaseButton size="lg">Large</BaseButton>
      </div>

      <BaseButton fullWidth loading={loading} onClick={handleAsync}>
        保存设置
      </BaseButton>
    </div>
  );
}

