import { useState } from 'react';
import { 
  useHealthCheck, 
  useWordInfo, 
  useVocabList, 
  useGrammarList, 
  useStats 
} from '../hooks/useApi.js';

export const ApiDemo = () => {
  const [searchWord, setSearchWord] = useState('');
  const [searchedWord, setSearchedWord] = useState('');

  // 使用 React Query hooks
  const healthCheck = useHealthCheck();
  const wordInfo = useWordInfo(searchedWord);
  const vocabList = useVocabList();
  const grammarList = useGrammarList();
  const stats = useStats();

  const handleSearch = () => {
    if (searchWord.trim()) {
      setSearchedWord(searchWord.trim());
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">API 演示</h1>
      
      {/* 健康检查 */}
      <div className="mb-8 p-4 border rounded-lg">
        <h2 className="text-xl font-semibold mb-2">健康检查</h2>
        {healthCheck.isLoading && <p>检查中...</p>}
        {healthCheck.isError && <p className="text-red-500">错误: {healthCheck.error.message}</p>}
        {healthCheck.isSuccess && (
          <div className="bg-green-100 p-3 rounded">
            <p>状态: {healthCheck.data.data.status}</p>
            <p>时间: {healthCheck.data.data.timestamp}</p>
          </div>
        )}
      </div>

      {/* 单词查询 */}
      <div className="mb-8 p-4 border rounded-lg">
        <h2 className="text-xl font-semibold mb-2">单词查询</h2>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={searchWord}
            onChange={(e) => setSearchWord(e.target.value)}
            placeholder="输入单词..."
            className="flex-1 px-3 py-2 border rounded"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            查询
          </button>
        </div>
        
        {wordInfo.isLoading && <p>查询中...</p>}
        {wordInfo.isError && <p className="text-red-500">错误: {wordInfo.error.message}</p>}
        {wordInfo.isSuccess && (
          <div className="bg-blue-100 p-3 rounded">
            <h3 className="font-semibold">{wordInfo.data.data.word}</h3>
            <p>定义: {wordInfo.data.data.definition || '暂无定义'}</p>
            <p>来源: {wordInfo.data.data.source}</p>
            <p>收藏: {wordInfo.data.data.is_starred ? '是' : '否'}</p>
          </div>
        )}
      </div>

      {/* 词汇列表 */}
      <div className="mb-8 p-4 border rounded-lg">
        <h2 className="text-xl font-semibold mb-2">词汇列表</h2>
        {vocabList.isLoading && <p>加载中...</p>}
        {vocabList.isError && <p className="text-red-500">错误: {vocabList.error.message}</p>}
        {vocabList.isSuccess && (
          <div className="grid gap-2">
            {vocabList.data.data.map((vocab) => (
              <div key={vocab.vocab_id} className="bg-gray-100 p-3 rounded">
                <h3 className="font-semibold">{vocab.vocab_body}</h3>
                <p>定义: {vocab.explanation || '暂无定义'}</p>
                <p>来源: {vocab.source}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 语法规则列表 */}
      <div className="mb-8 p-4 border rounded-lg">
        <h2 className="text-xl font-semibold mb-2">语法规则列表</h2>
        {grammarList.isLoading && <p>加载中...</p>}
        {grammarList.isError && <p className="text-red-500">错误: {grammarList.error.message}</p>}
        {grammarList.isSuccess && (
          <div className="grid gap-2">
            {grammarList.data.data.map((grammar) => (
              <div key={grammar.rule_id} className="bg-gray-100 p-3 rounded">
                <h3 className="font-semibold">{grammar.rule_name}</h3>
                <p>摘要: {grammar.rule_summary}</p>
                <p>来源: {grammar.source}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 统计数据 */}
      <div className="mb-8 p-4 border rounded-lg">
        <h2 className="text-xl font-semibold mb-2">统计数据</h2>
        {stats.isLoading && <p>加载中...</p>}
        {stats.isError && <p className="text-red-500">错误: {stats.error.message}</p>}
        {stats.isSuccess && (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-100 p-3 rounded">
              <h3 className="font-semibold">词汇</h3>
              <p>总数: {stats.data.data.vocab.total}</p>
              <p>收藏: {stats.data.data.vocab.starred}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded">
              <h3 className="font-semibold">语法规则</h3>
              <p>总数: {stats.data.data.grammar.total}</p>
              <p>收藏: {stats.data.data.grammar.starred}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
