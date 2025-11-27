import { BaseModal } from './BaseModal';
import { BaseButton } from './BaseButton';
import { BaseBadge } from './BaseBadge';

const confirmVariantMap = {
  primary: 'primary',
  danger: 'danger',
};

export function ConfirmDialog({
  isOpen,
  onConfirm,
  onCancel,
  title = '确认操作',
  description = '此操作将无法撤销，请确认后继续。',
  confirmLabel = '确认',
  cancelLabel = '取消',
  variant = 'primary',
  loading = false,
  meta,
}) {
  const confirmVariant = confirmVariantMap[variant] ?? 'primary';

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={onCancel}
      title={title}
      subtitle={description}
      size="sm"
      footer={
        <>
          <BaseButton variant="ghost" onClick={onCancel}>
            {cancelLabel}
          </BaseButton>
          <BaseButton
            variant={confirmVariant}
            onClick={onConfirm}
            loading={loading}
          >
            {confirmLabel}
          </BaseButton>
        </>
      }
    >
      {meta && (
        <div className="space-y-2 text-sm text-gray-700">
          {Object.entries(meta).map(([label, value]) => (
            <div
              key={label}
              className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-gray-600"
            >
              <span className="font-medium">{label}</span>
              <BaseBadge size="sm" variant="default">
                {value}
              </BaseBadge>
            </div>
          ))}
        </div>
      )}
    </BaseModal>
  );
}

