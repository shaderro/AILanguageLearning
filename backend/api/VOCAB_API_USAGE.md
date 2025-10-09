# Vocab API 使用指南

## 📋 概述

词汇 API 使用数据库版本的 `VocabManagerDB`，提供完整的词汇管理功能。

**基础 URL**: `http://localhost:8000/api/v2/vocab`

---

## 🚀 启动服务器

```bash
# 在项目根目录运行
python server.py

# 或使用 uvicorn
uvicorn server:app --reload --port 8000
```

**访问 API 文档**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📚 API 端点列表

### 1. 获取所有词汇

**GET** `/api/v2/vocab/`

**参数**:
- `skip` (int, 可选): 跳过的记录数，默认 0
- `limit` (int, 可选): 返回的最大记录数，默认 100
- `starred_only` (bool, 可选): 是否只返回收藏的词汇，默认 false

**示例**:
```bash
# 获取前20个词汇
curl "http://localhost:8000/api/v2/vocab/?skip=0&limit=20"

# 获取收藏的词汇
curl "http://localhost:8000/api/v2/vocab/?starred_only=true"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "vocabs": [
      {
        "vocab_id": 1,
        "vocab_body": "challenging",
        "explanation": "具有挑战性的",
        "source": "auto",
        "is_starred": true
      }
    ],
    "count": 1,
    "skip": 0,
    "limit": 20
  }
}
```

---

### 2. 获取单个词汇

**GET** `/api/v2/vocab/{vocab_id}`

**参数**:
- `vocab_id` (路径参数): 词汇ID
- `include_examples` (bool, 可选): 是否包含例句，默认 true

**示例**:
```bash
# 获取词汇（包含例句）
curl "http://localhost:8000/api/v2/vocab/1"

# 获取词汇（不包含例句）
curl "http://localhost:8000/api/v2/vocab/1?include_examples=false"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "vocab_id": 1,
    "vocab_body": "challenging",
    "explanation": "具有挑战性的",
    "source": "auto",
    "is_starred": true,
    "examples": [
      {
        "vocab_id": 1,
        "text_id": 1,
        "sentence_id": 1,
        "context_explanation": "在这个句子中...",
        "token_indices": [11]
      }
    ]
  }
}
```

---

### 3. 创建新词汇

**POST** `/api/v2/vocab/`

**请求体**:
```json
{
  "vocab_body": "challenging",
  "explanation": "具有挑战性的",
  "source": "manual",
  "is_starred": false
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/v2/vocab/" \
  -H "Content-Type: application/json" \
  -d '{
    "vocab_body": "challenging",
    "explanation": "具有挑战性的",
    "source": "manual",
    "is_starred": false
  }'
```

**响应**:
```json
{
  "success": true,
  "message": "Vocab created successfully",
  "data": {
    "vocab_id": 30,
    "vocab_body": "challenging",
    "explanation": "具有挑战性的",
    "source": "manual",
    "is_starred": false
  }
}
```

---

### 4. 更新词汇

**PUT** `/api/v2/vocab/{vocab_id}`

**请求体** (只传需要更新的字段):
```json
{
  "explanation": "新的解释",
  "is_starred": true
}
```

**示例**:
```bash
curl -X PUT "http://localhost:8000/api/v2/vocab/1" \
  -H "Content-Type: application/json" \
  -d '{
    "explanation": "新的解释",
    "is_starred": true
  }'
```

**响应**:
```json
{
  "success": true,
  "message": "Vocab updated successfully",
  "data": {
    "vocab_id": 1,
    "vocab_body": "challenging",
    "explanation": "新的解释",
    "source": "auto",
    "is_starred": true
  }
}
```

---

### 5. 删除词汇

**DELETE** `/api/v2/vocab/{vocab_id}`

**示例**:
```bash
curl -X DELETE "http://localhost:8000/api/v2/vocab/1"
```

**响应**:
```json
{
  "success": true,
  "message": "Vocab ID 1 deleted successfully"
}
```

---

### 6. 切换收藏状态

**POST** `/api/v2/vocab/{vocab_id}/star`

**示例**:
```bash
curl -X POST "http://localhost:8000/api/v2/vocab/1/star"
```

**响应**:
```json
{
  "success": true,
  "message": "Vocab star status toggled to true",
  "data": {
    "vocab_id": 1,
    "is_starred": true
  }
}
```

---

### 7. 搜索词汇

**GET** `/api/v2/vocab/search/`

**参数**:
- `keyword` (string, 必需): 搜索关键词

**示例**:
```bash
curl "http://localhost:8000/api/v2/vocab/search/?keyword=挑战"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "vocabs": [
      {
        "vocab_id": 1,
        "vocab_body": "challenging",
        "explanation": "具有挑战性的",
        "source": "auto",
        "is_starred": true
      }
    ],
    "count": 1,
    "keyword": "挑战"
  }
}
```

---

### 8. 添加词汇例句

**POST** `/api/v2/vocab/examples`

**请求体**:
```json
{
  "vocab_id": 1,
  "text_id": 1,
  "sentence_id": 5,
  "context_explanation": "在这个句子中...",
  "token_indices": [3, 4]
}
```

