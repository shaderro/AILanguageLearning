import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { useUser } from './UserContext'
import authService from '../modules/auth/services/authService'
import { isCreditsInsufficient } from '../utils/creditsUtils'
import BillingModal from '../components/features/billing/BillingModal'

const BillingContext = createContext(null)

export function BillingProvider({ children }) {
  const { token, userInfo, refreshUserInfo } = useUser()
  const [modalState, setModalState] = useState({
    open: false,
    variant: 'usage',
    trigger: 'header',
  })
  const [isUpgrading, setIsUpgrading] = useState(false)
  const [isBuyingCredits, setIsBuyingCredits] = useState(false)
  const [billingError, setBillingError] = useState(null)

  const plan = userInfo?.plan || 'free'
  const tokenBalance = userInfo?.token_balance
  const creditsInsufficient = isCreditsInsufficient(tokenBalance, userInfo?.role)

  const closeBilling = useCallback(() => {
    setModalState((s) => ({ ...s, open: false }))
    setBillingError(null)
  }, [])

  const openBilling = useCallback((options = {}) => {
    setBillingError(null)
    setModalState({
      open: true,
      variant: options.variant || 'usage',
      trigger: options.trigger || 'header',
    })
  }, [])

  const openPaywall = useCallback((options = {}) => {
    setBillingError(null)
    setModalState({
      open: true,
      variant: 'paywall',
      trigger: options.action || options.trigger || 'ai',
    })
  }, [])

  const simulateUpgrade = useCallback(async () => {
    if (!token) return
    setIsUpgrading(true)
    setBillingError(null)
    try {
      await authService.simulateProUpgrade(token)
      await refreshUserInfo(token, { force: true })
      closeBilling()
    } catch (err) {
      setBillingError(err?.response?.data?.detail || err?.message || 'Upgrade failed')
    } finally {
      setIsUpgrading(false)
    }
  }, [token, refreshUserInfo, closeBilling])

  const simulateBuyCredits = useCallback(async (credits) => {
    if (!token || !credits) return
    setIsBuyingCredits(true)
    setBillingError(null)
    try {
      await authService.simulateCreditsPurchase(token, credits)
      await refreshUserInfo(token, { force: true })
      closeBilling()
    } catch (err) {
      setBillingError(err?.response?.data?.detail || err?.message || 'Purchase failed')
    } finally {
      setIsBuyingCredits(false)
    }
  }, [token, refreshUserInfo, closeBilling])

  const value = useMemo(
    () => ({
      plan,
      tokenBalance,
      creditsInsufficient,
      modalState,
      isUpgrading,
      isBuyingCredits,
      billingError,
      openBilling,
      openPaywall,
      closeBilling,
      simulateUpgrade,
      simulateBuyCredits,
    }),
    [
      plan,
      tokenBalance,
      creditsInsufficient,
      modalState,
      isUpgrading,
      isBuyingCredits,
      billingError,
      openBilling,
      openPaywall,
      closeBilling,
      simulateUpgrade,
      simulateBuyCredits,
    ],
  )

  return (
    <BillingContext.Provider value={value}>
      {children}
      <BillingModal />
    </BillingContext.Provider>
  )
}

export function useBilling() {
  const ctx = useContext(BillingContext)
  if (!ctx) {
    throw new Error('useBilling must be used within BillingProvider')
  }
  return ctx
}

export function useBillingOptional() {
  return useContext(BillingContext)
}
