import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api.js';
import guestDataManager from '../utils/guestDataManager.js';

const normalizeLanguageKey = (language) => {
  if (!language) return null;
  const value = String(language).trim().toLowerCase().replace(/_/g, '-');
  const aliasToKey = {
    'zh': 'zh',
    'zh-cn': 'zh',
    'zh-hans': 'zh',
    '中文': 'zh',
    'chinese': 'zh',
    'en': 'en',
    'en-us': 'en',
    '英文': 'en',
    '英语': 'en',
    'english': 'en',
    'de': 'de',
    'de-de': 'de',
    '德文': 'de',
    '德语': 'de',
    'german': 'de',
    'es': 'es',
    'es-es': 'es',
    '西班牙语': 'es',
    'spanish': 'es',
    'fr': 'fr',
    'fr-fr': 'fr',
    '法语': 'fr',
    'french': 'fr',
    'ja': 'ja',
    'ja-jp': 'ja',
    '日语': 'ja',
    '日文': 'ja',
    '日本語': 'ja',
    'japanese': 'ja',
    'ko': 'ko',
    'ko-kr': 'ko',
    '韩语': 'ko',
    'korean': 'ko',
    'ar': 'ar',
    'ar-sa': 'ar',
    '阿拉伯语': 'ar',
    'arabic': 'ar',
    'ru': 'ru',
    'ru-ru': 'ru',
    '俄语': 'ru',
    'russian': 'ru',
  };
  return aliasToKey[value] || value;
};

const matchesSelectedLanguage = (itemLanguage, selectedLanguage) => {
  if (!selectedLanguage || selectedLanguage === 'all') return true;
  const target = normalizeLanguageKey(selectedLanguage);
  const current = normalizeLanguageKey(itemLanguage);
  return !!target && !!current && target === current;
};

const filterListByLanguage = (items, selectedLanguage, label) => {
  if (!Array.isArray(items) || !selectedLanguage || selectedLanguage === 'all') {
    return items;
  }
  const filtered = items.filter((item) => matchesSelectedLanguage(item?.language, selectedLanguage));
  if (filtered.length !== items.length) {
    console.log(`🔍 [useApi] ${label} 前端语言兜底过滤生效: ${items.length} -> ${filtered.length} (${selectedLanguage})`);
  }
  return filtered;
};

const filterResponseDataByLanguage = (response, selectedLanguage, label) => {
  if (!selectedLanguage || selectedLanguage === 'all') {
    return response;
  }
  if (Array.isArray(response)) {
    return filterListByLanguage(response, selectedLanguage, label);
  }
  if (response && Array.isArray(response.data)) {
    const filtered = filterListByLanguage(response.data, selectedLanguage, label);
    return {
      ...response,
      data: filtered,
      count: filtered.length,
    };
  }
  return response;
};

