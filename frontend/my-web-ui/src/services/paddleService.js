/**
 * Paddle Billing Checkout（前端仅使用 Client-side token，不含 API Key）。
 *
 * initializePaddle 在首次需要 Checkout 时调用；BillingProvider 挂载时会预热 initPaddle()。
 */
import { initializePaddle } from '@paddle/paddle-js'

let initPromise = null
let eventHandler = null

export function isPaddleEnabled() {
  return Boolean(import.meta.env.VITE_PADDLE_CLIENT_TOKEN?.trim())
}

function paddleEnvironment() {
  const env = (import.meta.env.VITE_PADDLE_ENV || 'sandbox').toLowerCase()
  return env === 'production' ? 'production' : 'sandbox'
}

export function getProPriceId() {
  return import.meta.env.VITE_PADDLE_PRICE_PRO?.trim() || ''
}

export function setPaddleEventHandler(handler) {
  eventHandler = handler
}

async function ensurePaddle() {
  if (!isPaddleEnabled()) {
    throw new Error('Paddle client token not configured')
  }
  if (!initPromise) {
    const token = import.meta.env.VITE_PADDLE_CLIENT_TOKEN.trim()
    const environment = paddleEnvironment()
    initPromise = initializePaddle({
      environment,
      token,
      eventCallback: (event) => {
        if (import.meta.env.DEV) {
          console.debug('[Paddle]', event?.name, event)
        }
        if (typeof eventHandler === 'function') {
          eventHandler(event)
        }
      },
    }).then((paddle) => {
      if (import.meta.env.DEV) {
        console.info(`[Paddle] initialized (${environment})`)
      }
      return paddle
    })
  }
  const paddle = await initPromise
  if (!paddle) {
    throw new Error('Failed to initialize Paddle')
  }
  return paddle
}

/** 应用启动时预热 Paddle.js（Sandbox + client-side token） */
export function initPaddle() {
  if (!isPaddleEnabled()) return Promise.resolve(null)
  return ensurePaddle().catch((err) => {
    console.warn('[Paddle] init failed:', err?.message || err)
    initPromise = null
    return null
  })
}

/**
 * 打开 Paddle Checkout overlay。
 * customData.user_id 供 webhook 入账时识别用户。
 */
export async function openPaddleCheckout({ priceId, userId, email }) {
  if (!priceId) {
    throw new Error('Price ID not configured')
  }
  if (!userId) {
    throw new Error('User must be logged in')
  }

  const paddle = await ensurePaddle()
  paddle.Checkout.open({
    items: [{ priceId, quantity: 1 }],
    customData: { user_id: String(userId) },
    customer: email ? { email } : undefined,
    settings: {
      displayMode: 'overlay',
      theme: 'light',
      successUrl: window.location.href.split('#')[0],
    },
  })
}
