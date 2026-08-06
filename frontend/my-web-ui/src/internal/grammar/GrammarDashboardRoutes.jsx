import GrammarDashboardPage from './GrammarDashboardPage'

function normalizePath(pathname) {
  return (pathname || '/').replace(/\/+$/, '') || '/'
}

export function isInternalGrammarDashboardPath(pathname) {
  return normalizePath(pathname) === '/internal/grammar-dashboard'
}

export default function GrammarDashboardRoutes() {
  return <GrammarDashboardPage />
}
