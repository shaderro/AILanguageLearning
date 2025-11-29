import { BaseButton } from '../../base'

const QuickReviewCard = ({
  title,
  count,
  description,
  buttonLabel,
  onAction,
}) => {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-6 flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-3xl font-bold text-primary-600">{count}</p>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
      <BaseButton
        variant="primary"
        size="md"
        onClick={onAction}
        className="px-6"
      >
        {buttonLabel}
      </BaseButton>
    </div>
  )
}

export default QuickReviewCard

