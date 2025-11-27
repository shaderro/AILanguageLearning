import { BaseCard } from './BaseCard';
import { BaseButton } from './BaseButton';
import { BaseBadge } from './BaseBadge';

export function BaseCardDemo() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <BaseCard
        title="文章学习"
        subtitle="今日阅读 3 篇"
        actions={<BaseButton size="sm">查看</BaseButton>}
        footer={<span className="text-sm text-gray-500">最近更新：2 小时前</span>}
      >
        <p className="text-gray-600">
          统一卡片结构，支持标题、描述、操作和自定义内容区域，适用于文章、词汇、语法等多种列表。
        </p>
      </BaseCard>

      <BaseCard elevation="lg" interactive="hover">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">学习状态</p>
            <p className="text-2xl font-semibold text-gray-900">82%</p>
          </div>
          <BaseBadge variant="success">已完成 41/50</BaseBadge>
        </div>
      </BaseCard>
    </div>
  );
}

