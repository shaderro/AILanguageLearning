import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import {
  SANDBOX_COSTS,
  SANDBOX_CREDIT_PACKS,
  SANDBOX_PLANS,
  addCredits,
  consumeCredits,
  enableLimitedMode,
  loadSandboxState,
  resetSandboxState,
  simulateDowngrade,
  simulateProUpgrade,
} from './billingSandboxStore'

const BillingSandboxContext = createContext(null)

export function BillingSandboxProvider({ children }) {
  const [state, setState] = useState(() => loadSandboxState())
  const [checkoutOpen, setCheckoutOpen] = useState(false)
  const [checkoutPhase, setCheckoutPhase] = useState('review') // review | processing | success
  const [lastCheckoutResult, setLastCheckoutResult] = useState(null)

  const refreshFromStorage = useCallback(() => {
    setState(loadSandboxState())
  }, [])

  const handleReset = useCallback(() => {
    setState(resetSandboxState())
    setCheckoutOpen(false)
    setCheckoutPhase('review')
    setLastCheckoutResult(null)
  }, [])

  const handleAddCredits = useCallback((amount) => {
    setState((prev) => addCredits(prev, amount, `Manual top-up: +${amount} credits.`))
  }, [])

  const handleDowngrade = useCallback(() => {
    setState((prev) => simulateDowngrade(prev))
  }, [])

  const handleUpgradePro = useCallback(() => {
    setState((prev) => simulateProUpgrade(prev))
  }, [])

  const openProCheckout = useCallback(() => {
    setCheckoutPhase('review')
    setLastCheckoutResult(null)
    setCheckoutOpen(true)
  }, [])

  const closeCheckout = useCallback(() => {
    if (checkoutPhase === 'processing') return
    setCheckoutOpen(false)
    setCheckoutPhase('review')
    setLastCheckoutResult(null)
  }, [checkoutPhase])

  const confirmCheckout = useCallback(() => {
    setCheckoutPhase('processing')
    window.setTimeout(() => {
      const next = simulateProUpgrade(loadSandboxState())
      setState(next)
      setCheckoutPhase('success')
      setLastCheckoutResult({
        plan: 'pro',
        creditsGranted: SANDBOX_PLANS.pro.includedCredits,
        totalCredits: next.credits,
      })
    }, 900)
  }, [])

  const simulateUsage = useCallback((kind) => {
    const cost = SANDBOX_COSTS[kind]
    const labels = {
      chat: 'Simulate Chat',
      annotation: 'Simulate Annotation',
      summarization: 'Simulate Summarization',
    }
    setState((prev) => {
      const result = consumeCredits(prev, cost, labels[kind])
      return result.ok ? result.state : prev
    })
    return cost
  }, [])

  const buyCreditPack = useCallback((packKey) => {
    const amount = SANDBOX_CREDIT_PACKS[packKey]
    if (!amount) return
    setState((prev) => addCredits(prev, amount, `Simulated credit purchase: +${amount} credits.`))
  }, [])

  const continueLimitedMode = useCallback(() => {
    setState((prev) => enableLimitedMode(prev))
  }, [])

  const value = useMemo(
    () => ({
      state,
      plans: SANDBOX_PLANS,
      costs: SANDBOX_COSTS,
      creditPacks: SANDBOX_CREDIT_PACKS,
      checkoutOpen,
      checkoutPhase,
      lastCheckoutResult,
      refreshFromStorage,
      reset: handleReset,
      addCredits: handleAddCredits,
      upgradePro: handleUpgradePro,
      downgrade: handleDowngrade,
      openProCheckout,
      closeCheckout,
      confirmCheckout,
      simulateUsage,
      buyCreditPack,
      continueLimitedMode,
      isExhausted: state.credits <= 0,
    }),
    [
      state,
      checkoutOpen,
      checkoutPhase,
      lastCheckoutResult,
      refreshFromStorage,
      handleReset,
      handleAddCredits,
      handleUpgradePro,
      handleDowngrade,
      openProCheckout,
      closeCheckout,
      confirmCheckout,
      simulateUsage,
      buyCreditPack,
      continueLimitedMode,
    ],
  )

  return (
    <BillingSandboxContext.Provider value={value}>
      {children}
    </BillingSandboxContext.Provider>
  )
}

export function useBillingSandbox() {
  const ctx = useContext(BillingSandboxContext)
  if (!ctx) {
    throw new Error('useBillingSandbox must be used within BillingSandboxProvider')
  }
  return ctx
}
