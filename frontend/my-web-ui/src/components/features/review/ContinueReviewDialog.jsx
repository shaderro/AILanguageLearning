/**
 * 继续复习对话框
 * 询问用户是否继续上次的复习进度
 */
import { BaseModal, BaseButton } from '../../base'
import { useUIText } from '../../../i18n/useUIText'

const ContinueReviewDialog = ({ isOpen, onContinue, onRestart, onCancel, currentProgress, totalProgress }) => {
  const t = useUIText()
  
  if (!isOpen) return null

  const progressText = currentProgress && totalProgress 
    ? t('上次复习到第 {current} / {total} 个').replace('{current}', currentProgress).replace('{total}', totalProgress)
    : t('上次复习进度')

  // 🔧 关闭按钮应该调用 onCancel（如果提供），否则调用 onRestart
  const handleClose = onCancel || onRestart

  return (
    <BaseModal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('继续上次复习？')}
      subtitle={progressText}
      size="sm"
      showCloseButton={true}
    >
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          {t('检测到您有未完成的复习进度，是否继续上次的复习？')}
        </p>
        
        <div className="flex flex-col space-y-3 pt-2">
          <BaseButton 
            onClick={onContinue} 
            fullWidth
            variant="primary"
          >
            {t('继续上次进度')}
          </BaseButton>
          <BaseButton 
            onClick={onRestart} 
            fullWidth
            variant="secondary"
          >
            {t('重新开始')}
          </BaseButton>
        </div>
      </div>
    </BaseModal>
  )
}

export default ContinueReviewDialog