// React Query 配置 - 添加 userId 到 queryKeys
export const queryKeys = {
  health: ['health'],
  word: (text) => ['word', text],
  vocab: {
    all: (userId, language, learnStatus, textId) => ['vocab', userId, language, learnStatus, textId],  // 添加 userId、language、learnStatus 和 textId
    detail: (id, userId) => ['vocab', id, userId],  // 添加 userId
  },
  grammar: {
    all: (userId, language, learnStatus, textId) => ['grammar', userId, language, learnStatus, textId],  // 添加 userId、language、learnStatus 和 textId
    detail: (id, userId) => ['grammar', id, userId],  // 添加 userId
  },
  stats: (userId) => ['stats', userId],  // 添加 userId
  articles: {
    all: (userId, language) => ['articles', userId, language],  // 添加 userId 和 language
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

// 获取词汇列表 Hook - 支持游客模式和语言过滤
export const useVocabList = (userId = null, isGuest = false, language = null, learnStatus = null, textId = null) => {
  return useQuery({
    queryKey: queryKeys.vocab.all(userId, language, learnStatus, textId),
    queryFn: async () => {
      if (isGuest) {
        // 游客模式：从 localStorage 获取数据
        let vocabs = guestDataManager.getVocabs(userId)
        vocabs = filterListByLanguage(vocabs, language, 'vocab')
        // 在本地过滤学习状态
        if (learnStatus && learnStatus !== 'all') {
          vocabs = vocabs.filter(v => (v.learn_status || 'not_mastered') === learnStatus)
        }
        // 在本地过滤文章（需要检查 examples 中是否有该 text_id）
        if (textId && textId !== 'all') {
          vocabs = vocabs.filter(v => {
            const examples = v.examples || []
            return examples.some(ex => ex.text_id === Number(textId))
          })
        }
        console.log('👤 [useVocabList] 游客模式，加载本地数据:', vocabs.length, '条', language ? `(语言: ${language})` : '', learnStatus ? `(状态: ${learnStatus})` : '', textId ? `(文章: ${textId})` : '')
        return { data: vocabs, count: vocabs.length }
      }

      const response = await apiService.getVocabList(language, learnStatus, textId)
      return filterResponseDataByLanguage(response, language, 'vocab')
    },
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

// 获取语法规则列表 Hook - 支持游客模式和语言过滤
export const useGrammarList = (userId = null, isGuest = false, language = null, learnStatus = null, textId = null) => {
  return useQuery({
    queryKey: queryKeys.grammar.all(userId, language, learnStatus, textId),
    queryFn: async () => {
      if (isGuest) {
        // 游客模式：从 localStorage 获取数据
        let grammars = guestDataManager.getGrammars(userId)
        grammars = filterListByLanguage(grammars, language, 'grammar')
        // 在本地过滤学习状态
        if (learnStatus && learnStatus !== 'all') {
          grammars = grammars.filter(g => (g.learn_status || 'not_mastered') === learnStatus)
        }
        // 在本地过滤文章（需要检查 examples 中是否有该 text_id）
        if (textId && textId !== 'all') {
          grammars = grammars.filter(g => {
            const examples = g.examples || []
            return examples.some(ex => ex.text_id === Number(textId))
          })
        }
        console.log('👤 [useGrammarList] 游客模式，加载本地数据:', grammars.length, '条', language ? `(语言: ${language})` : '', learnStatus ? `(状态: ${learnStatus})` : '', textId ? `(文章: ${textId})` : '')
        return { data: grammars, count: grammars.length }
      }

      const response = await apiService.getGrammarList(language, learnStatus, textId)
      return filterResponseDataByLanguage(response, language, 'grammar')
    },
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

// 获取文章列表 Hook - 支持 userId、isGuest 和 language
export const useArticles = (userId = null, language = null, isGuest = false) => {
  return useQuery({
    queryKey: queryKeys.articles.all(userId, language),
    queryFn: isGuest ? async () => {
      // 游客模式：从 localStorage 获取数据
      let articles = guestDataManager.getArticles(userId)
      // 在本地过滤语言
      if (language && language !== 'all') {
        articles = articles.filter(a => a.language === language)
      }
      console.log('👤 [useArticles] 游客模式，加载本地数据:', articles.length, '条', language ? `(语言: ${language})` : '')
      return { data: articles }
    } : () => apiService.getArticlesList(language),
    enabled: userId !== null,  // 游客和登录用户都可以查询（userId 不为 null）
    staleTime: 5 * 60 * 1000, // 5分钟
    retry: 2, // 失败时重试2次
    retryDelay: 1000, // 重试延迟1秒
  });
};

// 获取文章详情 Hook - 支持 userId
export const useArticle = (id, userId = null) => {
  // 🔧 检查id是否为有效数字（上传模式下可能是字符串'upload'）
  const isValidId = id && id !== 'upload' && (typeof id === 'number' || !isNaN(parseInt(id)))
  
  return useQuery({
    queryKey: queryKeys.articles.detail(id, userId),
    queryFn: () => apiService.getArticleById(id),
    enabled: isValidId, // 只有当 id 存在且有效时才执行查询
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