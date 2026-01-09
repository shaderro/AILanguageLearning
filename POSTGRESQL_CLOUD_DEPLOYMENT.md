# 云平台 PostgreSQL 部署指南（Vercel & PaaS）

## 📋 概述

本文档专门针对在 **Vercel** 和 **PaaS 平台**（如 Render、Railway、Fly.io 等）上部署 PostgreSQL 的配置方式。与本地部署相比，云平台提供了托管的 PostgreSQL 服务，配置更加简单。

---

## 🎯 重要区别说明

### 本地开发 vs 云平台部署

| 方面 | 本地开发 | 云平台（Vercel/PaaS） |
|------|---------|---------------------|
| **数据库安装** | 需要手动安装 PostgreSQL | 平台自动提供托管服务 |
| **数据库创建** | 手动创建数据库 | 自动创建或一键添加 |
| **连接字符串** | 手动配置 | 通过环境变量自动注入 |
| **凭证管理** | 手动管理用户名密码 | 平台自动生成并管理 |
| **网络访问** | localhost | 通过 URL 和 SSL 连接 |

---

## 🚀 方案一：使用 Vercel 部署

### ⚠️ 重要提示

**Vercel 主要用于前端部署**，虽然支持 Serverless Functions，但对于 FastAPI 这种需要持久连接和长时间运行的应用，**不推荐使用 Vercel**。

**推荐架构：**
- **前端** → 部署到 Vercel
- **后端 API (FastAPI)** → 部署到专门的 PaaS 平台（Render、Railway 等）
- **数据库** → 使用托管 PostgreSQL（如 Vercel Postgres、Neon、Supabase）

### 1.1 Vercel Postgres（如果后端也在 Vercel）

如果您坚持在 Vercel 上部署后端：

#### 步骤 1: 创建 Vercel Postgres 数据库

1. 在 Vercel 项目中，进入 **Storage** 标签
2. 点击 **Create Database** → 选择 **Postgres**
3. 选择区域（推荐：离用户最近的区域）
4. 创建数据库（会自动生成连接字符串）

#### 步骤 2: 配置环境变量

Vercel 会自动创建以下环境变量：
- `POSTGRES_URL` - 主连接字符串
- `POSTGRES_PRISMA_URL` - Prisma 格式连接字符串
- `POSTGRES_URL_NON_POOLING` - 非池化连接（用于迁移）

#### 步骤 3: 在代码中使用

```python
import os
from sqlalchemy import create_engine

# Vercel Postgres 会自动注入环境变量
database_url = os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL')

if not database_url:
    raise ValueError("DATABASE_URL 环境变量未设置")

# SQLAlchemy 连接
engine = create_engine(database_url, echo=False)
```

---

## 🌐 方案二：PaaS 平台部署（推荐）

以下平台更适合部署 FastAPI 应用：

- **Render** - 简单易用，免费层可用
- **Railway** - 开发友好，自动部署
- **Fly.io** - 全球分布式，性能好
- **DigitalOcean App Platform** - 企业级
- **Heroku** - 老牌 PaaS（已取消免费层）

### 2.1 Render 平台

#### 步骤 1: 创建 PostgreSQL 数据库

1. 登录 Render: https://render.com
2. 点击 **New +** → **PostgreSQL**
3. 配置：
   - **Name**: `language-learning-db`
   - **Database**: `language_learning_prod`（可选，会自动创建）
   - **User**: 自动生成
   - **Region**: 选择离用户最近的区域
   - **PostgreSQL Version**: 16（推荐）
   - **Plan**: Free（开发）或 Starter（生产）
4. 点击 **Create Database**

#### 步骤 2: 获取连接字符串

创建后，Render 会显示：
- **Internal Database URL** - 仅 Render 服务内部使用
- **External Database URL** - 外部连接使用

连接字符串格式：
```
postgresql://user:password@hostname:5432/database_name
```

#### 步骤 3: 创建 Web Service（部署应用）

