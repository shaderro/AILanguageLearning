# AI语言学习应用 - 系统架构文档

**文档版本**: 1.0  
**更新日期**: 2025年1月

## 📋 目录

1. [系统概览](#系统概览)
2. [前端架构](#前端架构)
3. [后端架构](#后端架构)
4. [数据库架构](#数据库架构)
5. [部署方案](#部署方案)
6. [迁移方案](#迁移方案)

---

## 系统概览

### 技术栈总览

```
┌─────────────────────────────────────────────────────────┐
│                    AI语言学习应用                          │
├─────────────────────────────────────────────────────────┤
│  前端: React 19 + Vite + TailwindCSS                    │
│  后端: FastAPI + Uvicorn + SQLAlchemy                   │
│  数据库: SQLite (开发) / PostgreSQL (生产)              │
│  AI服务: OpenAI API (DeepSeek)                          │
└─────────────────────────────────────────────────────────┘
```

### 架构模式

- **前后端分离**: 前端独立部署，通过 REST API 与后端通信
- **模块化设计**: 前后端均采用模块化架构，便于维护和扩展
- **数据库抽象层**: 支持 SQLite 和 PostgreSQL，通过环境变量切换

---

## 前端架构

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19.1.1 | UI框架 |
| Vite | 7.1.7 | 构建工具和开发服务器 |
| TailwindCSS | 3.4.17 | CSS框架 |
| React Query | 5.85.5 | 数据获取和状态管理 |
| Axios | 1.11.0 | HTTP客户端 |
| React Speech Kit | 3.0.1 | 语音合成 |

### 项目结构

```
frontend/my-web-ui/
├── src/
│   ├── App.jsx                    # 主应用组件
│   ├── main.jsx                   # 入口文件
│   ├── components/                # 基础组件
│   │   ├── base/                  # 基础UI组件
│   │   └── features/              # 功能组件
│   ├── modules/                   # 功能模块
│   │   ├── article/               # 文章阅读模块
│   │   ├── grammar-demo/          # 语法学习模块
│   │   ├── word-demo/             # 词汇学习模块
│   │   ├── auth/                   # 认证模块
│   │   └── shared/                # 共享组件
│   ├── contexts/                  # React Context
│   │   ├── UserContext.jsx        # 用户上下文
│   │   ├── LanguageContext.jsx    # 语言上下文
│   │   └── UiLanguageContext.jsx  # UI语言上下文
│   ├── hooks/                     # 自定义Hooks
│   ├── services/                  # 服务层
│   │   ├── api.js                 # API客户端
│   │   └── translationService.js  # 翻译服务
│   ├── i18n/                      # 国际化
│   └── utils/                     # 工具函数
├── public/                        # 静态资源
├── dist/                          # 构建输出
├── package.json                   # 依赖配置
├── vite.config.js                 # Vite配置
└── tailwind.config.js             # Tailwind配置
```

### 核心模块说明

#### 1. 文章阅读模块 (`modules/article/`)

- **ArticleViewer**: 文章阅读器，支持句子选择、标注显示
- **ArticleChatView**: 文章对话界面，集成AI助手
- **Notation系统**: 语法和词汇标注显示
  - `GrammarNotationCard`: 语法标注卡片
  - `VocabNotationCard`: 词汇标注卡片
  - `UnifiedNotationManager`: 统一标注管理

#### 2. 认证模块 (`modules/auth/`)

- JWT token 管理
- 用户登录/注册
- 权限控制

#### 3. 数据管理

- **React Query**: 用于数据获取、缓存和同步
- **API Service**: 统一的API调用接口
- **Context API**: 全局状态管理（用户、语言等）

### 开发服务器配置

```javascript
// vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    strictPort: true
  }
})
```

### 构建和部署

#### 开发环境

```bash
cd frontend/my-web-ui
npm install
npm run dev  # 启动开发服务器 (http://localhost:5173)
```

#### 生产构建

```bash
npm run build  # 构建到 dist/ 目录
npm run preview  # 预览生产构建
```

#### 部署选项

1. **静态文件托管**
   - 构建产物: `dist/` 目录
   - 可部署到: Vercel, Netlify, GitHub Pages, Nginx, Apache
   - 需要配置反向代理到后端API

2. **Docker部署**
   ```dockerfile
   FROM node:18-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   RUN npm run build
   FROM nginx:alpine
   COPY --from=0 /app/dist /usr/share/nginx/html
   ```

3. **CDN部署**
   - 将 `dist/` 内容上传到CDN
   - 配置API代理

---

## 后端架构

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.104.0+ | Web框架 |
| Uvicorn | 0.24.0+ | ASGI服务器 |
| SQLAlchemy | 2.0.0+ | ORM框架 |
| Pydantic | 2.11.5 | 数据验证 |
| Python-dotenv | 1.0.0+ | 环境变量管理 |
| OpenAI | 1.84.0 | AI API客户端 |
| JWT | 3.3.0 | 认证 |

### 项目结构

```
backend/
├── api/                           # API路由
│   ├── auth_routes.py            # 认证路由
│   ├── text_routes.py            # 文章路由
│   ├── grammar_routes.py         # 语法路由
│   ├── vocab_routes.py           # 词汇路由
│   ├── notation_routes.py        # 标注路由
│   ├── chat_history_routes.py    # 聊天历史路由
│   └── user_routes.py            # 用户路由
├── assistants/                   # AI助手系统
│   ├── main_assistant.py         # 主助手
│   ├── sub_assistants/           # 子助手
│   │   ├── summarize_grammar_rule.py
│   │   ├── grammar_explanation.py
│   │   ├── vocab_explanation.py
│   │   └── ...
│   └── chat_info/                # 会话管理
│       ├── session_state.py
│       └── dialogue_history.py
├── data_managers/                # 数据管理
│   ├── data_controller.py        # 数据控制器
│   ├── grammar_rule_manager_db.py
│   ├── vocab_manager_db.py
│   ├── original_text_manager_db.py
│   └── ...
├── preprocessing/                # 数据预处理
│   ├── article_processor.py
│   ├── sentence_processor.py
│   ├── token_processor.py
│   └── ...
├── adapters/                     # 数据适配器
├── middleware/                    # 中间件
│   └── rate_limit.py
├── services/                     # 服务层
│   └── token_service.py
├── utils/                        # 工具函数
│   └── auth.py
└── config.py                     # 配置管理

frontend/my-web-ui/backend/
└── main.py                       # FastAPI应用入口
```

### 核心模块说明

#### 1. API路由层 (`api/`)

- **RESTful API设计**: 遵循REST规范
- **版本控制**: 支持 `/api/v2/` 版本路由
- **认证中间件**: JWT token验证
- **CORS配置**: 支持跨域请求

#### 2. AI助手系统 (`assistants/`)

- **主助手** (`main_assistant.py`): 协调所有子助手，处理用户对话
- **子助手** (`sub_assistants/`):
  - 语法规则总结和解释
  - 词汇解释
  - 相关性检查
  - 对话历史总结
- **会话管理**: 维护对话上下文和状态

#### 3. 数据管理层 (`data_managers/`)

- **数据控制器**: 统一的数据操作接口
- **管理器类**: 各实体的CRUD操作
  - `GrammarRuleManagerDB`: 语法规则管理
  - `VocabManagerDB`: 词汇管理
  - `OriginalTextManagerDB`: 文章管理
- **适配器模式**: 数据模型转换

#### 4. 数据预处理 (`preprocessing/`)

- **文章处理**: HTML/PDF提取，文本清理
- **句子处理**: 句子分割，难度评估
- **词汇处理**: Token分割，词性标注

### 配置管理

```python
# backend/config.py
# 环境变量配置
ENV = os.getenv("ENV", "development")  # development/testing/production
JWT_SECRET = os.getenv("JWT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")  # 可选，覆盖默认配置
```

### 启动方式

#### 开发环境

```bash
# 方式1: 直接运行
cd frontend/my-web-ui/backend
python main.py

# 方式2: 使用Uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 生产环境

```bash
# 使用Gunicorn + Uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 数据库架构

### 数据库系统

#### 本地开发 (SQLite)

```python
# database_system/data_storage/config/config.py
DATABASE_CONFIG = {
    'development': 'sqlite:///database_system/data_storage/data/dev.db',
    'testing': 'sqlite:///database_system/data_storage/data/test.db',
    'production': 'sqlite:///database_system/data_storage/data/language_learning.db'
}
```

#### 生产环境 (PostgreSQL)

```python
# 通过环境变量 DATABASE_URL 配置
# 格式: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv("DATABASE_URL")
```

### 数据库管理器

```python
# database_system/database_manager.py
class DatabaseManager:
    def __init__(self, environment: str = 'development'):
        # 自动检测数据库类型（SQLite/PostgreSQL）
        # 配置连接池和超时设置
        pass
```

### 数据模型

#### 核心表结构

1. **users**: 用户表
2. **original_texts**: 原始文章表
3. **sentences**: 句子表
4. **grammar_rules**: 语法规则表
5. **grammar_examples**: 语法示例表
6. **vocab_expressions**: 词汇表达表
7. **vocab_examples**: 词汇示例表
8. **grammar_notations**: 语法标注表
9. **vocab_notations**: 词汇标注表
10. **chat_messages**: 聊天消息表
11. **asked_tokens**: 已提问token表

#### ORM模型

```python
# database_system/business_logic/models.py
# 使用SQLAlchemy ORM定义所有数据模型
```

### 数据访问层

```
database_system/business_logic/
├── models.py              # ORM模型定义
├── crud/                  # CRUD操作
│   ├── user_crud.py
│   ├── text_crud.py
│   ├── grammar_crud.py
│   └── ...
├── managers/              # 业务逻辑管理器
│   ├── user_manager.py
│   ├── text_manager.py
│   └── ...
└── data_access_layer.py   # 数据访问抽象层
```

---

## 部署方案

### 当前部署架构

```
┌─────────────────────────────────────────────────────────┐
│                      用户浏览器                           │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   前端 (静态文件)                         │
│  - Vite构建产物 (dist/)                                  │
│  - 部署在: Vercel/Netlify/Nginx                          │
└───────────────────────┬─────────────────────────────────┘
                        │ API请求
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   后端 (FastAPI)                         │
│  - Uvicorn/Gunicorn服务器                               │
│  - 端口: 8000                                           │
│  - 部署在: Render/Railway/Heroku/VPS                     │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   数据库                                  │
│  - 开发: SQLite (本地文件)                               │
│  - 生产: PostgreSQL (云数据库)                          │
│  - 部署在: Render/Railway/Supabase/自建PostgreSQL       │
└─────────────────────────────────────────────────────────┘
```

### 前端部署

#### 选项1: Vercel/Netlify (推荐)

```bash
# 1. 构建项目
cd frontend/my-web-ui
npm run build

# 2. 部署到Vercel
vercel deploy

# 3. 配置环境变量
# - VITE_API_URL: 后端API地址
```

**优点**:
- 自动HTTPS
- CDN加速
- 自动部署
- 免费额度充足

#### 选项2: Nginx静态托管

```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    
    root /var/www/frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 选项3: Docker部署

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 后端部署

#### 选项1: Render (推荐)

```yaml
# render.yaml
services:
  - type: web
    name: ai-language-learning-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENV
        value: production
      - key: DATABASE_URL
        sync: false
      - key: JWT_SECRET
        sync: false
      - key: OPENAI_API_KEY
        sync: false
```

#### 选项2: Railway

```bash
# 1. 连接GitHub仓库
# 2. 配置环境变量
# 3. 设置启动命令
uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 选项3: Docker部署

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### 选项4: VPS部署

```bash
# 1. 安装依赖
sudo apt update
sudo apt install python3-pip nginx postgresql

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 使用systemd管理服务
# /etc/systemd/system/ai-language-learning.service
[Unit]
Description=AI Language Learning API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 数据库部署

#### PostgreSQL云服务

1. **Render PostgreSQL**
   - 自动提供 `DATABASE_URL`
   - 免费额度: 90天试用

2. **Railway PostgreSQL**
   - 按使用量计费
   - 自动备份

3. **Supabase**
   - 免费额度充足
   - 提供PostgreSQL + 额外功能

4. **自建PostgreSQL**
   ```bash
   # Docker部署
   docker run -d \
     --name postgres \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=language_learning \
     -p 5432:5432 \
     postgres:15
   ```

---

## 迁移方案

### 前端迁移

#### 从当前架构迁移到新框架

**场景1: 迁移到Next.js**

```bash
# 1. 创建Next.js项目
npx create-next-app@latest new-frontend --typescript --tailwind --app

# 2. 迁移组件
# - 将 React 组件迁移到 Next.js App Router
# - 使用 Next.js 的 Server Components 优化性能
# - 迁移 API 调用到 Server Actions 或 Route Handlers

# 3. 配置
# - next.config.js: 配置API代理
# - 迁移路由到 App Router 结构

# 4. 优势
# - SSR/SSG支持
# - 更好的SEO
# - 内置API路由
```

**场景2: 迁移到Vue 3**

```bash
# 1. 创建Vue项目
npm create vue@latest new-frontend

# 2. 迁移策略
# - 组件: React JSX → Vue SFC
# - 状态管理: React Query → Pinia + Vue Query
# - 路由: React Router → Vue Router
# - 样式: TailwindCSS保持不变

# 3. 逐步迁移
# - 先迁移独立组件
# - 再迁移页面
# - 最后迁移状态管理
```

**场景3: 迁移到Svelte**

```bash
# 1. 创建Svelte项目
npm create svelte@latest new-frontend

# 2. 迁移策略
# - 组件: React → Svelte组件
# - 状态: React Context → Svelte Stores
# - 路由: React Router → SvelteKit路由
```

#### 前端迁移检查清单

- [ ] 评估目标框架的生态系统和社区支持
- [ ] 创建新项目结构
- [ ] 迁移UI组件（保持样式一致）
- [ ] 迁移状态管理逻辑
- [ ] 迁移API调用层
- [ ] 迁移路由配置
- [ ] 测试所有功能
- [ ] 性能优化
- [ ] 部署新版本

### 后端迁移

#### 场景1: 迁移到Django

```python
# 优势
# - 完整的ORM系统
# - 内置管理后台
# - 更成熟的生态系统

# 迁移步骤
# 1. 创建Django项目
django-admin startproject language_learning

# 2. 迁移数据模型
# - SQLAlchemy models → Django models
# - 保持数据库结构不变

# 3. 迁移API
# - FastAPI routes → Django REST Framework views
# - 保持API接口兼容

# 4. 迁移业务逻辑
# - 保持核心逻辑不变
# - 适配Django的ORM和中间件
```

#### 场景2: 迁移到Flask

```python
# 优势
# - 更轻量级
# - 更灵活
# - 学习曲线平缓

# 迁移步骤
# 1. 创建Flask项目
# 2. 迁移路由: FastAPI → Flask Blueprints
# 3. 迁移数据模型: SQLAlchemy保持不变
# 4. 迁移中间件
```

#### 场景3: 迁移到Node.js (Express/NestJS)

```typescript
// 优势
// - 前后端统一语言
// - 更好的类型安全（TypeScript）
// - 丰富的生态系统

// 迁移步骤
// 1. 选择框架: Express 或 NestJS
// 2. 迁移数据模型: SQLAlchemy → TypeORM/Prisma
// 3. 迁移API路由
// 4. 迁移业务逻辑（需要重写Python代码）
```

#### 后端迁移检查清单

- [ ] 评估目标框架的优缺点
- [ ] 分析现有代码结构
- [ ] 设计新的项目结构
- [ ] 迁移数据模型
- [ ] 迁移API路由
- [ ] 迁移业务逻辑
- [ ] 迁移认证系统
- [ ] 迁移AI助手系统
- [ ] 数据库迁移脚本
- [ ] 测试所有功能
- [ ] 性能测试
- [ ] 部署新版本

### 数据库迁移

#### SQLite → PostgreSQL

```python
# 1. 导出SQLite数据
# 使用sqlite3命令行工具
sqlite3 dev.db .dump > backup.sql

# 2. 转换SQL语法
# - 手动调整SQL语法差异
# - 或使用迁移工具

# 3. 导入PostgreSQL
psql -U user -d database -f backup.sql

# 4. 使用SQLAlchemy自动迁移
# database_system/database_manager.py 已支持自动切换
# 只需设置 DATABASE_URL 环境变量
```

#### 数据库迁移工具

1. **Alembic** (SQLAlchemy官方工具)
   ```bash
   # 初始化
   alembic init alembic
   
   # 生成迁移
   alembic revision --autogenerate -m "Initial migration"
   
   # 执行迁移
   alembic upgrade head
   ```

2. **Django Migrations** (如果迁移到Django)
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### 完整迁移流程示例

#### 迁移到Next.js + Django + PostgreSQL

**阶段1: 准备阶段**
1. 备份所有数据
2. 设置新的开发环境
3. 创建新的项目结构

**阶段2: 后端迁移**
1. 创建Django项目
2. 迁移数据模型
3. 迁移API路由
4. 迁移业务逻辑
5. 测试API功能

**阶段3: 数据库迁移**
1. 导出SQLite数据
2. 导入PostgreSQL
3. 验证数据完整性

**阶段4: 前端迁移**
1. 创建Next.js项目
2. 迁移UI组件
3. 迁移状态管理
4. 更新API调用
5. 测试前端功能

**阶段5: 部署**
1. 部署新后端
2. 部署新前端
3. 配置域名和SSL
4. 监控和测试

**阶段6: 切换**
1. 维护窗口
2. 数据同步
3. 切换DNS
4. 监控运行状态

---

## 总结

### 当前架构优势

1. **前后端分离**: 独立开发和部署
2. **模块化设计**: 易于维护和扩展
3. **数据库抽象**: 支持多种数据库
4. **现代化技术栈**: React 19, FastAPI, SQLAlchemy 2.0

### 迁移建议

1. **渐进式迁移**: 不要一次性迁移所有内容
2. **保持API兼容**: 确保迁移过程中API接口不变
3. **充分测试**: 每个阶段都要进行完整测试
4. **数据备份**: 迁移前必须备份所有数据
5. **回滚计划**: 准备回滚方案以防万一

### 推荐迁移路径

- **短期**: 优化当前架构，提升性能和稳定性
- **中期**: 考虑迁移到Next.js（如果需要SSR/SSG）
- **长期**: 根据业务需求和技术趋势决定是否迁移后端框架

---

**文档维护**: 本文档应随架构变更及时更新  
**联系方式**: 如有问题，请提交Issue或联系开发团队

