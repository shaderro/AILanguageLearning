# Vocab API 快速启动指南

## 🚀 5分钟快速开始

### 步骤1：确保数据库有数据

```bash
# 迁移词汇数据到数据库
python migrate_vocab_only.py
```

**预期输出**：
```
[OK] inserted vocab=29, examples=22
```

---

### 步骤2：启动 FastAPI 服务器

```bash
# 方式1：直接运行
python server.py

# 方式2：使用 uvicorn（推荐）
uvicorn server:app --reload --port 8000
```

**预期输出**：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

### 步骤3：访问 API 文档

打开浏览器访问：
- **Swagger UI（推荐）**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API 根路径**: http://localhost:8000

---

### 步骤4：测试 API

#### 方式1：使用浏览器（Swagger UI）

1. 访问 http://localhost:8000/docs
2. 找到 `GET /api/v2/vocab/` 端点
3. 点击 "Try it out"
4. 点击 "Execute"
5. 查看响应结果

#### 方式2：使用测试脚本

```bash
python test_vocab_api.py
```

#### 方式3：使用 curl

```bash
# 获取所有词汇
curl "http://localhost:8000/api/v2/vocab/"

# 获取单个词汇
curl "http://localhost:8000/api/v2/vocab/1"

# 搜索词汇
curl "http://localhost:8000/api/v2/vocab/search/?keyword=test"

# 获取统计
curl "http://localhost:8000/api/v2/vocab/stats/summary"
```

---

## 📋 常见端点速查

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v2/vocab/` | 获取所有词汇 |
| GET | `/api/v2/vocab/{id}` | 获取单个词汇 |
| POST | `/api/v2/vocab/` | 创建新词汇 |
| PUT | `/api/v2/vocab/{id}` | 更新词汇 |
| DELETE | `/api/v2/vocab/{id}` | 删除词汇 |
| POST | `/api/v2/vocab/{id}/star` | 切换收藏 |
| GET | `/api/v2/vocab/search/` | 搜索词汇 |
| GET | `/api/v2/vocab/stats/summary` | 获取统计 |

---

## 🔍 快速测试示例

### JavaScript（前端）

```javascript
// 获取所有词汇
fetch('http://localhost:8000/api/v2/vocab/')
  .then(res => res.json())
  .then(data => console.log(data.data.vocabs));

// 创建词汇
fetch('http://localhost:8000/api/v2/vocab/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    vocab_body: 'test',
    explanation: '测试',
    source: 'manual'
  })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

### Python

```python
import requests

# 获取所有词汇
response = requests.get('http://localhost:8000/api/v2/vocab/')
vocabs = response.json()['data']['vocabs']
print(f"共有 {len(vocabs)} 个词汇")

# 创建词汇
new_vocab = {
    "vocab_body": "test",
    "explanation": "测试",
    "source": "manual"
}
response = requests.post('http://localhost:8000/api/v2/vocab/', json=new_vocab)
print(response.json())
```

---

## ⚠️ 故障排查

### 问题1：服务器启动失败

**错误**: `ModuleNotFoundError`

**解决**:
```bash
# 安装依赖
pip install fastapi uvicorn sqlalchemy
```

---

### 问题2：数据库为空

**错误**: `GET /api/v2/vocab/` 返回空列表

**解决**:
```bash
# 运行迁移脚本
python migrate_vocab_only.py
```

---

### 问题3：CORS 错误（前端调用）

**错误**: `Access-Control-Allow-Origin`

**解决**: 服务器已配置 CORS，允许所有来源。如果仍有问题：
- 检查前端是否使用正确的 URL
- 确保服务器在运行

---

### 问题4：数据库锁定

**错误**: `database is locked`

**解决**:
```bash
# 停止所有使用数据库的进程
# 重启服务器
```

---

## 🎯 下一步

1. ✅ 阅读完整文档: `VOCAB_API_USAGE.md`
2. ✅ 查看架构说明: `../../ARCHITECTURE_DB_DM_FLOW.md`
3. ✅ 在前端集成 API
4. ✅ 创建更多端点（语法、文章等）

---

## 📞 获取帮助

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health
- **测试脚本**: `python test_vocab_api.py`

---

**祝你使用愉快！** 🎉