1. 在 Render 仪表板，点击 **New +** → **Web Service**
2. 连接您的 Git 仓库（GitHub/GitLab/Bitbucket）
3. 选择仓库和分支
4. 配置应用设置：
   - **Name**: `language-learning-api`（自定义名称）
   - **Region**: 选择与数据库相同的区域
   - **Branch**: `main` 或 `master`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Root Directory**: **留空**（或填写 `.`）
     - ⚠️ **重要**: 必须使用仓库根目录，因为：
       - `requirements.txt` 在根目录
       - `database_system/` 在根目录
       - `backend/` 在根目录
       - `main.py` 代码会自动切换到根目录运行
   - **Start Command**: `uvicorn frontend.my-web-ui.backend.main:app --host 0.0.0.0 --port $PORT`
     - ⚠️ **注意**: 使用完整模块路径 `frontend.my-web-ui.backend.main:app`
   - **Instance Type**: Free（开发）或 Starter（生产）

#### 步骤 4: 配置环境变量（重要！）

在创建 Web Service 时或创建后，有两种方式添加环境变量：

##### 方式 A: 在创建服务时添加（推荐）

在创建 Web Service 页面，向下滚动找到 **Environment Variables** 部分，点击 **Add Environment Variable**，添加：

```
Key: DATABASE_URL
Value: 从步骤 2 复制的 Internal Database URL（或 External Database URL）
```

然后继续添加其他环境变量：

```
DATABASE_URL=postgresql://user:password@dpg-xxxxx-a/language_learning_prod
ENV=production
JWT_SECRET=your_jwt_secret_here
OPENAI_API_KEY=sk-your-openai-api-key
```

##### 方式 B: 在服务创建后添加

如果服务已经创建，按以下步骤：

1. **进入服务页面**：
   - 在 Render 仪表板，点击您创建的 Web Service 名称
   - 或从左侧菜单选择您的服务

2. **找到 Environment 标签**：
   - 在服务详情页面的顶部，有几个标签页：
     - **Logs**（日志）
     - **Events**（事件）
     - **Metrics**（指标）
     - **Settings**（设置）⭐ **点击这里**
   
3. **进入 Environment 设置**：
   - 在 **Settings** 标签页中
   - 向下滚动找到 **Environment Variables** 部分
   - 您会看到已有的环境变量列表（如果有）

4. **添加环境变量**：
   - 点击 **Add Environment Variable** 按钮
   - 在弹出框中输入：
     - **Key**: `DATABASE_URL`
     - **Value**: 粘贴从 PostgreSQL 数据库复制的连接字符串
   - 点击 **Save Changes**

5. **继续添加其他变量**：
   - 重复步骤 4，添加以下变量：
     ```
     ENV=production
     JWT_SECRET=your_secure_jwt_secret
     OPENAI_API_KEY=sk-your-openai-api-key
     ```

6. **自动重启**：
   - 添加环境变量后，Render 会自动重新部署服务
   - 可以在 **Logs** 标签页查看部署进度

#### 步骤 5: 链接数据库到应用（推荐方式）

**更简单的方法** - Render 提供了自动链接功能：

1. 在 PostgreSQL 数据库页面，找到 **Connections** 部分
2. 点击 **Link** 按钮
3. 选择您创建的 Web Service
4. Render 会自动将数据库连接信息注入为环境变量 `DATABASE_URL`

这样您就不需要手动复制粘贴连接字符串了！

#### 步骤 6: 部署和验证

1. 点击 **Create Web Service**（如果还在创建页面）
2. 等待首次部署完成（通常需要 2-5 分钟）
3. 部署成功后，在 **Logs** 标签页查看应用启动日志
4. 访问您的应用 URL（格式：`https://your-service-name.onrender.com`）
5. 测试 API：访问 `https://your-service-name.onrender.com/docs` 查看 API 文档

---

### 2.2 Railway 平台

#### 步骤 1: 创建 PostgreSQL 数据库

1. 登录 Railway: https://railway.app
2. 创建新项目
3. 点击 **New** → **Database** → **Add PostgreSQL**
4. 数据库会自动创建并配置

#### 步骤 2: 自动环境变量

Railway 会自动创建以下环境变量：
- `DATABASE_URL` - PostgreSQL 连接字符串
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` - 单独的环境变量

#### 步骤 3: 部署应用

1. 在同一个项目中，点击 **New** → **GitHub Repo**
2. 选择您的仓库
3. Railway 会自动检测 Python 项目
4. 配置：
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. 确保环境变量中包含了 `DATABASE_URL`

---

### 2.3 Fly.io 平台

#### 步骤 1: 创建 PostgreSQL 数据库

```bash
# 安装 flyctl
# Windows: https://fly.io/docs/getting-started/installing-flyctl/

# 登录
flyctl auth login

# 创建应用
flyctl apps create language-learning-api

