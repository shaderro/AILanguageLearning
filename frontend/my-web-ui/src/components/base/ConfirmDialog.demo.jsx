import { useState } from 'react';
import { ConfirmDialog } from './ConfirmDialog';
import { BaseButton } from './BaseButton';

export function ConfirmDialogDemo() {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleConfirm = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setIsOpen(false);
    }, 1200);
  };

  return (
    <div className="space-y-4">
      <BaseButton onClick={() => setIsOpen(true)}>删除文章</BaseButton>

      <ConfirmDialog
        isOpen={isOpen}
        onCancel={() => setIsOpen(false)}
        onConfirm={handleConfirm}
        loading={loading}
        variant="danger"
        meta={{
          文章名称: '德语语法入门',
          已学习: '67%',
        }}
        description="删除后将无法恢复，确认要继续吗？"
        confirmLabel="永久删除"
        cancelLabel="保留"
      />
    </div>
  );
}


