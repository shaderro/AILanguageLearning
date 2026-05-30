/** 记住 magic link 使用的邮箱（仅本地 UX，非认证凭据） */
const LAST_EMAIL_KEY = 'linktext_magic_link_last_email'

export function getLastMagicLinkEmail() {
  try {
    return localStorage.getItem(LAST_EMAIL_KEY) || ''
  } catch {
    return ''
  }
}

export function setLastMagicLinkEmail(email) {
  const trimmed = (email || '').trim()
  if (!trimmed) return
  try {
    localStorage.setItem(LAST_EMAIL_KEY, trimmed)
  } catch {
    /* ignore quota */
  }
}