# 创建 PostgreSQL 数据库
flyctl postgres create --name language-learning-db --region hkg  # 香港区域
```

#### 步骤 2: 连接数据库到应用

```bash
# 将数据库连接到应用
flyctl postgres attach --app language-learning-api language-learning-db
```

这会自动创建 `DATABASE_URL` 环境变量。

#### 步骤 3: 部署应用

```bash
# 在项目根目录
flyctl deploy
```

---

## 🔧 通用配置：适配云平台 PostgreSQL

### 3.1 更新数据库配置代码

需要修改 `database_system/data_storage/config/config.py`：

```python
import os
from urllib.parse import urlparse

# 优先使用环境变量中的 DATABASE_URL（云平台会自动注入）
DATABASE_URL_ENV = os.getenv('DATABASE_URL')

# 云平台连接字符串格式示例：
# postgresql://user:password@hostname:5432/database_name
# 或
# postgresql+psycopg2://user:password@hostname:5432/database_name

if DATABASE_URL_ENV:
    # 云平台环境：使用环境变量
    # 确保连接字符串使用 postgresql:// 协议（不是 postgresql+psycopg2://）
    if DATABASE_URL_ENV.startswith('postgresql://'):
        # 可能需要转换为 postgresql+psycopg2://（取决于 SQLAlchemy 版本）
        pass
    elif DATABASE_URL_ENV.startswith('postgresql+psycopg2://'):
        pass
    else:
        # 如果不是 postgresql:// 开头，可能需要转换
        DATABASE_URL_ENV = DATABASE_URL_ENV.replace('postgres://', 'postgresql://')
    
    DATABASE_CONFIG = {
        'development': DATABASE_URL_ENV,
        'testing': DATABASE_URL_ENV,
        'production': DATABASE_URL_ENV
    }
else:
    # 本地开发环境：使用 SQLite（向后兼容）
    DATABASE_CONFIG = {
        'development': 'sqlite:///database_system/data_storage/data/dev.db',
        'testing': 'sqlite:///database_system/data_storage/data/test.db',
        'production': 'sqlite:///database_system/data_storage/data/language_learning.db'
    }

# 数据库文件路径（仅用于 SQLite，云平台不需要）
DB_FILES = {
    'dev': 'database_system/data_storage/data/dev.db',
    'test': 'database_system/data_storage/data/test.db',
    'prod': 'database_system/data_storage/data/language_learning.db'
}
```

### 3.2 更新 DatabaseManager

修改 `database_system/database_manager.py`：

```python
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .data_storage.config.config import DATABASE_CONFIG, DB_FILES
import os

class DatabaseManager:
    def __init__(self, environment: str = 'development'):
        if environment not in DATABASE_CONFIG:
            raise ValueError(f"Unknown environment: {environment}")
        self.environment = environment
        self.database_url = DATABASE_CONFIG[environment]
        self._engine = None
        self._Session = None

    def get_engine(self):
        if self._engine is None:
            # 检查是否是 PostgreSQL（云平台）
            is_postgres = self.database_url.startswith('postgresql://') or \
                         self.database_url.startswith('postgresql+psycopg2://')
            
            if is_postgres:
                # PostgreSQL 配置（云平台）
                # 使用连接池优化性能
                self._engine = create_engine(
                    self.database_url,
                    echo=False,
                    future=True,
                    pool_size=5,  # 连接池大小
                    max_overflow=10,  # 最大溢出连接
                    pool_pre_ping=True,  # 连接前检查（重要：避免连接超时）
                    pool_recycle=3600,  # 1小时后回收连接
                )
            else:
                # SQLite 配置（本地开发）
                db_path = DB_FILES.get(
                    'dev' if self.environment == 'development' else (
                        'test' if self.environment == 'testing' else 'prod'
                    )
                )
                if db_path:
                    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                self._engine = create_engine(
                    self.database_url,
                    echo=False,
                    future=True
                )
        return self._engine

    def get_session(self):
        if self._Session is None:
            engine = self.get_engine()
            self._Session = sessionmaker(
                bind=engine,
                autoflush=False,
                autocommit=False,
                future=True
            )
        return self._Session()
```

### 3.3 环境检测

在 `backend/config.py` 或应用启动文件中：

```python
import os

