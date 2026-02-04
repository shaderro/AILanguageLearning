import axios from "axios";

// 环境切换优先级：
// 生产环境：强制使用 db（忽略 URL 参数和 localStorage）
// 开发环境：URL 参数 > localStorage > VITE_API_TARGET > 默认 db
// 用法：
//  - 在地址栏加 ?api=mock 或 ?api=db（仅开发环境有效）
//  - 或者在控制台执行 localStorage.setItem('API_TARGET','mock')（仅开发环境有效）
//  - 或者使用 VITE_API_TARGET=mock 启动
function getApiTarget() {
  // 🔧 生产环境强制使用 db 模式（确保上线版本使用正确的 API）
  const isProduction = import.meta.env.PROD || 
    (typeof window !== 'undefined' && 
     !window.location.hostname.includes('localhost') && 
     !window.location.hostname.includes('127.0.0.1'));
  
  if (isProduction) {
    // 生产环境：强制使用 db，忽略所有其他设置
    return 'db';
  }
  
  // 开发环境：允许通过 URL 参数、localStorage 或环境变量切换
  try {
    const url = new URL(window.location.href);
    const param = url.searchParams.get('api');
    if (param === 'mock' || param === 'db') return param;
  } catch {}
  const saved = (typeof localStorage !== 'undefined' && localStorage.getItem('API_TARGET')) || '';
  if (saved === 'mock' || saved === 'db') return saved;
  const envVal = (import.meta?.env?.VITE_API_TARGET || '').toLowerCase();
  if (envVal === 'mock' || envVal === 'db') return envVal;
  return 'db'; // 默认使用数据库模式
}
const API_TARGET = getApiTarget();
// 从环境变量获取 API 基础 URL，默认使用 localhost:8000（本地开发）
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// 创建 axios 实例
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 增加到 2 分钟
  headers: { "Content-Type": "application/json" },
});

console.log(`[API] Target: ${API_TARGET} → ${BASE_URL}`);

