import { BillingSandboxProvider } from './BillingSandboxContext'
import BillingSandboxHome from './BillingSandboxHome'
import BillingSandboxPage from './BillingSandboxPage'

function normalizeSandboxPath(pathname) {
  const path = (pathname || '/').replace(/\/+$/, '') || '/'
  return path
}

export default function BillingSandboxRoutes() {
  const path = normalizeSandboxPath(window.location.pathname)

  return (
    <BillingSandboxProvider>
      {path === '/sandbox/billing' ? <BillingSandboxPage /> : <BillingSandboxHome />}
    </BillingSandboxProvider>
  )
}

export function isBillingSandboxPath(pathname) {
  const path = normalizeSandboxPath(pathname)
  return path === '/sandbox' || path === '/sandbox/billing'
}