def get_database_url():
    """获取数据库连接字符串，优先使用环境变量"""
    # 云平台会自动注入 DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # 确保使用正确的协议
        if database_url.startswith('postgres://'):
            # 某些平台可能使用 postgres://，需要转换为 postgresql://
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # 本地开发：使用配置文件
    from database_system.data_storage.config.config import DATABASE_CONFIG
    env = os.getenv('ENV', 'development')
    return DATABASE_CONFIG.get(env)

# 检测是否在云平台
IS_CLOUD = bool(os.getenv('DATABASE_URL'))
IS_VERCEL = bool(os.getenv('VERCEL'))
IS_RENDER = bool(os.getenv('RENDER'))
IS_RAILWAY = bool(os.getenv('RAILWAY'))
IS_FLY_IO = bool(os.getenv('FLY_APP_NAME'))
```

---

## 📝 云平台环境变量配置清单

### 必需的环境变量

```env
# 数据库（云平台会自动注入）
DATABASE_URL=postgresql://user:password@hostname:5432/database_name

# 应用环境
ENV=production

# JWT 密钥
JWT_SECRET=your_secure_jwt_secret_here

# OpenAI API 密钥
OPENAI_API_KEY=sk-your-openai-api-key
```

### 可选的环境变量

```env
# 日志级别
LOG_LEVEL=INFO

# CORS 允许的来源（前端域名）
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,https://your-domain.com

# 其他配置
...
```

---

## 🔐 安全注意事项

### 1. 不要提交敏感信息

- ✅ 使用环境变量存储所有敏感信息
- ❌ 不要将 `.env` 文件提交到 Git
- ✅ 确保 `.gitignore` 包含 `.env`

### 2. 使用 SSL 连接

云平台的 PostgreSQL 通常默认使用 SSL，确保连接字符串包含 SSL 参数：

```python
# 某些平台可能需要显式启用 SSL
database_url = f"{base_url}?sslmode=require"
```

### 3. 连接池配置

对于云平台的 Serverless 函数（如 Vercel），注意：
- 使用连接池避免频繁创建连接
- 设置合理的连接超时时间
- 使用 `pool_pre_ping=True` 检查连接有效性

---

## 🚀 部署步骤总结

### 快速部署流程（以 Render 为例）

1. **准备数据库**
   - 在 Render 创建 PostgreSQL 数据库
   - 复制 `DATABASE_URL`

2. **准备代码**
   - 确保代码支持从 `DATABASE_URL` 环境变量读取配置
   - 更新 `requirements.txt` 包含 `psycopg2-binary`
   - 测试数据库连接逻辑

3. **部署应用**
   - 在 Render 创建 Web Service
   - 连接 Git 仓库
   - 配置构建和启动命令
   - 添加环境变量

4. **数据迁移**
   - 运行数据库迁移脚本（创建表结构）
   - 从 SQLite 导出数据
   - 导入到 PostgreSQL

5. **测试验证**
   - 测试所有 API 端点
   - 验证数据库连接
   - 检查日志是否有错误

---

## 🔍 常见问题

### Q1: 在 Render 找不到 "Environment" 设置入口？

**A:** 以下是详细步骤：

#### 如果您正在创建新服务：

1. 创建 Web Service 时，向下滚动页面
2. 在表单底部，找到 **"Environment Variables"** 或 **"Environment"** 部分
3. 点击 **"Add Environment Variable"** 按钮

#### 如果服务已经创建：

1. **进入服务详情页**：
   - 在 Render 仪表板（Dashboard），点击左侧的 **"Services"** 或查看服务列表
   - 点击您要配置的服务名称

2. **导航到 Settings**：
   - 在服务详情页面顶部，找到标签页：
     - Logs
     - Events  
     - Metrics
     - **Settings** ⭐ 点击这个

3. **找到 Environment Variables**：
   - 在 Settings 页面中，向下滚动
   - 找到 **"Environment Variables"** 部分
   - 如果看不到，可能是页面还在加载，刷新页面

#### 如果还是找不到，尝试以下方法：

- **方法 1**: 直接访问 URL 格式：
  ```
  https://dashboard.render.com/web/[your-service-name]/environment-variables
  ```
  将 `[your-service-name]` 替换为您的服务名称

- **方法 2**: 查看 Render 文档：
  https://render.com/docs/environment-variables

- **方法 3**: 使用 Render CLI（命令行工具）：
  ```bash
  # 安装 Render CLI
  npm install -g render-cli
  
  # 登录
  render login
  
  # 设置环境变量
  render env set DATABASE_URL "postgresql://..."
  ```

#### 替代方案：使用数据库链接功能（最简单）

1. 进入您创建的 PostgreSQL 数据库页面
2. 找到 **"Connections"** 部分
3. 点击 **"Link"** 按钮
4. 选择您的 Web Service
5. Render 会自动将 `DATABASE_URL` 添加到服务环境变量中

这样就不需要手动找 Environment 设置了！

---

### Q2: Vercel 可以部署 FastAPI 吗？

**A:** 可以，但不推荐。Vercel 的 Serverless Functions 有执行时间限制（10秒免费层），FastAPI 更适合部署到支持长时间运行的平台。

**推荐方案：**
- 前端 → Vercel
- 后端 API → Render/Railway/Fly.io
- 数据库 → 托管 PostgreSQL

### Q2.1: 如何从 SQLite 迁移数据到云平台 PostgreSQL？

**A:** 有多种方法：

1. **使用 SQLAlchemy 脚本**（推荐）:
```python
# migrate_to_cloud.py
from sqlalchemy import create_engine
from database_system.business_logic.models import Base

