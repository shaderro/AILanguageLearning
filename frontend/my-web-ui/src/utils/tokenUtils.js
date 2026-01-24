/**
 * Token 工具函数
 */

/**
 * 将 token 转换为积分
 * 转换规则：10000 token = 1积分
 * 显示小数点后一位，四舍五入
 * UI显示最小为0（即使token balance为负数）
 * @param {number} tokens - token 数量
 * @returns {string} 积分字符串（保留一位小数）
 */
export const convertTokensToPoints = (tokens) => {
  if (tokens === undefined || tokens === null) {
    return '0.0'
  }
  // UI显示最小为0，即使token balance为负数
  const displayTokens = Math.max(0, tokens)
  const points = displayTokens / 10000
  return points.toFixed(1)
}

/**
 * 检查用户token是否不足
 * 判断条件：
 * - 非admin用户
 * - token < 1000 或 积分 < 0.1
 * @param {number} tokenBalance - token余额
 * @param {string} role - 用户角色（'admin' | 'user'）
 * @returns {boolean} true表示token不足，false表示token充足
 */
export const isTokenInsufficient = (tokenBalance, role = 'user') => {
  // admin用户不受限制
  if (role === 'admin') {
    return false
  }
  
  // 检查token是否不足
  if (tokenBalance === undefined || tokenBalance === null) {
    return true
  }
  
  // token < 1000 或 积分 < 0.1（即 token < 1000）
  return tokenBalance < 1000
}
