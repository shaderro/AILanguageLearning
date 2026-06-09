import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService, isMockApi } from '../services/api.js';
import guestDataManager from '../utils/guestDataManager.js';
import { enrichArticleListItem } from '../utils/articleMetadata.js';

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

const filterListByTextId = (items, textId) => {
  if (!Array.isArray(items) || !textId || textId === 'all') {
    return items;
  }
  const targetId = Number(textId);
  if (Number.isNaN(targetId)) {
    return items;
  }
  return items.filter((item) => {
    const examples = item?.examples || [];
    if (examples.some((ex) => Number(ex?.text_id ?? ex?.article_id) === targetId)) {
      return true;
    }
    const textIds = item?.example_text_ids || item?.source_text_ids || [];
    return Array.isArray(textIds) && textIds.some((id) => Number(id) === targetId);
  });
};

const filterResponseDataByTextId = (response, textId, label) => {
  if (!textId || textId === 'all') {
    return response;
  }
  if (Array.isArray(response)) {
    return filterListByTextId(response, textId);
  }
  if (response && Array.isArray(response.data)) {
    const filtered = filterListByTextId(response.data, textId);
    if (filtered.length !== response.data.length) {
      console.log(`🔍 [useApi] ${label} 前端文章过滤生效: ${response.data.length} -> ${filtered.length} (text_id=${textId})`);
    }
    return {
      ...response,
      data: filtered,
      count: filtered.length,
    };
  }
  return response;
};

const normalizeKnowledgeListResponse = (response) => {
  if (!response) {
    return { data: [], count: 0 };
  }
  if (Array.isArray(response)) {
    return { data: response, count: response.length };
  }
  // 兼容 { status: 'success', data: [...] } 未被拦截器归一化的情况
  if (response.status === 'success' && Array.isArray(response.data)) {
    return {
      data: response.data,
      count: response.count ?? response.data.length,
    };
  }
  if (Array.isArray(response.data)) {
    return {
      ...response,
      data: response.data,
      count: response.count ?? response.data.length,
    };
  }
  if (Array.isArray(response.data?.vocabs)) {
    return {
      data: response.data.vocabs,
      count: response.data.count ?? response.data.vocabs.length,
    };
  }
  if (Array.isArray(response.data?.rules)) {
    return {
      data: response.data.rules,
      count: response.data.count ?? response.data.rules.length,
    };
  }
  console.warn('⚠️ [useApi] 无法识别的知识点列表响应格式:', response);
  return { data: [], count: 0 };
};

const enrichKnowledgeListSourceTextIds = (response) => {
  if (!response) {
    return response;
  }
  const enrichItem = (item) => {
    if (!item || typeof item !== 'object') {
      return item;
    }
    if (Array.isArray(item.source_text_ids) && item.source_text_ids.length > 0) {
      return item;
    }
    const ids = new Set();
    for (const ex of item.examples || []) {
      const tid = Number(ex?.text_id ?? ex?.article_id);
      if (!Number.isNaN(tid)) {
        ids.add(tid);
      }
    }
    return {
      ...item,
      source_text_ids: [...ids],
    };
  };
  if (Array.isArray(response)) {
    return response.map(enrichItem);
  }
  if (Array.isArray(response.data)) {
    return {
      ...response,
      data: response.data.map(enrichItem),
    };
  }
  return response;
};

const collectKnowledgeIdsFromNotations = (notationResponse, idField) => {
  const ids = new Set();
  const payload = notationResponse?.data ?? notationResponse;
  const raw = payload?.notations
    ?? payload?.data?.notations
    ?? (Array.isArray(payload) ? payload : null)
    ?? [];
  for (const item of raw) {
    const id = Number(item?.[idField]);
    if (!Number.isNaN(id)) {
      ids.add(id);
    }
  }
  return ids;
};

const filterKnowledgeListByArticle = async ({
  fullResult,
  apiTextId,
  userId,
  label,
  idField,
  fetchNotations,
  fetchServerFiltered,
}) => {
  if (!apiTextId) {
    return fullResult;
  }

  const bySourceTextIds = filterResponseDataByTextId(fullResult, apiTextId, label);
  if (bySourceTextIds.data?.length > 0) {
    console.log(`🔍 [use${label}List] ${bySourceTextIds.data.length} 条 source_text_ids 过滤 text_id=${apiTextId}`);
    return bySourceTextIds;
  }

  try {
    const notationResp = await fetchNotations(apiTextId, userId);
    const linkedIds = collectKnowledgeIdsFromNotations(notationResp, idField);
    if (linkedIds.size > 0) {
      const data = (fullResult.data || []).filter((item) => linkedIds.has(Number(item[idField])));
      console.log(`🔍 [use${label}List] ${data.length} 条 标注 fallback text_id=${apiTextId}`);
      return { ...fullResult, data, count: data.length };
    }
  } catch (err) {
    console.warn(`⚠️ [use${label}List] 标注 fallback 失败:`, err);
  }

  if (typeof fetchServerFiltered === 'function') {
    try {
      const serverResp = await fetchServerFiltered();
      const serverResult = enrichKnowledgeListSourceTextIds(normalizeKnowledgeListResponse(serverResp));
      if (serverResult.data?.length > 0) {
        console.log(`🔍 [use${label}List] ${serverResult.data.length} 条 服务端 text_id=${apiTextId}`);
        return serverResult;
      }
    } catch (err) {
      console.warn(`⚠️ [use${label}List] 服务端 text_id 过滤失败:`, err);
    }
  }

  return { ...fullResult, data: [], count: 0 };
};