**示例**:
```bash
curl -X POST "http://localhost:8000/api/v2/vocab/examples" \
  -H "Content-Type: application/json" \
  -d '{
    "vocab_id": 1,
    "text_id": 1,
    "sentence_id": 5,
    "context_explanation": "在这个句子中...",
    "token_indices": [3, 4]
  }'
```

**响应**:
```json
{
  "success": true,
  "message": "Vocab example created successfully",
  "data": {
    "vocab_id": 1,
    "text_id": 1,
    "sentence_id": 5,
    "context_explanation": "在这个句子中...",
    "token_indices": [3, 4]
  }
}
```

---

### 9. 获取词汇统计

**GET** `/api/v2/vocab/stats/summary`

**示例**:
```bash
curl "http://localhost:8000/api/v2/vocab/stats/summary"
```

**响应**:
```json
{
  "success": true,
  "data": {
    "total": 29,
    "starred": 2,
    "auto": 25,
    "manual": 4
  }
}
```

---

## 🧪 测试示例（Python）

### 使用 requests 库

```python
import requests

BASE_URL = "http://localhost:8000/api/v2/vocab"

# 1. 获取所有词汇
response = requests.get(f"{BASE_URL}/")
print("所有词汇:", response.json())

# 2. 创建新词汇
new_vocab = {
    "vocab_body": "test_word",
    "explanation": "测试词汇",
    "source": "manual",
    "is_starred": False
}
response = requests.post(f"{BASE_URL}/", json=new_vocab)
print("创建结果:", response.json())

# 3. 获取单个词汇
vocab_id = 1
response = requests.get(f"{BASE_URL}/{vocab_id}")
print("词汇详情:", response.json())

# 4. 搜索词汇
response = requests.get(f"{BASE_URL}/search/", params={"keyword": "test"})
print("搜索结果:", response.json())

# 5. 切换收藏状态
response = requests.post(f"{BASE_URL}/{vocab_id}/star")
print("收藏状态:", response.json())

# 6. 获取统计
response = requests.get(f"{BASE_URL}/stats/summary")
print("统计信息:", response.json())
```

---

## 🔧 在前端中使用

### JavaScript/Fetch

```javascript
const BASE_URL = "http://localhost:8000/api/v2/vocab";

// 获取所有词汇
async function getAllVocabs() {
  const response = await fetch(`${BASE_URL}/?limit=20`);
  const data = await response.json();
  return data.data.vocabs;
}

// 创建词汇
async function createVocab(vocabData) {
  const response = await fetch(`${BASE_URL}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(vocabData),
  });
  return response.json();
}

// 搜索词汇
async function searchVocabs(keyword) {
  const response = await fetch(`${BASE_URL}/search/?keyword=${keyword}`);
  const data = await response.json();
  return data.data.vocabs;
}
```

### React 示例

```jsx
import { useState, useEffect } from 'react';

function VocabList() {
  const [vocabs, setVocabs] = useState([]);
  const BASE_URL = "http://localhost:8000/api/v2/vocab";

  useEffect(() => {
    fetchVocabs();
  }, []);

  const fetchVocabs = async () => {
    const response = await fetch(`${BASE_URL}/`);
    const data = await response.json();
    setVocabs(data.data.vocabs);
  };

  return (
    <div>
      <h2>词汇列表</h2>
      {vocabs.map(vocab => (
        <div key={vocab.vocab_id}>
          <h3>{vocab.vocab_body}</h3>
          <p>{vocab.explanation}</p>
        </div>
      ))}
    </div>
  );
}
```

---

## ⚠️ 错误处理

### 常见错误码

| 状态码 | 说明 | 示例 |
|--------|------|------|
| 200 | 成功 | 正常响应 |
| 201 | 创建成功 | POST 创建词汇 |
| 400 | 请求错误 | 词汇已存在、缺少必需字段 |
| 404 | 未找到 | 词汇ID不存在 |
| 500 | 服务器错误 | 数据库错误 |

### 错误响应格式

```json
{
  "detail": "Vocab ID 999 not found"
}
```

---

## 🎯 最佳实践

1. **使用分页**: 获取大量数据时使用 `skip` 和 `limit`
2. **错误处理**: 总是检查 `success` 字段和处理错误
3. **性能优化**: 列表查询时不包含例句（`include_examples=false`）
4. **验证输入**: 创建/更新前验证数据格式
5. **使用搜索**: 优先使用搜索API而非获取所有数据后过滤

---

## 📊 与旧版本对比

| 特性 | 旧版本 (JSON) | 新版本 (DB) |
|-----|--------------|-------------|
| **端点** | `/api/vocab` | `/api/v2/vocab` |
| **存储** | JSON 文件 | SQLite 数据库 |
| **性能** | 慢 | 快 |
| **分页** | 无 | 有 |
| **搜索** | 简单 | SQL LIKE |
| **事务** | 无 | 有 |

---

## 📚 总结

- ✅ 完整的 RESTful API
- ✅ 自动事务管理
- ✅ 数据库持久化
- ✅ 统一错误处理
- ✅ API 文档自动生成
- ✅ CORS 支持

访问 http://localhost:8000/docs 查看交互式 API 文档！

