# 语言学习 API 文档

## 概述

这是一个基于 FastAPI 的语言学习后端 API，提供词汇和语法规则的数据访问服务。API 采用统一的响应格式，支持分页查询和搜索功能。

## 统一响应格式

所有 API 响应都遵循以下统一格式：

### 成功响应
```json
{
  "status": "success",
  "data": {...},
  "error": null,
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "status": "error",
  "data": null,
  "error": "错误描述",
  "message": null
}
```

### 分页响应
```json
{
  "status": "success",
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 100,
    "total_pages": 10
  },
  "error": null,
  "message": "成功获取数据"
}
```

## API 端点

### 1. 根路径
- **GET** `/`
- **描述**: 获取 API 状态信息
- **响应**: API 版本和可用端点信息

### 2. 词汇相关

#### 获取词汇列表
- **GET** `/api/vocab`
- **查询参数**:
  - `page` (int, 可选): 页码，默认为 1
  - `page_size` (int, 可选): 每页数量，默认为 10，最大 100
  - `search` (string, 可选): 搜索关键词
  - `starred_only` (bool, 可选): 是否只显示收藏的词汇，默认为 false

**示例请求**:
```
GET /api/vocab?page=1&page_size=5&search=challenge&starred_only=false
```

#### 获取单个词汇详情
- **GET** `/api/vocab/{vocab_id}`
- **路径参数**:
  - `vocab_id` (int): 词汇 ID

**示例请求**:
```
GET /api/vocab/1
```

### 3. 语法相关

#### 获取语法规则列表
- **GET** `/api/grammar`
- **查询参数**:
  - `page` (int, 可选): 页码，默认为 1
  - `page_size` (int, 可选): 每页数量，默认为 10，最大 100
  - `search` (string, 可选): 搜索关键词
  - `starred_only` (bool, 可选): 是否只显示收藏的语法规则，默认为 false

**示例请求**:
```
GET /api/grammar?page=1&page_size=5&search=perfect&starred_only=true
```

#### 获取单个语法规则详情
- **GET** `/api/grammar/{rule_id}`
- **路径参数**:
  - `rule_id` (int): 语法规则 ID

**示例请求**:
```
GET /api/grammar/1
```

### 4. 统计信息

#### 获取数据统计
- **GET** `/api/stats`
- **描述**: 获取词汇和语法规则的总数和收藏数统计

### 5. 兼容性接口

#### 根据单词查询（兼容旧版本）
- **GET** `/api/word`
- **查询参数**:
  - `text` (string, 必需): 要查询的单词

## 数据模型

### Vocab（词汇）
```json
{
  "vocab_id": 1,
  "vocab_body": "challenging",
  "explanation": "具有挑战性的",
  "examples": [
    {
      "vocab_id": 1,
      "text_id": 1,
      "sentence_id": 1,
      "context_explanation": "在这个句子中...",
      "token_indices": [11]
    }
  ],
  "source": "auto",
  "is_starred": false
}
```

### GrammarRule（语法规则）
```json
{
  "rule_id": 1,
  "rule_name": "Present Perfect Tense",
  "rule_summary": "现在完成时用于表示...",
  "examples": [
    "I have lived in this city for five years.",
    "She has finished her homework."
  ],
  "source": "auto",
  "is_starred": true
}
```

## 错误处理

API 使用统一的错误处理机制：

1. **400 Bad Request**: 请求参数错误
2. **404 Not Found**: 资源不存在
3. **500 Internal Server Error**: 服务器内部错误

所有错误都会返回统一的错误响应格式。

## 运行方式

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动服务器：
```bash
python main.py
```

3. 访问 API 文档：
```
http://localhost:8000/docs
```

## 开发说明

### 项目结构
```
backend/
├── main.py              # 主应用文件
├── models.py            # Pydantic 模型定义
├── services.py          # 数据服务层
├── utils.py             # 工具函数
├── requirements.txt     # 依赖列表
└── API_DOCUMENTATION.md # API 文档
```

### 扩展建议

1. **数据库集成**: 可以轻松替换 `DataService` 为数据库操作
2. **缓存机制**: 添加 Redis 缓存提高性能
3. **认证授权**: 添加 JWT 认证
4. **日志系统**: 集成结构化日志
5. **测试覆盖**: 添加单元测试和集成测试