const applyMockKnowledgeListFilters = (response, language, learnStatus, label) => {
  let result = filterResponseDataByLanguage(response, language, label);
  if (learnStatus && learnStatus !== 'all' && result?.data) {
    const statusFiltered = result.data.filter(
      (item) => (item.learn_status || 'not_mastered') === learnStatus,
    );
    result = {
      ...result,
      data: statusFiltered,
      count: statusFiltered.length,
    };
  }
  return enrichKnowledgeListSourceTextIds(result);
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
  if (response && Array.isArray(response.texts)) {
    const filtered = filterListByLanguage(response.texts, selectedLanguage, label);
    return {
      ...response,
      texts: filtered,
      count: filtered.length,
    };
  }
  return response;
};

const enrichArticlesResponse = (response) => {
  if (!response) return response;
  if (Array.isArray(response)) {
    return response.map(enrichArticleListItem);
  }
  if (response && Array.isArray(response.data)) {
    return {
      ...response,
      data: response.data.map(enrichArticleListItem),
    };
  }
  if (response && Array.isArray(response.texts)) {
    return {
      ...response,
      texts: response.texts.map(enrichArticleListItem),
    };
  }
  return response;
};

export { matchesSelectedLanguage, filterListByLanguage };

// React Query 配置 - 添加 userId 到 queryKeys
export const queryKeys = {
  health: ['health'],
  word: (text) => ['word', text],
  vocab: {
    all: (userId, language, learnStatus, textId) => ['vocab', userId, language, learnStatus, textId ?? 'all'],
    detail: (id, userId) => ['vocab', id, userId],  // 添加 userId
  },
  grammar: {
    all: (userId, language, learnStatus, textId) => ['grammar', userId, language, learnStatus, textId ?? 'all'],
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
  const apiTextId = textId && textId !== 'all' ? textId : null;

  return useQuery({
    queryKey: queryKeys.vocab.all(userId, language, learnStatus, apiTextId),
    queryFn: async () => {
      if (isGuest) {
        let vocabs = guestDataManager.getVocabs(userId)
        vocabs = filterListByLanguage(vocabs, language, 'vocab')
        if (learnStatus && learnStatus !== 'all') {
          vocabs = vocabs.filter(v => (v.learn_status || 'not_mastered') === learnStatus)
        }
        let result = enrichKnowledgeListSourceTextIds({ data: vocabs, count: vocabs.length })
        if (apiTextId) {
          result = filterResponseDataByTextId(result, apiTextId, 'vocab')
        }
        console.log('👤 [useVocabList] 游客模式:', result.data?.length ?? 0, '条', apiTextId ? `(text_id=${apiTextId})` : '')
        return normalizeKnowledgeListResponse(result)
      }

      const response = await apiService.getVocabList(language, learnStatus, null)
      let result = enrichKnowledgeListSourceTextIds(normalizeKnowledgeListResponse(response))

      if (apiTextId) {
        result = await filterKnowledgeListByArticle({
          fullResult: result,
          apiTextId,
          userId,
          label: 'Vocab',
          idField: 'vocab_id',
          fetchNotations: apiService.getVocabNotations.bind(apiService),
          fetchServerFiltered: () => apiService.getVocabList(language, learnStatus, apiTextId),
        })
      }

      const sample = result.data?.[0]
      console.log(
        '🔍 [useVocabList]',
        result.data?.length ?? 0,
        '条',
        apiTextId ? `文章 text_id=${apiTextId}` : '全部文章',
        sample ? `示例 source_text_ids=${JSON.stringify(sample.source_text_ids ?? [])}` : '',
      )
      return result
    },
    enabled: userId !== null,
    staleTime: 5 * 60 * 1000,
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
  const apiTextId = textId && textId !== 'all' ? textId : null;

  return useQuery({
    queryKey: queryKeys.grammar.all(userId, language, learnStatus, apiTextId),
    queryFn: async () => {
      if (isGuest) {
        let grammars = guestDataManager.getGrammars(userId)
        grammars = filterListByLanguage(grammars, language, 'grammar')
        if (learnStatus && learnStatus !== 'all') {
          grammars = grammars.filter(g => (g.learn_status || 'not_mastered') === learnStatus)
        }
        let result = enrichKnowledgeListSourceTextIds({ data: grammars, count: grammars.length })
        if (apiTextId) {
          result = filterResponseDataByTextId(result, apiTextId, 'grammar')
        }
        return normalizeKnowledgeListResponse(result)
      }

      const response = await apiService.getGrammarList(language, learnStatus, null)
      let result = enrichKnowledgeListSourceTextIds(normalizeKnowledgeListResponse(response))

      if (apiTextId) {
        result = await filterKnowledgeListByArticle({
          fullResult: result,
          apiTextId,
          userId,
          label: 'Grammar',
          idField: 'rule_id',
          fetchNotations: apiService.getGrammarNotations.bind(apiService),
          fetchServerFiltered: () => apiService.getGrammarList(language, learnStatus, apiTextId),
        })
      }
      return result
    },
    enabled: userId !== null,
    staleTime: 5 * 60 * 1000,
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
        articles = articles.filter(a => matchesSelectedLanguage(a.language, language))
      }
      console.log('👤 [useArticles] 游客模式，加载本地数据:', articles.length, '条', language ? `(语言: ${language})` : '')
      return { data: articles.map(enrichArticleListItem) }
    } : async () => {
      const response = await apiService.getArticlesList(language)
      return enrichArticlesResponse(filterResponseDataByLanguage(response, language, 'articles'))
    },
    enabled: userId !== null,  // 游客和登录用户都可以查询（userId 不为 null）
    staleTime: 60 * 1000, // 1分钟（语言切换后更快拿到新数据）
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