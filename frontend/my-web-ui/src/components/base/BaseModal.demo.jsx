import { useState } from 'react';
import { BaseModal } from './BaseModal';
import { BaseButton } from './BaseButton';

export function BaseModalDemo() {
  const [open, setOpen] = useState(false);

  return (
    <div className="space-y-4">
      <BaseButton onClick={() => setOpen(true)}>打开模态框</BaseButton>

      <BaseModal
        isOpen={open}
        onClose={() => setOpen(false)}
        title="上传文章"
        subtitle="上传文章后即可开始阅读与 AI 对话。"
        footer={
          <>
            <BaseButton variant="ghost" onClick={() => setOpen(false)}>
              取消
            </BaseButton>
            <BaseButton>开始处理</BaseButton>
          </>
        }
      >
        <p className="text-sm text-gray-600">
          支持 URL、文件或直接粘贴文本进行上传，系统会自动为您进行分段和语法拆解。
        </p>
      </BaseModal>
    </div>
  );
}

