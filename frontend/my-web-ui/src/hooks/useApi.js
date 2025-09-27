import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api.js';

// React Query 配置
export const queryKeys = {
  health: ['health'],
  word: (text) => ['word', text],
  vocab: {
    all: ['vocab'],
    detail: (id) => ['vocab', id],
  },
  grammar: {
    all: ['grammar'],
    detail: (id) => ['grammar', id],
  },
  stats: ['stats'],
  articles: {
    all: ['articles'],
    detail: (id) => ['articles', id],
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

// 获取词汇列表 Hook
export const useVocabList = () => {
  return useQuery({
    queryKey: queryKeys.vocab.all,
    queryFn: apiService.getVocabList,
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

// 获取语法规则列表 Hook
export const useGrammarList = () => {
  return useQuery({
    queryKey: queryKeys.grammar.all,
    queryFn: apiService.getGrammarList,
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
export const useStats = () => {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: apiService.getStats,
    staleTime: 2 * 60 * 1000, // 2分钟
  });
};

// 刷新数据的 Hook
export const useRefreshData = () => {
  const queryClient = useQueryClient();
  
  const refreshAll = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.vocab.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.grammar.all });
    queryClient.invalidateQueries({ queryKey: queryKeys.stats });
    queryClient.invalidateQueries({ queryKey: queryKeys.articles.all });
  };
  
  const refreshVocab = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.vocab.all });
  };
  
  const refreshGrammar = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.grammar.all });
  };

  const refreshArticles = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.articles.all });
  };
  
  return {
    refreshAll,
    refreshVocab,
    refreshGrammar,
    refreshArticles,
  };
};

// 获取文章列表 Hook
export const useArticles = () => {
  return useQuery({
    queryKey: queryKeys.articles.all,
    queryFn: apiService.getArticlesList,
    staleTime: 5 * 60 * 1000, // 5分钟
  });
};

// 获取文章详情 Hook
export const useArticle = (id) => {
  return useQuery({
    queryKey: queryKeys.articles.detail(id),
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