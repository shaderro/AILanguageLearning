/** Render 生产后端（与 Vercel / linktext.app 前端配合） */
export const PRODUCTION_API_BASE_URL = 'https://ailanguagelearning.onrender.com'

/**
 * API 根地址：VITE_API_BASE_URL > linktext.app 生产 > 本地开发默认。
 */
export function resolveApiBaseUrl() {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (envUrl && String(envUrl).trim()) {
    return String(envUrl).trim().replace(/\/$/, '')
  }
  if (typeof window !== 'undefined') {
    const host = window.location.hostname
    if (host === 'linktext.app' || host === 'www.linktext.app') {
      return PRODUCTION_API_BASE_URL
    }
  }
  return 'http://127.0.0.1:8000'
}
