import { createContext } from 'react'

/**
 * NotationContext - 提供 Grammar 和 Vocab Notation 相关的缓存和查询功能
 * 
 * 这个 Context 统一管理所有 notation 相关的数据和方法，
 * 避免通过多层组件传递 props (prop drilling)
 */
export const NotationContext = createContext(null)

