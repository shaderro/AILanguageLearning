/**
 * Opens the magic-link auth modal
 */
import { BaseButton } from '../../../components/base'
import { useUIText } from '../../../i18n/useUIText'

const LoginButton = ({ onClick }) => {
  const t = useUIText()
  return (
    <BaseButton onClick={onClick} size="md" className="rounded-lg font-medium">
      {t('Get Started')}
    </BaseButton>
  )
}

export default LoginButton