// 请求拦截器 - 添加 JWT token
api.interceptors.request.use(
  (config) => {
    console.log("🌐 API Request:", config.method?.toUpperCase(), config.url);
    
    // 🔧 从 localStorage 获取 token 并添加到请求头
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log("🔑 Added Authorization header with token:", token.substring(0, 20) + "...");
    } else {
      console.warn("⚠️ No access token found in localStorage - API request may fail with 401");
    }
    
    // 🔧 如果是 FormData，移除 Content-Type 让浏览器自动设置（包含 boundary）
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
      console.log("📎 FormData detected, letting browser set Content-Type");
    }
    
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
    
    // 🔧 特殊处理：错误响应格式 { status: "error", data: {...}, error: "..." }
    if (response.data && response.data.status === 'error') {
      console.log("🔍 [DEBUG] Detected error response format, returning full response.data");
      return response.data;
    }
    
    // 🔧 特殊处理：成功响应格式 { status: "success", data: {...}, message: "..." }
    if (response.data && response.data.status === 'success') {
      console.log("🔍 [DEBUG] Detected success response format with status field");
      // 返回整个 response.data，包含 status, data, message
      return response.data;
    }
    
    // 🔧 特殊处理：pending-knowledge API 需要保留完整结构
    if (urlPath.includes('/api/chat/pending-knowledge')) {
      console.log('🔍 [DEBUG] PendingKnowledge endpoint detected - returning full response.data');
      return response.data;
    }
    
    // 数据库API返回格式: { success: true, data: {...} }
    // Mock API返回格式: 直接返回数据
    if (response.data && response.data.success !== undefined) {
      console.log("🔍 [DEBUG] Detected database API format");
      // 数据库API格式 - 提取内层data
      const innerData = response.data.data;
      console.log("🔍 [DEBUG] Inner data:", innerData);
      
      // 🔧 特殊处理：如果 innerData 是 undefined，说明响应格式是 { success: true, message: '...' }
      // 这种情况下直接返回整个 response.data
      if (innerData === undefined) {
        console.log("🔍 [DEBUG] innerData is undefined, returning full response.data");
        return response.data;
      }
      
      // 🔧 Chat API 特殊处理：优先检查并保留 created_grammar_notations 和 created_vocab_notations
      // 必须在检查其他字段之前处理，避免提前返回导致丢失数据
      if (innerData && typeof innerData === 'object' && 
          (innerData.created_grammar_notations !== undefined || innerData.created_vocab_notations !== undefined)) {
        console.log("🔍 [DEBUG] Chat API detected - preserving created_grammar_notations and created_vocab_notations");
        console.log("🔍 [DEBUG] innerData 完整内容:", JSON.stringify(innerData, null, 2));
        console.log("🔍 [DEBUG] created_grammar_notations:", innerData.created_grammar_notations);
        console.log("🔍 [DEBUG] created_grammar_notations 类型:", typeof innerData.created_grammar_notations);
        console.log("🔍 [DEBUG] created_grammar_notations 长度:", Array.isArray(innerData.created_grammar_notations) ? innerData.created_grammar_notations.length : 'not array');
        console.log("🔍 [DEBUG] created_vocab_notations:", innerData.created_vocab_notations);
        console.log("🔍 [DEBUG] created_vocab_notations 类型:", typeof innerData.created_vocab_notations);
        console.log("🔍 [DEBUG] created_vocab_notations 长度:", Array.isArray(innerData.created_vocab_notations) ? innerData.created_vocab_notations.length : 'not array');
        console.log("🔍 [DEBUG] 返回 innerData（保留所有字段）");
        return innerData;
      }
      
      // 进一步提取列表数据（如果存在）
      // 🔧 优先检查数组格式（因为数组也是 object 类型）
      if (Array.isArray(innerData)) {
        // 检查是否是 vocab 数组（有 vocab_id 字段）
        // 🔧 修复：即使数组为空也要检查，通过 URL 路径判断
        const urlPath = response?.config?.url || '';
        if (urlPath.includes('/vocab') || (innerData.length > 0 && innerData[0].vocab_id !== undefined)) {
          console.log("🔍 [DEBUG] Found vocab array, returning as is");
          return {
            data: innerData,
            count: innerData.length
          };
        }
        // 检查是否是 grammar 数组（有 rule_id 字段）
        // 🔧 修复：即使数组为空也要检查，通过 URL 路径判断
        if (urlPath.includes('/grammar') || (innerData.length > 0 && innerData[0].rule_id !== undefined)) {
          // 🔧 使用后端返回的 count（如果存在），否则使用数组长度
          const count = response.data.count !== undefined ? response.data.count : innerData.length;
          return {
            data: innerData,
            count: count
          };
        }
        // Texts API - 如果直接是数组（向后兼容）
        console.log("🔍 [DEBUG] Found texts array, applying field mapping");
        const mappedTexts = innerData.map(text => ({
          ...text,
          id: text.text_id,
          title: text.text_title
        }));
        return {
          data: mappedTexts,
          count: innerData.length
        };
      }
      
      // API返回 { vocabs: [...], count: X } -> 提取vocabs数组
      if (innerData && typeof innerData === 'object') {
        console.log("🔍 [DEBUG] Inner data keys:", Object.keys(innerData));
        
        // 检查常见的列表字段名
        if (innerData.vocabs) {
          console.log("🔍 [DEBUG] Found vocabs, applying field mapping");
          // 映射字段名：vocab_body -> vocab
          const mappedVocabs = innerData.vocabs.map(v => ({
            ...v,
            vocab: v.vocab_body || v.vocab,  // 前端可能期望 vocab
            id: v.vocab_id                    // 前端可能期望 id
          }));
          console.log("🔍 [DEBUG] Mapped vocabs:", mappedVocabs[0]);
          return {
            data: mappedVocabs,
            count: innerData.count,
            skip: innerData.skip,
            limit: innerData.limit
          };
        }
        
        // 单个 Vocab - 需要字段名映射并保持 { data: {...} } 格式
        if (innerData.vocab_id && innerData.vocab_body !== undefined) {
          console.log("🔍 [DEBUG] Found single vocab, applying field mapping");
          const mappedVocab = {
            ...innerData,
            vocab: innerData.vocab_body,     // 前端期望 vocab
            id: innerData.vocab_id           // 前端期望 id
          };
          console.log("🔍 [DEBUG] Mapped vocab:", mappedVocab);
          // 返回包装格式，让前端可以用 response.data 访问
          return {
            data: mappedVocab
          };
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
        
        // 单个 Grammar Rule - 需要字段名映射并保持 { data: {...} } 格式
        if (innerData.rule_id && innerData.name !== undefined) {
          console.log("🔍 [DEBUG] Found single grammar rule, applying field mapping");
          const mappedRule = {
            ...innerData,
            rule_name: innerData.name,           // 前端期望 rule_name
            rule_summary: innerData.explanation  // 前端期望 rule_summary
          };
          console.log("🔍 [DEBUG] Mapped rule:", mappedRule);
          // 返回包装格式，让前端可以用 response.data 访问
          return {
            data: mappedRule
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
        
        // 单个 Text 详情 - 包含 text_id, text_title, sentences
        // 🔧 修复：即使 sentences 为空数组或 undefined，只要有 text_id 就应该返回完整结构
        if (innerData.text_id !== undefined) {
          console.log("🔍 [DEBUG] Found single text (text_id present)");
          console.log("🔍 [DEBUG] Text data keys:", Object.keys(innerData));
          console.log("🔍 [DEBUG] Has sentences:", !!innerData.sentences);
          console.log("🔍 [DEBUG] Sentences type:", Array.isArray(innerData.sentences) ? 'array' : typeof innerData.sentences);
          console.log("🔍 [DEBUG] Sentences length:", Array.isArray(innerData.sentences) ? innerData.sentences.length : 'N/A');
          // 返回包装格式，让前端可以用 response.data 访问
          return {
            data: innerData
          };
        }
        
        // 🔧 如果只有 sentences 数组但没有 text_id，可能是单独的句子列表 API
        if (innerData.sentences && !innerData.text_id) {
          console.log("🔍 [DEBUG] Returning sentences array (no text_id)");
          return innerData.sentences;
        }
        
        // Vocab notations API - 新格式 { notations: [...], count: N }
        if (innerData.notations) {
          console.log("🔍 [DEBUG] Found notations array (vocab/grammar)");
          // 返回完整结构，让调用者可以访问notations和count
          return {
            success: true,
            data: innerData
          };
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
    // 🔧 改进错误日志，提供更详细的信息
    if (error.code === 'ECONNABORTED') {
      console.error("❌ API Response Error: Request timeout", {
        url: error.config?.url,
        method: error.config?.method,
        timeout: error.config?.timeout,
        baseURL: error.config?.baseURL
      });
    } else if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      // 🔧 减少日志噪音：只在第一次网络错误时详细记录，后续只记录简要信息
      const errorKey = `network_error_${error.config?.url}`
      const errorCount = (window.__networkErrorCount || {})[errorKey] || 0
      window.__networkErrorCount = window.__networkErrorCount || {}
      window.__networkErrorCount[errorKey] = errorCount + 1
      
      if (errorCount === 0) {
        // 第一次错误，详细记录
        console.error("❌ API Response Error: Network Error", {
          url: error.config?.url,
          method: error.config?.method,
          baseURL: error.config?.baseURL,
          message: error.message,
          code: error.code,
          hint: '请检查后端服务是否运行在 ' + (error.config?.baseURL || BASE_URL)
        });
      } else if (errorCount < 3) {
        // 前3次错误，简要记录
        console.warn(`⚠️ [API] Network Error (${errorCount + 1}x): ${error.config?.method} ${error.config?.url}`)
      }
      // 超过3次后，不再记录日志，避免控制台被刷屏
    } else if (error.response) {
      // 服务器返回了错误响应
      console.error("❌ API Response Error:", error.response.status, error.response.statusText, {
        url: error.config?.url,
        method: error.config?.method,
        data: error.response.data
      });
    } else {
      // 其他错误
      console.error("❌ API Response Error:", error?.response?.status, error?.message, {
        url: error.config?.url,
        method: error.config?.method,
        code: error.code
      });
    }
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
  getVocabList: async (language = null, learnStatus = null, textId = null) => {
    try {
      if (API_TARGET === 'mock') {
        return api.get("/api/vocab");
      } else {
        // 数据库模式：只使用 v2 API（有用户隔离），不再回退到旧端点
        // 旧端点（/api/vocab）没有用户隔离，会导致不同用户看到同一份数据
          const params = new URLSearchParams();
          if (language && language !== 'all') {
            params.append('language', language);
          }
          if (learnStatus && learnStatus !== 'all') {
            params.append('learn_status', learnStatus);
          }
          if (textId && textId !== 'all') {
            params.append('text_id', textId);
          }
          const queryString = params.toString();
          const url = queryString ? `/api/v2/vocab/?${queryString}` : '/api/v2/vocab/';
          console.log(`🔍 [Frontend API] getVocabList called: language=${language}, learnStatus=${learnStatus}, textId=${textId}, url=${url}`);
          return await api.get(url);
      }
    } catch (e) {
      console.error('❌ [API] 获取词汇列表失败:', e);
      throw e;
    }
  },

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
  updateVocab: (id, vocabData) => api.put(API_TARGET === 'mock' ? `/api/vocab/${id}` : `/api/v2/vocab/${id}`, vocabData),

  // 删除词汇
  deleteVocab: (id) => api.delete(API_TARGET === 'mock' ? `/api/vocab/${id}` : `/api/v2/vocab/${id}/`),

  // ==================== Grammar API（数据库版本）====================
  
  // 获取语法规则列表
  // Grammar
  getGrammarList: async (language = null, learnStatus = null, textId = null) => {
    try {
      if (API_TARGET === 'mock') {
        return api.get("/api/grammar");
      } else {
        // 数据库模式：只使用 v2 API（有用户隔离），不再回退到旧端点
        // 旧端点（/api/grammar）没有用户隔离，会导致不同用户看到同一份数据
          const params = new URLSearchParams();
          if (language && language !== 'all') {
            params.append('language', language);
          }
          if (learnStatus && learnStatus !== 'all') {
            params.append('learn_status', learnStatus);
          }
          if (textId && textId !== 'all') {
            params.append('text_id', textId);
          }
          const queryString = params.toString();
          const url = queryString ? `/api/v2/grammar/?${queryString}` : '/api/v2/grammar/';
          console.log(`🔍 [Frontend API] getGrammarList called: language=${language}, learnStatus=${learnStatus}, textId=${textId}, url=${url}`);
          return await api.get(url);
      }
    } catch (e) {
      console.error('❌ [API] 获取语法列表失败:', e);
      throw e;
    }
  },

  // 获取单个语法规则详情
  getGrammarById: (id) => api.get(API_TARGET === 'mock' ? `/api/grammar/${id}` : `/api/v2/grammar/${id}`),

  // 搜索语法规则
  searchGrammar: (keyword) => 
    api.get(API_TARGET === 'mock'
      ? `/api/grammar?keyword=${encodeURIComponent(keyword)}`
      : `/api/v2/grammar/search/?keyword=${encodeURIComponent(keyword)}`),

  // 创建语法规则
  createGrammar: (grammarData) => api.post(API_TARGET === 'mock' ? "/api/grammar" : "/api/v2/grammar/", grammarData),

  // 更新语法规则
  updateGrammar: (id, grammarData) => api.put(API_TARGET === 'mock' ? `/api/grammar/${id}` : `/api/v2/grammar/${id}`, grammarData),

  // 删除语法规则
  deleteGrammar: (id) => api.delete(API_TARGET === 'mock' ? `/api/grammar/${id}` : `/api/v2/grammar/${id}/`),

  // 获取语法注释列表
  getGrammarNotations: (textId, userId) => {
    // 🔧 验证textId是否为有效数字（上传模式下可能是字符串'upload'）
    if (typeof textId === 'string' && (textId === 'upload' || isNaN(parseInt(textId)))) {
      console.warn(`⚠️ [Frontend] Invalid textId for getGrammarNotations: ${textId}`);
      return Promise.reject(new Error(`Invalid textId: ${textId}. Expected a number.`));
    }
    // 🔧 确保 textId 是数字类型（如果传入的是字符串数字，转换为数字）
    const textIdInt = typeof textId === 'string' ? parseInt(textId) : textId
    if (isNaN(textIdInt)) {
      console.warn(`⚠️ [Frontend] Invalid textId for getGrammarNotations: ${textId}`);
      return Promise.reject(new Error(`Invalid textId: ${textId}. Expected a number.`));
    }
    // 🔧 如果没有传入 userId，从 localStorage 获取
    if (!userId) {
      const storedUserId = localStorage.getItem('user_id')
      userId = storedUserId ? parseInt(storedUserId) : 1  // 默认 User 1
    }
    
    // 🔧 统一使用数据库API路径，确保 text_id 是数字
    const url = `/api/v2/notations/grammar?text_id=${textIdInt}${userId ? `&user_id=${userId}` : ''}`
    console.log(`🔍 [API] getGrammarNotations: ${url}`)
    return api.get(url).catch(error => {
      // 🔧 如果是404错误，返回空数组而不是抛出错误，避免无限重试
      if (error.response && error.response.status === 404) {
        console.warn(`⚠️ [API] Grammar notations not found for textId=${textIdInt}, returning empty array`)
        return { data: { success: true, data: { notations: [], count: 0 } } }
      }
      throw error
    })
  },

  // 获取句子的语法规则
  getSentenceGrammarRules: (textId, sentenceId) => 
    api.get(API_TARGET === 'mock' 
      ? `/api/grammar_notations/${textId}/${sentenceId}` 
      : `/api/v2/notations/grammar/${textId}/${sentenceId}`),

  // 获取词汇注释列表
  getVocabNotations: (textId, userId) => {
    // 🔧 验证textId是否为有效数字（上传模式下可能是字符串'upload'）
    if (typeof textId === 'string' && (textId === 'upload' || isNaN(parseInt(textId)))) {
      console.warn(`⚠️ [Frontend] Invalid textId for getVocabNotations: ${textId}`);
      return Promise.reject(new Error(`Invalid textId: ${textId}. Expected a number.`));
    }
    // 🔧 确保 textId 是数字类型（如果传入的是字符串数字，转换为数字）
    const textIdInt = typeof textId === 'string' ? parseInt(textId) : textId
    if (isNaN(textIdInt)) {
      console.warn(`⚠️ [Frontend] Invalid textId for getVocabNotations: ${textId}`);
      return Promise.reject(new Error(`Invalid textId: ${textId}. Expected a number.`));
    }
    // 🔧 如果没有传入 userId，从 localStorage 获取
    if (!userId) {
      const storedUserId = localStorage.getItem('user_id')
      userId = storedUserId ? parseInt(storedUserId) : 1  // 默认 User 1
    }
    
    // 🔧 统一使用数据库API路径，确保 text_id 是数字
    const url = `/api/v2/notations/vocab?text_id=${textIdInt}${userId ? `&user_id=${userId}` : ''}`
    console.log(`🔍 [API] getVocabNotations: ${url}`)
    return api.get(url).catch(error => {
      // 🔧 如果是404错误，返回空数组而不是抛出错误，避免无限重试
      if (error.response && error.response.status === 404) {
        console.warn(`⚠️ [API] Vocab notations not found for textId=${textIdInt}, returning empty array`)
        return { data: { success: true, data: { notations: [], count: 0 } } }
      }
      throw error
    })
  },

  // 获取句子的词汇注释
  getSentenceVocabNotations: (textId, sentenceId) => 
    api.get(API_TARGET === 'mock' 
      ? `/api/vocab_notations/${textId}/${sentenceId}` 
      : `/api/v2/notations/vocab/${textId}/${sentenceId}`),

  // 创建词汇标注（新API）
  createVocabNotation: (userId, textId, sentenceId, tokenId, vocabId = null) => {
    // 🔧 如果没有传入 userId，从 localStorage 获取
    if (!userId) {
      const storedUserId = localStorage.getItem('user_id')
      userId = storedUserId ? parseInt(storedUserId) : 1  // 默认 User 1
    }
    
    console.log(`➕ [Frontend] Creating vocab notation: ${textId}:${sentenceId}:${tokenId}`, { userId, vocabId })
    return api.post(
      API_TARGET === 'mock' 
        ? '/api/user/asked-tokens'  // Mock服务器使用旧端点，但字段要按旧端点要求
        : '/api/v2/notations/vocab',
      API_TARGET === 'mock'
        ? {
            user_id: userId,
            text_id: textId,
            sentence_id: sentenceId,
            // 旧端点字段名为 sentence_token_id（不是 token_id）
            sentence_token_id: tokenId,
            vocab_id: vocabId
          }
        : {
            user_id: userId,
            text_id: textId,
            sentence_id: sentenceId,
            token_id: tokenId,
            vocab_id: vocabId
          }
    )
  },

  // ==================== Text/Article API（数据库版本）====================
  
  // 获取文章列表
  // Articles
  getArticlesList: async (language = null) => {
    try {
      if (API_TARGET === 'mock') {
        return api.get("/api/articles");
      } else {
        // 数据库模式：只使用 v2 API（有用户隔离），不再回退到文件系统
        // 文件系统API没有用户隔离，会导致显示不属于当前用户的文章
        try {
          const url = language && language !== 'all' 
            ? `/api/v2/texts/?language=${encodeURIComponent(language)}`
            : '/api/v2/texts/';
          const response = await api.get(url);
          // 即使数据库返回空，也不回退到文件系统（避免显示其他用户的文章）
          return response;
        } catch (dbError) {
          console.error('❌ [API] 数据库API失败:', dbError.message);
          // 不再回退到文件系统，直接抛出错误
          throw dbError;
        }
      }
    } catch (e) {
      console.error('❌ [API] 获取文章列表失败:', e);
      throw e;
    }
  },

  // 获取文章详情（包含句子）
  getArticleById: async (id) => {
    try {
      if (API_TARGET === 'mock') {
        return api.get(`/api/articles/${id}`);
      } else {
        // 数据库模式：只使用 v2 API（有用户隔离），不再回退到文件系统
        // 文件系统API没有用户隔离，会导致显示不属于当前用户的文章
        try {
          const dbResult = await api.get(`/api/v2/texts/${id}?include_sentences=true`);
          return dbResult;
        } catch (dbError) {
          console.error('❌ [API] 数据库API失败:', dbError.message);
          // 不再回退到文件系统，直接抛出错误（避免显示其他用户的文章）
          throw dbError;
        }
      }
    } catch (e) {
      console.error('❌ [API] 获取文章详情失败:', e);
      throw e;
    }
  },

  // 获取文章的句子列表（可选 limit）
  getArticleSentences: (textId, { limit } = {}) => {
    const query = limit ? `?limit=${encodeURIComponent(limit)}` : '';
    return api.get(
      API_TARGET === 'mock'
        ? `/api/articles/${textId}`
        : `/api/v2/texts/${textId}/sentences/${query}`,
    );
  },
  
  // 更新文章
  updateArticle: async (textId, updates) => {
    const response = await api.put(`/api/v2/texts/${textId}`, updates);
    return response;
  },
  
  // 删除文章
  deleteArticle: async (textId) => {
    const response = await api.delete(`/api/v2/texts/${textId}`);
    return response;
  },

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
  
  getAskedTokens: (userId, textId) => {
    // 🔧 如果没有传入 userId，从 localStorage 获取
    if (!userId) {
      const storedUserId = localStorage.getItem('user_id')
      userId = storedUserId ? parseInt(storedUserId) : 1  // 默认 User 1
    }
    
    // 🔧 验证textId是否为有效数字（上传模式下可能是字符串'upload'）
    if (typeof textId === 'string' && (textId === 'upload' || isNaN(parseInt(textId)))) {
      console.warn(`⚠️ [Frontend] Invalid textId for getAskedTokens: ${textId}`);
      return Promise.reject(new Error(`Invalid textId: ${textId}. Expected a number.`));
    }
    
    console.log(`🔍 [Frontend] Getting asked tokens for user=${userId}, text=${textId}`);
    return api.get(`/api/user/asked-tokens?user_id=${userId}&text_id=${textId}`);
  },

  markTokenAsked: (userId, textId, sentenceId, sentenceTokenId, vocabId = null, grammarId = null) => {
    // 🔧 如果没有传入 userId，从 localStorage 获取
    if (!userId) {
      const storedUserId = localStorage.getItem('user_id')
      userId = storedUserId ? parseInt(storedUserId) : 1  // 默认 User 1
    }
    
    console.log(`🏷️ [Frontend] Marking token as asked: ${textId}:${sentenceId}:${sentenceTokenId}`, { userId, vocabId, grammarId });
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
  // 如果只启动数据库API（8000），这些功能可能不可用
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
    // 测试开关：?fullFlow=1 或 localStorage.CHAT_FULL_FLOW = '1'
    const needFullFlow = (() => {
      try {
        const url = new URL(window.location.href);
        const q = (url.searchParams.get('fullFlow') || '').toLowerCase();
        if (q === '1' || q === 'true' || q === 'yes' || q === 'on') return true;
      } catch {}
      try {
        const v = (typeof localStorage !== 'undefined' && localStorage.getItem('CHAT_FULL_FLOW')) || '';
        if (v === '1' || v.toLowerCase() === 'true') return true;
      } catch {}
      return false;
    })();
    const finalPayload = needFullFlow ? { ...payload, full_flow: true } : payload;
    if (needFullFlow) console.log('🔧 [Frontend] full_flow enabled for this request');
    return api.post("/api/chat", finalPayload);
  },

  // 获取聊天历史（跨设备）
  getChatHistory: ({ textId = null, sentenceId = null, userId = null, limit = 100, offset = 0 } = {}) => {
    const params = {}
    // 🔧 确保 textId 和 sentenceId 是整数类型（如果提供）
    if (textId != null) {
      const textIdInt = parseInt(textId)
      if (!isNaN(textIdInt)) {
        params.text_id = textIdInt
      }
    }
    if (sentenceId != null) {
      const sentenceIdInt = parseInt(sentenceId)
      if (!isNaN(sentenceIdInt)) {
        params.sentence_id = sentenceIdInt
      }
    }
    if (userId != null) params.user_id = userId
    params.limit = limit
    params.offset = offset
    console.log('💬 [Frontend] Fetching chat history params:', params)
    return api.get("/api/chat/history", { params })
  },

  // 获取后台任务创建的新知识点（用于显示 toast）
  getPendingKnowledge: ({ user_id, text_id }) => {
    // 🔧 确保 text_id 是整数类型
    const textIdInt = parseInt(text_id) || text_id
    const userIdInt = parseInt(user_id) || user_id
    return api.get(`/api/chat/pending-knowledge?user_id=${userIdInt}&text_id=${textIdInt}`);
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
  },

  // ==================== Upload API ====================
  
  // 上传文件
  uploadFile: async (file, title = "Untitled Article", language = "") => {
    console.log('📤 [Frontend] Uploading file:', file.name, 'title:', title, 'language:', language);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('language', language);
    
    // 🔧 注意：不要手动设置 Content-Type，让浏览器自动设置（包含 boundary）
    // 🔧 增加超时时间到 10 分钟，因为处理大文件可能需要很长时间
    return api.post("/api/upload/file", formData, {
      timeout: 600000, // 10 分钟超时
      headers: {
        // 移除 Content-Type，让 axios 自动处理 FormData
      },
    });
  },

  // 上传URL
  uploadUrl: async (url, title = "URL Article", language = "") => {
    console.log('📤 [Frontend] Uploading URL:', url, 'title:', title, 'language:', language);
    const formData = new FormData();
    formData.append('url', url);
    formData.append('title', title);
    formData.append('language', language);
    
    // 🔧 注意：不要手动设置 Content-Type，让浏览器自动设置（包含 boundary）
    // 🔧 增加超时时间到 10 分钟，因为 URL 提取和处理大量文本可能需要很长时间
    return api.post("/api/upload/url", formData, {
      timeout: 600000, // 10 分钟超时
      headers: {
        // 移除 Content-Type，让 axios 自动处理 FormData
      },
    });
  },

  // 上传文本
  uploadText: async (text, title = "Text Article", language = "", skipLengthCheck = false) => {
    console.log('📤 [Frontend] Uploading text, title:', title, 'length:', text.length, 'language:', language, 'skipLengthCheck:', skipLengthCheck);
    console.log('📤 [Frontend] Text content preview (first 100 chars):', text.substring(0, 100));
    console.log('📤 [Frontend] Text content preview (last 100 chars):', text.substring(Math.max(0, text.length - 100)));
    const formData = new FormData();
    formData.append('text', text);
    formData.append('title', title);
    formData.append('language', language);
    if (skipLengthCheck) {
      formData.append('skip_length_check', 'true');
    }
    
    // 🔧 注意：不要手动设置 Content-Type，让浏览器自动设置（包含 boundary）
    return api.post("/api/upload/text", formData, {
      headers: {
        // 移除 Content-Type，让 axios 自动处理 FormData
      },
    });
  },
};

export default api;
