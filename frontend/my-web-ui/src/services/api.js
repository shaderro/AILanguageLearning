import axios from "axios";

// 环境切换优先级：URL 参数 > localStorage > VITE_API_TARGET > 默认 db
// 用法：
//  - 在地址栏加 ?api=mock 或 ?api=db
//  - 或者在控制台执行 localStorage.setItem('API_TARGET','mock')
//  - 或者使用 VITE_API_TARGET=mock 启动
function getApiTarget() {
  try {
    const url = new URL(window.location.href);
    const param = url.searchParams.get('api');
    if (param === 'mock' || param === 'db') return param;
  } catch {}
  const saved = (typeof localStorage !== 'undefined' && localStorage.getItem('API_TARGET')) || '';
  if (saved === 'mock' || saved === 'db') return saved;
  const envVal = (import.meta?.env?.VITE_API_TARGET || '').toLowerCase();
  if (envVal === 'mock' || envVal === 'db') return envVal;
  return 'mock';
}
const API_TARGET = getApiTarget();
const BASE_URL = API_TARGET === "mock" ? "http://localhost:8000" : "http://localhost:8001";

// 创建 axios 实例
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

console.log(`[API] Target: ${API_TARGET} → ${BASE_URL}`);

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log("🌐 API Request:", config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error("❌ API Request Error:", error);
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理数据库API格式
api.interceptors.response.use(
  (response) => {
    console.log("🔍 [DEBUG] API Response:", response.status, response.config.url);
    console.log("🔍 [DEBUG] Response data:", response.data);
    const urlPath = response?.config?.url || '';

    // 特例：Asked Tokens 接口需要保留完整包裹结构 { success, data }
    if (urlPath.startsWith('/api/user/asked-tokens')) {
      console.log('🔍 [DEBUG] AskedTokens endpoint detected - returning raw response.data');
      return response.data;
    }
    
    // 数据库API返回格式: { success: true, data: {...} }
    // Mock API返回格式: 直接返回数据
    if (response.data && response.data.success !== undefined) {
      console.log("🔍 [DEBUG] Detected database API format");
      // 数据库API格式 - 提取内层data
      const innerData = response.data.data;
      console.log("🔍 [DEBUG] Inner data:", innerData);
      
      // 进一步提取列表数据（如果存在）
      // API返回 { vocabs: [...], count: X } -> 提取vocabs数组
      if (innerData && typeof innerData === 'object') {
        console.log("🔍 [DEBUG] Inner data keys:", Object.keys(innerData));
        
        // 检查常见的列表字段名
        if (innerData.vocabs) {
          console.log("🔍 [DEBUG] Returning vocabs array");
          return innerData.vocabs;
        }
        
        // Grammar API - 需要字段名映射
        if (innerData.rules) {
          console.log("🔍 [DEBUG] Found rules, applying field mapping");
          // 映射字段名：name -> rule_name, explanation -> rule_summary
          const mappedRules = innerData.rules.map(rule => ({
            ...rule,
            rule_name: rule.name,           // 前端期望 rule_name
            rule_summary: rule.explanation  // 前端可能期望 rule_summary
          }));
          console.log("🔍 [DEBUG] Mapped rules:", mappedRules[0]);
          // 返回完整的数据结构，保持前端组件期望的格式
          return {
            data: mappedRules,
            count: innerData.count,
            skip: innerData.skip,
            limit: innerData.limit
          };
        }
        
        if (innerData.grammars) {
          console.log("🔍 [DEBUG] Returning grammars array");
          return innerData.grammars;
        }
        if (innerData.grammar_rules) {
          console.log("🔍 [DEBUG] Returning grammar_rules array");
          return innerData.grammar_rules;
        }
        
        // Texts API - 可能需要字段名映射
        if (innerData.texts) {
          console.log("🔍 [DEBUG] Found texts, applying field mapping");
          // 映射字段名：text_title -> title, text_id -> id
          const mappedTexts = innerData.texts.map(text => ({
            ...text,
            id: text.text_id,              // 前端期望 id
            title: text.text_title         // 前端期望 title
          }));
          console.log("🔍 [DEBUG] Mapped texts:", mappedTexts[0]);
          // 返回完整的数据结构，保持前端组件期望的格式
          return {
            data: mappedTexts,
            count: innerData.count,
            skip: innerData.skip,
            limit: innerData.limit
          };
        }
        
        if (innerData.sentences) {
          console.log("🔍 [DEBUG] Returning sentences array");
          return innerData.sentences;
        }
      }
      
      // 如果没有列表字段，返回整个innerData
      console.log("🔍 [DEBUG] No list fields found, returning innerData");
      return innerData;
    }
    
    // 其他格式直接返回
    console.log("🔍 [DEBUG] Not database API format, returning response.data");
    return response.data;
  },
  (error) => {
    console.error("❌ API Response Error:", error?.response?.status, error?.message);
    return Promise.reject(error);
  }
);

// API 服务
export const apiService = {
  // 健康检查（两端均支持）
  healthCheck: () => api.get("/api/health"),

  // ==================== Vocab API（数据库版本）====================
  
  // 获取词汇列表
  // Vocab
  getVocabList: () => api.get(API_TARGET === 'mock' ? "/api/vocab" : "/api/v2/vocab/"),

  // 获取单个词汇详情
  getVocabById: (id) => api.get(API_TARGET === 'mock' ? `/api/vocab/${id}` : `/api/v2/vocab/${id}/`),

  // 搜索词汇
  searchVocab: (keyword) => 
    api.get(API_TARGET === 'mock'
      ? `/api/vocab?keyword=${encodeURIComponent(keyword)}`
      : `/api/v2/vocab/search/?keyword=${encodeURIComponent(keyword)}`),

  // 创建词汇
  createVocab: (vocabData) => api.post(API_TARGET === 'mock' ? "/api/vocab" : "/api/v2/vocab/", vocabData),

  // 更新词汇
  updateVocab: (id, vocabData) => api.put(API_TARGET === 'mock' ? `/api/vocab/${id}` : `/api/v2/vocab/${id}/`, vocabData),

  // 删除词汇
  deleteVocab: (id) => api.delete(API_TARGET === 'mock' ? `/api/vocab/${id}` : `/api/v2/vocab/${id}/`),

  // ==================== Grammar API（数据库版本）====================
  
  // 获取语法规则列表
  // Grammar
  getGrammarList: () => api.get(API_TARGET === 'mock' ? "/api/grammar" : "/api/v2/grammar/"),

  // 获取单个语法规则详情
  getGrammarById: (id) => api.get(API_TARGET === 'mock' ? `/api/grammar/${id}` : `/api/v2/grammar/${id}/`),

  // 搜索语法规则
  searchGrammar: (keyword) => 
    api.get(API_TARGET === 'mock'
      ? `/api/grammar?keyword=${encodeURIComponent(keyword)}`
      : `/api/v2/grammar/search/?keyword=${encodeURIComponent(keyword)}`),

  // 创建语法规则
  createGrammar: (grammarData) => api.post(API_TARGET === 'mock' ? "/api/grammar" : "/api/v2/grammar/", grammarData),

  // 更新语法规则
  updateGrammar: (id, grammarData) => api.put(API_TARGET === 'mock' ? `/api/grammar/${id}` : `/api/v2/grammar/${id}/`, grammarData),

  // 删除语法规则
  deleteGrammar: (id) => api.delete(API_TARGET === 'mock' ? `/api/grammar/${id}` : `/api/v2/grammar/${id}/`),

  // 获取语法注释列表
  getGrammarNotations: (textId) => api.get(API_TARGET === 'mock' ? `/api/grammar_notations/${textId}` : `/api/v2/notations/grammar?text_id=${textId}`),

  // ==================== Text/Article API（数据库版本）====================
  
  // 获取文章列表
  // Articles
  getArticlesList: () => api.get(API_TARGET === 'mock' ? "/api/articles" : "/api/v2/texts/"),

  // 获取文章详情（包含句子）
  getArticleById: (id) => 
    api.get(API_TARGET === 'mock'
      ? `/api/articles/${id}`
      : `/api/v2/texts/${id}/?include_sentences=true`),

  // 获取文章的句子列表
  getArticleSentences: (textId) => 
    api.get(API_TARGET === 'mock'
      ? `/api/articles/${textId}`
      : `/api/v2/texts/${textId}/sentences/`),

  // 搜索文章
  searchArticles: (keyword) => 
    api.get(API_TARGET === 'mock'
      ? `/api/articles?keyword=${encodeURIComponent(keyword)}`
      : `/api/v2/texts/search/?keyword=${encodeURIComponent(keyword)}`),

  // ==================== 统计 API ====================
  
  // 获取统计数据
  getStats: () => api.get("/api/stats"),

  // ==================== 旧API（待迁移）====================
  
  // 按词查询（如果还在使用）
  getWordInfo: (text) => api.get(`/api/word?text=${encodeURIComponent(text)}`),

  // ==================== 词汇解释（临时假数据）====================
  
  getVocabExplanation: (word, context = "") => {
    // 临时返回假数据，实际应该调用后端AI API
    return Promise.resolve({
      word: word,
      definition: "This is a test explanation",
      examples: [],
      difficulty: "medium",
      lemma: word.toLowerCase(),
      pronunciation: `/${word.toLowerCase()}/`,
      partOfSpeech: "noun",
      etymology: `The word "${word}" has interesting historical origins.`,
      synonyms: [],
      antonyms: []
    });
  },

  // ==================== Asked Tokens API（JSON版本，保持不变）====================
  // 注意：这些端点仍然使用JSON文件存储，等数据结构最终确定后再迁移到数据库
  
  getAskedTokens: (userId = 'default_user', textId) => {
    console.log(`🔍 [Frontend] Getting asked tokens for user=${userId}, text=${textId}`);
    return api.get(`/api/user/asked-tokens?user_id=${userId}&text_id=${textId}`);
  },

  markTokenAsked: (userId = 'default_user', textId, sentenceId, sentenceTokenId, vocabId = null, grammarId = null) => {
    console.log(`🏷️ [Frontend] Marking token as asked: ${textId}:${sentenceId}:${sentenceTokenId}`, { vocabId, grammarId });
    return api.post('/api/user/asked-tokens', {
      user_id: userId,
      text_id: textId,
      sentence_id: sentenceId,
      sentence_token_id: sentenceTokenId,
      vocab_id: vocabId,
      grammar_id: grammarId
    });
  },

  // ==================== Session 和 Chat API（需要Mock服务器）====================
  // ⚠️ 注意：这些功能依赖Mock服务器的SessionState
  // 如果只启动数据库API（8001），这些功能可能不可用
  // 需要同时启动Mock服务器（8000）或将这些功能迁移到数据库版本
  
  // Session 管理
  session: {
    // 设置当前句子上下文
    setSentence: (sentenceData) => {
      console.log('🔵 [Frontend] Setting session sentence:', sentenceData);
      return api.post("/api/session/set_sentence", sentenceData);
    },

    // 设置选中的 token
    selectToken: (tokenData) => {
      console.log('🔵 [Frontend] Setting selected token:', tokenData);
      return api.post("/api/session/select_token", { token: tokenData });
    },

    // 一次性更新句子和 token（优化版，减少网络请求）
    updateContext: (contextData) => {
      console.log('🔵 [Frontend] Updating session context (batch):', contextData);
      return api.post("/api/session/update_context", contextData);
    },

    // 重置会话状态
    reset: () => {
      console.log('🔵 [Frontend] Resetting session state');
      return api.post("/api/session/reset", {});
    }
  },

  // 聊天功能
  sendChat: (payload = {}) => {
    console.log('💬 [Frontend] Sending chat request:', payload);
    return api.post("/api/chat", payload);
  },

  // 按位置查找词汇例句
  getVocabExampleByLocation: (textId, sentenceId = null, tokenIndex = null) => {
    console.log('🔍 [Frontend] Getting vocab example by location:', { textId, sentenceId, tokenIndex });
    const params = { text_id: textId };
    if (sentenceId !== null) params.sentence_id = sentenceId;
    if (tokenIndex !== null) params.token_index = tokenIndex;
    return api.get("/api/vocab-example-by-location", { params });
  },

  // 刷新词汇数据（从JSON文件重新加载）
  refreshVocab: () => {
    console.log('🔄 [Frontend] Refreshing vocab data');
    return api.post("/api/vocab/refresh");
  }
};

export default api;