# 连接到两个数据库
sqlite_engine = create_engine('sqlite:///path/to/your.db')
postgres_engine = create_engine(os.getenv('DATABASE_URL'))

# 导出数据并导入
# ... 实现数据迁移逻辑
```

2. **使用 pgloader**（如果可用）

3. **使用 CSV 导出/导入**

### Q3: 部署时出现 "uvicorn: command not found" 错误？

**A:** 这是因为 `requirements.txt` 中缺少 `fastapi` 和 `uvicorn` 依赖。

**解决方案：**

确保 `requirements.txt` 包含以下必需依赖：

```txt
# Web 框架和服务器
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# 数据库相关
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
```

**验证步骤：**

1. 检查 `requirements.txt` 文件
2. 确认包含 `fastapi` 和 `uvicorn`
3. 提交更改到 Git
4. 重新部署（Render 会自动重新构建）

**如果构建成功但启动失败：**

检查日志中的错误信息：
- `uvicorn: command not found` → 缺少 `uvicorn`
- `ModuleNotFoundError: No module named 'fastapi'` → 缺少 `fastapi`
- `ModuleNotFoundError: No module named 'sqlalchemy'` → 缺少 `sqlalchemy`

---

### Q4: 云平台的连接字符串格式不同怎么办？

**A:** 统一转换为标准格式：
```python
def normalize_database_url(url):
    """标准化数据库连接字符串"""
    if url.startswith('postgres://'):
        # 某些平台使用 postgres://，需要转换为 postgresql://
        url = url.replace('postgres://', 'postgresql://', 1)
    return url
```

### Q4: 如何处理连接超时？

**A:** 配置连接池和超时参数：
```python
engine = create_engine(
    database_url,
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=3600,   # 1小时后回收
    connect_args={
        "connect_timeout": 10,  # 连接超时 10 秒
        "options": "-c statement_timeout=30000"  # 查询超时 30 秒
    }
)
```

---

## 📚 推荐的平台组合方案

### 方案 A: 免费/低成本（适合小型项目）

- **前端**: Vercel（免费）
- **后端**: Render（免费层）或 Railway（$5/月）
- **数据库**: Render PostgreSQL（免费层）或 Railway PostgreSQL

### 方案 B: 生产环境（推荐）

- **前端**: Vercel Pro（$20/月）
- **后端**: Render Standard（$7/月）或 Railway
- **数据库**: Render PostgreSQL Starter（$7/月）或 Railway PostgreSQL

### 方案 C: 高性能（企业级）

- **前端**: Vercel Enterprise
- **后端**: Fly.io 或 DigitalOcean App Platform
- **数据库**: 独立 PostgreSQL 实例（如 DigitalOcean Managed Database）

---

## ✅ 部署检查清单

部署前请确认：

- [ ] 数据库已在云平台创建
- [ ] `DATABASE_URL` 环境变量已配置
- [ ] `requirements.txt` 包含 `psycopg2-binary`
- [ ] 代码已更新支持从环境变量读取数据库配置
- [ ] 连接池配置已优化（避免连接超时）
- [ ] SSL 连接已启用（如果平台要求）
- [ ] 环境变量中所有敏感信息已正确设置
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 数据库迁移脚本已准备就绪
- [ ] 回滚方案已准备（保留 SQLite 备份）

---

**下一步**: 完成代码修改后，按照您选择的平台进行部署测试！
