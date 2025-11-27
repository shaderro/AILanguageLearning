import { BaseBadge } from './BaseBadge';

export function BaseBadgeDemo() {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <BaseBadge>默认</BaseBadge>
      <BaseBadge variant="primary">语法</BaseBadge>
      <BaseBadge variant="success">已完成</BaseBadge>
      <BaseBadge variant="warning">待复习</BaseBadge>
      <BaseBadge variant="danger">需注意</BaseBadge>
      <BaseBadge variant="info" size="lg">
        德语
      </BaseBadge>
    </div>
  );
}

