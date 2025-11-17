/**
 * 游客数据管理器
 * 
 * 管理游客模式下的本地数据存储
 */

const GUEST_DATA_PREFIX = 'guest_data_'

export const guestDataManager = {
  /**
   * 保存游客词汇数据
   */
  saveVocab: (guestId, vocabData) => {
    const key = `${GUEST_DATA_PREFIX}${guestId}_vocab`
    const existing = guestDataManager.getVocabs(guestId)
    
    // 检查是否已存在
    const exists = existing.find(v => v.vocab_body === vocabData.vocab_body)
    if (exists) {
      console.log('⚠️ [GuestData] 词汇已存在:', vocabData.vocab_body)
      return false
    }
    
    // 添加新词汇
    const newVocab = {
      vocab_id: Date.now(), // 临时ID
      ...vocabData,
      created_at: new Date().toISOString()
    }
    
    const updated = [...existing, newVocab]
    localStorage.setItem(key, JSON.stringify(updated))
    console.log('✅ [GuestData] 保存词汇:', vocabData.vocab_body)
    return true
  },

  /**
   * 获取游客词汇列表
   */
  getVocabs: (guestId) => {
    const key = `${GUEST_DATA_PREFIX}${guestId}_vocab`
    const data = localStorage.getItem(key)
    return data ? JSON.parse(data) : []
  },

  /**
   * 保存游客语法规则
   */
  saveGrammar: (guestId, grammarData) => {
    const key = `${GUEST_DATA_PREFIX}${guestId}_grammar`
    const existing = guestDataManager.getGrammars(guestId)
    
    // 检查是否已存在
    const exists = existing.find(g => g.rule_name === grammarData.rule_name)
    if (exists) {
      console.log('⚠️ [GuestData] 语法规则已存在:', grammarData.rule_name)
      return false
    }
    
    // 添加新规则
    const newGrammar = {
      rule_id: Date.now(), // 临时ID
      ...grammarData,
      created_at: new Date().toISOString()
    }
    
    const updated = [...existing, newGrammar]
    localStorage.setItem(key, JSON.stringify(updated))
    console.log('✅ [GuestData] 保存语法规则:', grammarData.rule_name)
    return true
  },

  /**
   * 获取游客语法规则列表
   */
  getGrammars: (guestId) => {
    const key = `${GUEST_DATA_PREFIX}${guestId}_grammar`
    const data = localStorage.getItem(key)
    return data ? JSON.parse(data) : []
  },

  /**
   * 保存游客文章数据
   */
  saveArticle: (guestId, articleData) => {
    const key = `${GUEST_DATA_PREFIX}${guestId}_articles`
    const existing = guestDataManager.getArticles(guestId)
    
    // 检查是否已存在（根据 article_id）
    const exists = existing.find(a => a.article_id === articleData.article_id)
    if (exists) {
      console.log('⚠️ [GuestData] 文章已存在:', articleData.article_id)
      return false
    }
    
    // 添加新文章
    const newArticle = {
      ...articleData,
      created_at: new Date().toISOString()
    }
    
    const updated = [...existing, newArticle]
    localStorage.setItem(key, JSON.stringify(updated))
    console.log('✅ [GuestData] 保存文章:', articleData.title || articleData.article_id)
    return true
  },

  /**
   * 获取游客文章列表
   */
  getArticles: (guestId) => {
    const key = `${GUEST_DATA_PREFIX}${guestId}_articles`
    const data = localStorage.getItem(key)
    return data ? JSON.parse(data) : []
  },

  /**
   * 获取所有游客数据（用于迁移）
   */
  getAllGuestData: (guestId) => {
    return {
      vocabs: guestDataManager.getVocabs(guestId),
      grammars: guestDataManager.getGrammars(guestId),
      articles: guestDataManager.getArticles(guestId)
    }
  },

  /**
   * 清空游客数据
   */
  clearGuestData: (guestId) => {
    localStorage.removeItem(`${GUEST_DATA_PREFIX}${guestId}_vocab`)
    localStorage.removeItem(`${GUEST_DATA_PREFIX}${guestId}_grammar`)
    localStorage.removeItem(`${GUEST_DATA_PREFIX}${guestId}_articles`)
    console.log('🗑️ [GuestData] 已清空游客数据:', guestId)
  },

  /**
   * 检查游客是否有数据
   */
  hasGuestData: (guestId) => {
    const vocabs = guestDataManager.getVocabs(guestId)
    const grammars = guestDataManager.getGrammars(guestId)
    const articles = guestDataManager.getArticles(guestId)
    return vocabs.length > 0 || grammars.length > 0 || articles.length > 0
  }
}

export default guestDataManager

