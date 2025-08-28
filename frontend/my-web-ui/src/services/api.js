import axios from 'axios';

// 创建 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response.data;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// API 函数
export const apiService = {
  // 健康检查
  healthCheck: () => api.get('/api/health'),
  
  // 按词查询
  getWordInfo: (text) => api.get(`/api/word?text=${encodeURIComponent(text)}`),
  
  // 获取词汇列表
  getVocabList: () => api.get('/api/vocab'),
  
  // 获取单个词汇详情
  getVocabById: (id) => api.get(`/api/vocab/${id}`),
  
  // 获取语法规则列表
  getGrammarList: () => api.get('/api/grammar'),
  
  // 获取单个语法规则详情
  getGrammarById: (id) => api.get(`/api/grammar/${id}`),
  
  // 获取统计数据
  getStats: () => api.get('/api/stats'),
};

export default api;
