import axios from "axios";

// ���� axios ʵ��
const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 60000,  // 增加到 60 秒，因为 AI 处理需要时间
  headers: {
    "Content-Type": "application/json",
  },
});

// ����������
api.interceptors.request.use(
  (config) => {
    console.log("API Request:", config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

// ��Ӧ������
api.interceptors.response.use(
  (response) => {
    console.log("API Response:", response.status, response.config.url);
    return response.data;
  },
  (error) => {
    console.error("API Response Error:", error?.response?.status, error?.message);
    return Promise.reject(error);
  }
);

// API ����
export const apiService = {
  // �������
  healthCheck: () => api.get("/api/health"),

  // ���ʲ�ѯ
  getWordInfo: (text) => api.get(`/api/word?text=${encodeURIComponent(text)}`),

  // ��ȡ�ʻ��б�
  getVocabList: () => api.get("/api/vocab"),

  // ��ȡ�����ʻ�����
  getVocabById: (id) => api.get(`/api/vocab/${id}`),

  // ��ȡ�﷨�����б�
  getGrammarList: () => api.get("/api/grammar"),

  // ��ȡ�����﷨��������
  getGrammarById: (id) => api.get(`/api/grammar/${id}`),

  // ��ȡͳ������
  getStats: () => api.get("/api/stats"),

  // ��ȡ�����б�ժҪ
  getArticlesList: () => api.get("/api/articles"),

  // ��ȡ��������
  getArticleById: (id) => api.get(`/api/articles/${id}`),

  // ��������ȡ�ʻ����
  getVocabExplanation: (word, context = "") => {
    // Ŀǰ���ز�������
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

  // 切换词汇收藏状态
  toggleVocabStar: (id, isStarred) => api.put(`/api/vocab/${id}/star`, { is_starred: isStarred }),

  // 切换语法规则收藏状态
  toggleGrammarStar: (id, isStarred) => api.put(`/api/grammar/${id}/star`, { is_starred: isStarred }),

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
  }
};

export default api;
