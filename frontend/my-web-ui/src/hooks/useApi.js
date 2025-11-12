import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api.js';
import guestDataManager from '../utils/guestDataManager.js';

// React Query 配置 - 添加 userId 到 queryKeys
export const queryKeys = {
  health: ['health'],
  word: (text) => ['word', text],
  vocab: {
    all: (userId) => ['vocab', userId],  // 添加 userId
    detail: (id, userId) => ['vocab', id, userId],  // 添加 userId
  },
  grammar: {
    all: (userId) => ['grammar', userId],  // 添加 userId
    detail: (id, userId) => ['grammar', id, userId],  // 添加 userId
  },
  stats: (userId) => ['stats', userId],  // 添加 userId
  articles: {
    all: (userId) => ['articles', userId],  // 添加 userId
    detail: (id, userId) => ['articles', id, userId],  // 添加 userId
  },
};

// 健康检查 Hook
export const useHealthCheck = () => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: apiService.healthCheck,
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};

// 按词查询 Hook
export const useWordInfo = (text) => {
  return useQuery({
    queryKey: queryKeys.word(text),
    queryFn: () => apiService.getWordInfo(text),
    enabled: !!text, // 只有当 text 存在时才执行查询
    staleTime: 10 * 60 * 1000, // 10分钟
  });
};

// 获取词汇列表 Hook - 支持游客模式
export const useVocabList = (userId = null, isGuest = false) => {
  return useQuery({
    queryKey: queryKeys.vocab.all(userId),
    queryFn: isGuest ? async () => {
      // 游客模式：从 localStorage 获取数据
      const vocabs = guestDataManager.getVocabs(userId)
      console.log('👤 [useVocabList] 游客模式，加载本地数据:', vocabs.length, '条')
      return { data: vocabs }
    } : apiService.getVocabList,
    enabled: userId !== null,  // 游客和登录用户都可以查询
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};

// 获取单个词汇详情 Hook
export const useVocabDetail = (id) => {
  return useQuery({
    queryKey: queryKeys.vocab.detail(id),
    queryFn: () => apiService.getVocabById(id),
    enabled: !!id, // 只有当 id 存在时才执行查询
    staleTime: 10 * 60 * 1000, // 10分钟
  });
};

// 获取语法规则列表 Hook - 支持游客模式
export const useGrammarList = (userId = null, isGuest = false) => {
  return useQuery({
    queryKey: queryKeys.grammar.all(userId),
    queryFn: isGuest ? async () => {
      // 游客模式：从 localStorage 获取数据
      const grammars = guestDataManager.getGrammars(userId)
      console.log('👤 [useGrammarList] 游客模式，加载本地数据:', grammars.length, '条')
      return { data: grammars }
    } : apiService.getGrammarList,
    enabled: userId !== null,  // 游客和登录用户都可以查询
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};

// 获取单个语法规则详情 Hook
export const useGrammarDetail = (id) => {
  return useQuery({
    queryKey: queryKeys.grammar.detail(id),
    queryFn: () => apiService.getGrammarById(id),
    enabled: !!id, // 只有当 id 存在时才执行查询
    staleTime: 10 * 60 * 1000, // 10分钟
  });
};

// 获取统计数据 Hook
export const useStats = (userId = null) => {
  return useQuery({
    queryKey: queryKeys.stats(userId),
    queryFn: apiService.getStats,
    staleTime: 2 * 60 * 1000, // 2分钟
  });
};

// 刷新数据的 Hook
export const useRefreshData = () => {
  const queryClient = useQueryClient();
  
  const refreshAll = () => {
    // 刷新所有用户的缓存（使用部分匹配）
    queryClient.invalidateQueries({ queryKey: ['vocab'] });
    queryClient.invalidateQueries({ queryKey: ['grammar'] });
    queryClient.invalidateQueries({ queryKey: ['stats'] });
    queryClient.invalidateQueries({ queryKey: ['articles'] });
  };
  
  const refreshVocab = () => {
    queryClient.invalidateQueries({ queryKey: ['vocab'] });
  };
  
  const refreshGrammar = () => {
    queryClient.invalidateQueries({ queryKey: ['grammar'] });
  };

  const refreshArticles = () => {
    queryClient.invalidateQueries({ queryKey: ['articles'] });
  };
  
  return {
    refreshAll,
    refreshVocab,
    refreshGrammar,
    refreshArticles,
  };
};

// 获取文章列表 Hook - 支持 userId
export const useArticles = (userId = null) => {
  return useQuery({
    queryKey: queryKeys.articles.all(userId),
    queryFn: apiService.getArticlesList,
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};

// 获取文章详情 Hook - 支持 userId
export const useArticle = (id, userId = null) => {
  return useQuery({
    queryKey: queryKeys.articles.detail(id, userId),
    queryFn: () => apiService.getArticleById(id),
    enabled: !!id, // 只有当 id 存在时才执行查询
    staleTime: 10 * 60 * 1000, // 10分钟
  });
};

// 切换词汇收藏状态 Hook
export const useToggleVocabStar = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, isStarred }) => apiService.toggleVocabStar(id, isStarred),
    onSuccess: () => {
      // 刷新词汇列表
      queryClient.invalidateQueries({ queryKey: queryKeys.vocab.all });
    },
  });
};

// 切换语法规则收藏状态 Hook
export const useToggleGrammarStar = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, isStarred }) => apiService.toggleGrammarStar(id, isStarred),
    onSuccess: () => {
      // 刷新语法规则列表
      queryClient.invalidateQueries({ queryKey: queryKeys.grammar.all });
    },
  });
};