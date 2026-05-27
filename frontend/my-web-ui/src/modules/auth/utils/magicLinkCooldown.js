const STORAGE_KEY = 'magic_link_send_state'
export const MAGIC_LINK_COOLDOWN_SECONDS = 60

export function getMagicLinkSendState() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    const sentAt = Number(parsed.sentAt)
    const cooldownMs = Number(parsed.cooldownMs) || MAGIC_LINK_COOLDOWN_SECONDS * 1000
    if (!parsed.email || !Number.isFinite(sentAt)) {
      sessionStorage.removeItem(STORAGE_KEY)
      return null
    }
    const remainingMs = sentAt + cooldownMs - Date.now()
    if (remainingMs <= 0) {
      sessionStorage.removeItem(STORAGE_KEY)
      return null
    }
    return {
      email: String(parsed.email),
      remainingSeconds: Math.ceil(remainingMs / 1000),
      cooldownMs,
    }
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export function setMagicLinkSendState(email, cooldownSeconds = MAGIC_LINK_COOLDOWN_SECONDS) {
  const seconds = Math.max(1, Number(cooldownSeconds) || MAGIC_LINK_COOLDOWN_SECONDS)
  sessionStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      email: String(email).trim().toLowerCase(),
      sentAt: Date.now(),
      cooldownMs: seconds * 1000,
    }),
  )
}

export function clearMagicLinkSendState() {
  sessionStorage.removeItem(STORAGE_KEY)
}

export function isEmailInCooldown(email) {
  const state = getMagicLinkSendState()
  if (!state) return false
  return state.email === String(email || '').trim().toLowerCase()
}
