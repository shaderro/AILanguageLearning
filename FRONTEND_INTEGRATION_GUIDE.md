# 前端集成指南 - Vocab API

## 📋 概览

本指南说明如何将新的Vocab API（数据库版本）集成到React前端。

---

## 🔗 API端点

**基础URL:** `http://localhost:8001/api/v2/vocab`

所有端点：
- `GET /` - 获取所有词汇
- `GET /{id}` - 获取单个词汇
- `POST /` - 创建词汇
- `PUT /{id}` - 更新词汇
- `DELETE /{id}` - 删除词汇
- `POST /{id}/star` - 切换收藏
- `GET /search/?keyword=xxx` - 搜索词汇
- `POST /examples` - 添加例句
- `GET /stats/summary` - 获取统计

---

## 📝 数据格式

### VocabDTO

```typescript
interface VocabDTO {
  vocab_id: number;
  vocab_body: string;
  explanation: string;
  source: "auto" | "qa" | "manual";  // 字符串，不是枚举
  is_starred: boolean;
  examples: VocabExampleDTO[];
}

interface VocabExampleDTO {
  vocab_id: number;
  text_id: number;
  sentence_id: number;
  context_explanation: string;
  token_indices: number[];  // 数组，不是字符串
}
```

---

## 🔧 前端实现

### 1. 创建API服务文件

`frontend/src/services/vocabApi.js`

```javascript
const API_BASE_URL = 'http://localhost:8001/api/v2/vocab';

// 获取所有词汇
export const getVocabs = async (skip = 0, limit = 20, starredOnly = false) => {
  const response = await fetch(
    `${API_BASE_URL}/?skip=${skip}&limit=${limit}&starred_only=${starredOnly}`
  );
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || 'Failed to fetch vocabs');
  }
  
  return data.data.vocabs;
};

// 获取单个词汇
export const getVocab = async (vocabId, includeExamples = true) => {
  const response = await fetch(
    `${API_BASE_URL}/${vocabId}?include_examples=${includeExamples}`
  );
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || 'Vocab not found');
  }
  
  return data.data;
};

// 创建词汇
export const createVocab = async (vocabData) => {
  const response = await fetch(`${API_BASE_URL}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      vocab_body: vocabData.vocab_body,
      explanation: vocabData.explanation,
      source: vocabData.source || 'manual',
      is_starred: vocabData.is_starred || false,
    }),
  });
  
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || 'Failed to create vocab');
  }
  
  return data.data;
};

