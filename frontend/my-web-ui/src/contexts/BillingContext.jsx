import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useUser } from './UserContext'
import authService from '../modules/auth/services/authService'
import { isCreditsInsufficient } from '../utils/creditsUtils'
import BillingModal from '../components/features/billing/BillingModal'
import {
  getProPriceId,
  initPaddle,
  isPaddleEnabled,
  openPaddleCheckout,
  setPaddleEventHandler,
} from '../services/paddleService'

const BillingContext = createContext(null)

export function BillingProvider({ children }) {
  const { token, userInfo, refreshUserInfo } = useUser()
  const [modalState, setModalState] = useState({
    open: false,
    variant: 'usage',
    trigger: 'header',
  })
  const [isUpgrading, setIsUpgrading] = useState(false)
  const [billingError, setBillingError] = useState(null)
  const paddleEnabled = isPaddleEnabled()

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

  const refreshAfterPayment = useCallback(async () => {
    if (!token) return
    await refreshUserInfo(token, { force: true })
    setTimeout(() => refreshUserInfo(token, { force: true }), 2500)
    closeBilling()
  }, [token, refreshUserInfo, closeBilling])

  useEffect(() => {
    if (!paddleEnabled) return undefined
    initPaddle()
    setPaddleEventHandler((event) => {
      if (event?.name === 'checkout.completed') {
        refreshAfterPayment()
      }
      if (event?.name === 'checkout.error') {
        setBillingError(event?.data?.detail || 'Checkout failed')
        setIsUpgrading(false)
      }
    })
    return () => setPaddleEventHandler(null)
  }, [paddleEnabled, refreshAfterPayment])

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

  const upgradeToPro = useCallback(async () => {
    if (!userInfo?.user_id) return
    if (paddleEnabled) {
      setIsUpgrading(true)
      setBillingError(null)
      try {
        await openPaddleCheckout({
          priceId: getProPriceId(),
          userId: userInfo.user_id,
          email: userInfo.email,
        })
      } catch (err) {
        setBillingError(err?.message || 'Failed to open checkout')
      } finally {
        setIsUpgrading(false)
      }
      return
    }
    await simulateUpgrade()
  }, [userInfo, paddleEnabled, simulateUpgrade])

  const value = useMemo(
    () => ({
      plan,
      tokenBalance,
      creditsInsufficient,
      modalState,
      isUpgrading,
      billingError,
      paddleEnabled,
      openBilling,
      openPaywall,
      closeBilling,
      upgradeToPro,
      simulateUpgrade,
    }),
    [
      plan,
      tokenBalance,
      creditsInsufficient,
      modalState,
      isUpgrading,
      billingError,
      paddleEnabled,
      openBilling,
      openPaywall,
      closeBilling,
      upgradeToPro,
      simulateUpgrade,
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
