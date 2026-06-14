import { LanguageProvider } from '../../contexts/LanguageContext'
import { UiLanguageProvider } from '../../contexts/UiLanguageContext'
import UISandboxPage from './UISandboxPage'

function normalizePath(pathname) {
  const path = (pathname || '/').replace(/\/+$/, '') || '/'
  return path
}

export default function UISandboxRoutes() {
  return (
    <LanguageProvider>
      <UiLanguageProvider>
        <UISandboxPage />
      </UiLanguageProvider>
    </LanguageProvider>
  )
}

export function isUISandboxPath(pathname) {
  return normalizePath(pathname) === '/ui-sandbox'
}
