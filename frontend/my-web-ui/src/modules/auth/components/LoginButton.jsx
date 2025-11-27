/**
 * 登录按钮
 * 显示在导航栏右侧，点击打开登录模态框
 */
import { useTranslate } from '../../../i18n/useTranslate'
import { BaseButton } from '../../../components/base'

const LoginButton = ({ onClick }) => {
  const t = useTranslate()
  return (
    <BaseButton
      onClick={onClick}
      size="md"
      leftIcon={
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
          />
        </svg>
      }
    >
      {t('登录')}
    </BaseButton>
  )
}

export default LoginButton