// 更新词汇
export const updateVocab = async (vocabId, updates) => {
  const response = await fetch(`${API_BASE_URL}/${vocabId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });
  
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || 'Failed to update vocab');
  }
  
  return data.data;
};

// 删除词汇
export const deleteVocab = async (vocabId) => {
  const response = await fetch(`${API_BASE_URL}/${vocabId}`, {
    method: 'DELETE',
  });
  
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || 'Failed to delete vocab');
  }
  
  return true;
};

// 切换收藏状态
export const toggleStar = async (vocabId) => {
  const response = await fetch(`${API_BASE_URL}/${vocabId}/star`, {
    method: 'POST',
  });
  
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || 'Failed to toggle star');
  }
  
  return data.data.is_starred;
};

// 搜索词汇
export const searchVocabs = async (keyword) => {
  const response = await fetch(
    `${API_BASE_URL}/search/?keyword=${encodeURIComponent(keyword)}`
  );
  
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || 'Search failed');
  }
  
  return data.data.vocabs;
};

// 添加例句
export const addVocabExample = async (exampleData) => {
  const response = await fetch(`${API_BASE_URL}/examples`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      vocab_id: exampleData.vocab_id,
      text_id: exampleData.text_id,
      sentence_id: exampleData.sentence_id,
      context_explanation: exampleData.context_explanation,
      token_indices: exampleData.token_indices || [],
    }),
  });
  
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || 'Failed to add example');
  }
  
  return data.data;
};

// 获取统计
export const getVocabStats = async () => {
  const response = await fetch(`${API_BASE_URL}/stats/summary`);
  const data = await response.json();
  
  if (!data.success) {
    throw new Error(data.error || 'Failed to get stats');
  }
  
  return data.data;
};
```

---

### 2. 使用React Hooks

`frontend/src/hooks/useVocabs.js`

```javascript
import { useState, useEffect } from 'react';
import * as vocabApi from '../services/vocabApi';

export const useVocabs = (skip = 0, limit = 20, starredOnly = false) => {
  const [vocabs, setVocabs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVocabs = async () => {
      try {
        setLoading(true);
        const data = await vocabApi.getVocabs(skip, limit, starredOnly);
        setVocabs(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchVocabs();
  }, [skip, limit, starredOnly]);

  return { vocabs, loading, error, refetch: () => fetchVocabs() };
};

export const useVocab = (vocabId) => {
  const [vocab, setVocab] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVocab = async () => {
      try {
        setLoading(true);
        const data = await vocabApi.getVocab(vocabId);
        setVocab(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (vocabId) {
      fetchVocab();
    }
  }, [vocabId]);

  return { vocab, loading, error };
};
```

---

### 3. React组件示例

#### VocabList组件

```javascript
import React, { useState } from 'react';
import { useVocabs } from '../hooks/useVocabs';
import { toggleStar, deleteVocab } from '../services/vocabApi';

const VocabList = () => {
  const [starredOnly, setStarredOnly] = useState(false);
  const { vocabs, loading, error, refetch } = useVocabs(0, 20, starredOnly);

  const handleToggleStar = async (vocabId) => {
    try {
      await toggleStar(vocabId);
      refetch();  // 刷新列表
    } catch (err) {
      console.error('Failed to toggle star:', err);
    }
  };

  const handleDelete = async (vocabId) => {
    if (window.confirm('确定要删除这个词汇吗？')) {
      try {
        await deleteVocab(vocabId);
        refetch();  // 刷新列表
      } catch (err) {
        console.error('Failed to delete vocab:', err);
      }
    }
  };

  if (loading) return <div>加载中...</div>;
  if (error) return <div>错误: {error}</div>;

  return (
    <div className="vocab-list">
      <div className="filter">
        <label>
          <input
            type="checkbox"
            checked={starredOnly}
            onChange={(e) => setStarredOnly(e.target.checked)}
          />
          只显示收藏
        </label>
      </div>

      {vocabs.map((vocab) => (
        <div key={vocab.vocab_id} className="vocab-item">
          <h3>{vocab.vocab_body}</h3>
          <p>{vocab.explanation}</p>
          <div className="vocab-meta">
            <span className="source">{vocab.source}</span>
            <button onClick={() => handleToggleStar(vocab.vocab_id)}>
              {vocab.is_starred ? '★' : '☆'}
            </button>
            <button onClick={() => handleDelete(vocab.vocab_id)}>删除</button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default VocabList;
```

#### VocabDetail组件

```javascript
import React from 'react';
import { useVocab } from '../hooks/useVocabs';

const VocabDetail = ({ vocabId }) => {
  const { vocab, loading, error } = useVocab(vocabId);

  if (loading) return <div>加载中...</div>;
  if (error) return <div>错误: {error}</div>;
  if (!vocab) return null;

  return (
    <div className="vocab-detail">
      <h2>{vocab.vocab_body}</h2>
      <p className="explanation">{vocab.explanation}</p>
      
      <div className="meta">
        <span>来源: {vocab.source}</span>
        <span>{vocab.is_starred ? '已收藏' : '未收藏'}</span>
      </div>

      <div className="examples">
        <h3>例句 ({vocab.examples.length})</h3>
        {vocab.examples.map((example, index) => (
          <div key={index} className="example">
            <p>{example.context_explanation}</p>
            <small>
              文章ID: {example.text_id}, 句子ID: {example.sentence_id}
            </small>
            {example.token_indices.length > 0 && (
              <small>Token索引: {example.token_indices.join(', ')}</small>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default VocabDetail;
```

#### CreateVocab组件

```javascript
import React, { useState } from 'react';
import { createVocab } from '../services/vocabApi';

const CreateVocab = ({ onCreated }) => {
  const [formData, setFormData] = useState({
    vocab_body: '',
    explanation: '',
    source: 'manual',
    is_starred: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      
      const newVocab = await createVocab(formData);
      
      // 重置表单
      setFormData({
        vocab_body: '',
        explanation: '',
        source: 'manual',
        is_starred: false,
      });
      
      // 通知父组件
      if (onCreated) {
        onCreated(newVocab);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="create-vocab" onSubmit={handleSubmit}>
      <h3>添加新词汇</h3>
      
      {error && <div className="error">{error}</div>}
      
      <input
        type="text"
        placeholder="词汇"
        value={formData.vocab_body}
        onChange={(e) => setFormData({ ...formData, vocab_body: e.target.value })}
        required
      />
      
      <textarea
        placeholder="解释"
        value={formData.explanation}
        onChange={(e) => setFormData({ ...formData, explanation: e.target.value })}
        required
      />
      
      <select
        value={formData.source}
        onChange={(e) => setFormData({ ...formData, source: e.target.value })}
      >
        <option value="manual">手动添加</option>
        <option value="auto">自动生成</option>
        <option value="qa">问答生成</option>
      </select>
      
      <label>
        <input
          type="checkbox"
          checked={formData.is_starred}
          onChange={(e) => setFormData({ ...formData, is_starred: e.target.checked })}
        />
        收藏
      </label>
      
      <button type="submit" disabled={loading}>
        {loading ? '创建中...' : '创建词汇'}
      </button>
    </form>
  );
};

export default CreateVocab;
```

---

## ⚠️ 注意事项

### 1. 数据格式变化

**旧版本（JSON文件）:**
```javascript
{
  vocab: {
    vocab_id: 1,
    vocab_body: "test",
    explanation: "...",
  },
  example: [...]  // 注意：是 example
}
```

**新版本（数据库）:**
```javascript
{
  vocab_id: 1,
  vocab_body: "test",
  explanation: "...",
  source: "auto",  // 新字段，字符串类型
  is_starred: true,  // 新字段
  examples: [...]  // 注意：是 examples (复数)
}
```

### 2. source字段类型

```javascript
// 旧版本可能是数字或枚举
source: 0  // ❌

// 新版本是字符串
source: "auto"  // ✅
source: "qa"    // ✅
source: "manual"  // ✅
```

### 3. token_indices字段

```javascript
// 确保是数组
token_indices: [1, 2, 3]  // ✅
// 不是字符串
token_indices: "1,2,3"  // ❌
```

---

## 🔄 迁移步骤

### 1. 更新API调用

```javascript
// 旧代码
const vocabs = await fetch('/api/vocab').then(r => r.json());

// 新代码
import { getVocabs } from './services/vocabApi';
const vocabs = await getVocabs();
```

### 2. 更新数据访问

```javascript
// 旧代码
const explanation = vocab.vocab.explanation;
const examples = vocab.example;

// 新代码
const explanation = vocab.explanation;
const examples = vocab.examples;  // 注意复数
```

### 3. 处理新字段

```javascript
// 添加source和is_starred的显示
<div className="vocab-meta">
  <span className="source">{vocab.source}</span>
  {vocab.is_starred && <span>★</span>}
</div>
```

---

## 🧪 测试

### 1. 启动后端服务器

```bash
python server.py
```

### 2. 配置前端代理（vite.config.js）

```javascript
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
};
```

### 3. 启动前端开发服务器

```bash
cd frontend/my-web-ui
npm run dev
```

---

## ✅ 验证清单

- [ ] API服务文件创建完成
- [ ] Hooks封装完成
- [ ] 组件更新完成
- [ ] 数据格式适配完成
- [ ] source字段处理正确
- [ ] examples字段处理正确（注意复数）
- [ ] token_indices作为数组处理
- [ ] 错误处理完善
- [ ] 加载状态显示
- [ ] 前端可以正常CRUD词汇
- [ ] 收藏功能正常
- [ ] 搜索功能正常

---

## 📚 相关文档

- `SWAGGER_TEST_GUIDE.md` - 使用Swagger测试API
- `FASTAPI_MANAGER_INTEGRATION.md` - 后端实现细节
- `VOCAB_DATABASE_COMPLETE.md` - 完整总结

---

## 🆘 常见问题

### Q1: CORS错误

**问题:** `Access to fetch has been blocked by CORS policy`

**解决:** 后端已配置CORS，确保服务器正常运行：
```bash
python server.py
```

### Q2: source字段类型错误

**问题:** 期望枚举，收到字符串

**解决:** 新版本返回字符串，直接使用即可：
```javascript
if (vocab.source === "auto") {  // ✅
  // ...
}
```

### Q3: examples字段不存在

**问题:** `vocab.example is undefined`

**解决:** 新版本是 `examples` (复数)：
```javascript
vocab.examples.map(...)  // ✅
```

---

## 🎉 完成

完成以上步骤后，前端应该能够：
- ✅ 获取词汇列表
- ✅ 查看词汇详情
- ✅ 创建新词汇
- ✅ 更新词汇
- ✅ 删除词汇
- ✅ 切换收藏状态
- ✅ 搜索词汇
- ✅ 添加例句

所有数据都来自数据库，无需JSON文件！

