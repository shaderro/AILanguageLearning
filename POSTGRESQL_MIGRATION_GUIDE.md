# PostgreSQL 迁移指南

## 📋 概述

本指南将帮助您将项目从 SQLite 迁移到 PostgreSQL。当前项目使用 SQLAlchemy ORM，这使迁移过程相对简单。

---

## 🔍 当前数据库状态

- **当前数据库**: SQLite
- **ORM**: SQLAlchemy
- **环境**: development, testing, production
- **配置文件位置**: `database_system/data_storage/config/config.py`

---

## 📦 第一步：安装 PostgreSQL 和 Python 驱动

### 1.1 安装 PostgreSQL 服务器

**Windows 方式（推荐）:**
1. 下载 PostgreSQL 安装程序：https://www.postgresql.org/download/windows/
2. 运行安装程序，记住设置的 postgres 用户密码
3. 确保 PostgreSQL 服务已启动（默认端口：5432）

**或使用 Docker（推荐用于开发环境）:**
```bash
docker run --name postgres-dev \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=language_learning_dev \
  -p 5432:5432 \
  -d postgres:16
```

### 1.2 安装 Python PostgreSQL 驱动

在项目根目录执行：

```bash
pip install psycopg2-binary sqlalchemy
```

或者添加到 `requirements.txt`:
```
psycopg2-binary>=2.9.9
sqlalchemy>=2.0.0
```

**注意**: 
- `psycopg2-binary` 是 PostgreSQL 的 Python 适配器（包含编译好的二进制文件，适合快速安装）
- 如果生产环境需要性能优化，可以使用 `psycopg2`（需要编译，性能更好）

---

## 🗄️ 第二步：创建 PostgreSQL 数据库

### 2.1 连接到 PostgreSQL

使用 PostgreSQL 命令行工具 `psql`：

```bash
# Windows (如果已添加到 PATH)
psql -U postgres

# 或使用完整路径
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
```

### 2.2 创建数据库和用户

```sql
-- 创建开发环境数据库
CREATE DATABASE language_learning_dev;

-- 创建测试环境数据库
CREATE DATABASE language_learning_test;

-- 创建生产环境数据库
CREATE DATABASE language_learning_prod;

-- 创建专用用户（可选，但推荐）
CREATE USER language_learning_user WITH PASSWORD 'your_secure_password';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE language_learning_dev TO language_learning_user;
GRANT ALL PRIVILEGES ON DATABASE language_learning_test TO language_learning_user;
GRANT ALL PRIVILEGES ON DATABASE language_learning_prod TO language_learning_user;

-- 退出 psql
\q
```

**或者使用 SQL 文件批量创建** (创建 `create_databases.sql`):

```sql
-- 创建数据库
CREATE DATABASE language_learning_dev;
CREATE DATABASE language_learning_test;
CREATE DATABASE language_learning_prod;

-- 创建用户并授予权限
CREATE USER language_learning_user WITH PASSWORD 'your_secure_password';

\c language_learning_dev
GRANT ALL PRIVILEGES ON DATABASE language_learning_dev TO language_learning_user;

\c language_learning_test
GRANT ALL PRIVILEGES ON DATABASE language_learning_test TO language_learning_user;

\c language_learning_prod
GRANT ALL PRIVILEGES ON DATABASE language_learning_prod TO language_learning_user;
```

执行：
```bash
psql -U postgres -f create_databases.sql
```

---

## ⚙️ 第三步：更新数据库配置

### 3.1 PostgreSQL 连接字符串格式

PostgreSQL 连接字符串格式：
```
postgresql://用户名:密码@主机:端口/数据库名
```

示例：
```
postgresql://postgres:password123@localhost:5432/language_learning_dev
```

### 3.2 需要修改的配置文件

**主要配置文件：**
- `database_system/data_storage/config/config.py` - 数据库配置字典

**需要检查的其他文件（可能包含数据库连接）:**
- `.env` 文件（如果存在）- 环境变量配置
- `backend/config.py` - 后端配置
- 直接使用 `sqlite3` 的文件（需要特别处理）

---

## 🔄 第四步：数据迁移策略

### 4.1 使用 SQLAlchemy 迁移工具（推荐）

#### 安装 Alembic（SQLAlchemy 的迁移工具）:

```bash
pip install alembic
```

添加到 `requirements.txt`:
```
alembic>=1.13.0
```

#### 初始化 Alembic:

```bash
cd database_system
alembic init alembic
```

#### 配置 `alembic/env.py`:

需要连接到您的 models 和数据库配置。

### 4.2 使用 SQLite 导出/PostgreSQL 导入（简单方法）

#### 方法 A: 使用 SQLAlchemy 脚本迁移

创建迁移脚本 `migrate_sqlite_to_postgres.py`（待实现），功能：
1. 从 SQLite 读取所有表数据
2. 创建 PostgreSQL 表结构
3. 将数据插入 PostgreSQL

#### 方法 B: 使用 `pgloader` 工具（跨平台）

安装 pgloader（如果可用）:
```bash
# Windows (需要下载或使用 WSL)
# 或使用 Docker
docker run --rm -it \
  -v /path/to/your/db:/data \
  dimitri/pgloader \
  pgloader /data/dev.db postgresql://user:pass@host:5432/dbname
```

---

## 🔧 第五步：代码兼容性检查

### 5.1 SQLite 特定代码

需要检查并修改以下文件（它们直接使用 `sqlite3`）:

1. **`backend/data_managers/chat_message_manager_db.py`**
   - 直接使用 `sqlite3.connect()`
   - 需要改为使用 SQLAlchemy

2. **`backend/data_managers/vocab_notation_manager.py`**
   - 包含 `sqlite3.connect()` 调用
   - 需要改为使用 SQLAlchemy

3. **`backend/data_managers/asked_tokens_manager.py`**
   - 包含 `sqlite3.connect()` 调用
   - 需要改为使用 SQLAlchemy

4. **`backend/data_managers/grammar_notation_manager.py`**
   - 包含 `sqlite3.connect()` 调用
   - 需要改为使用 SQLAlchemy

5. **其他迁移脚本中的 `sqlite3` 调用**

### 5.2 SQL 语法差异

需要检查以下 SQLite 特性是否在代码中使用：

1. **日期时间函数**
   - SQLite: `datetime('now')`
   - PostgreSQL: `NOW()` 或 `CURRENT_TIMESTAMP`

2. **字符串连接**
   - SQLite: `||` 或 `CONCAT()`
   - PostgreSQL: `||` 或 `CONCAT()`

3. **布尔值**
   - SQLite: 存储为 INTEGER (0/1)
   - PostgreSQL: 原生 BOOLEAN 类型

4. **自动递增**
   - SQLite: `AUTOINCREMENT`
   - PostgreSQL: `SERIAL` 或 `GENERATED ... AS IDENTITY`

### 5.3 Enum 类型处理

好消息：您的代码已经使用了自定义的 `EnumType` 来处理 SQLite 的枚举限制，这应该与 PostgreSQL 兼容。但需要验证：

- SQLite: 存储为字符串（通过 `EnumType`）
- PostgreSQL: 可以使用原生 ENUM 类型，或继续使用字符串（推荐，更兼容）

---

## 📝 第六步：环境变量配置

### 6.1 创建/更新 `.env` 文件

在项目根目录创建或更新 `.env` 文件：

```env
# 环境配置
ENV=development

# PostgreSQL 数据库配置
DATABASE_URL=postgresql://language_learning_user:your_secure_password@localhost:5432/language_learning_dev

# 或者分别为不同环境设置（如果支持）
# DATABASE_URL_DEV=postgresql://user:pass@localhost:5432/language_learning_dev
# DATABASE_URL_TEST=postgresql://user:pass@localhost:5432/language_learning_test
# DATABASE_URL_PROD=postgresql://user:pass@localhost:5432/language_learning_prod

# 其他现有环境变量
JWT_SECRET=your_jwt_secret
OPENAI_API_KEY=your_openai_key
```

### 6.2 更新配置读取逻辑

确保代码支持从环境变量读取 `DATABASE_URL`，如果没有设置则使用配置文件中的值。

---

## 🧪 第七步：测试迁移

### 7.1 测试步骤

1. **创建测试数据库**
   ```sql
   CREATE DATABASE language_learning_test;
   ```

2. **运行表结构创建**
   - 确保所有表在 PostgreSQL 中正确创建
   - 检查索引、外键、约束是否正确

3. **迁移少量测试数据**
   - 从 SQLite 导出少量数据
   - 导入到 PostgreSQL
   - 验证数据完整性

4. **运行应用测试**
   - 测试 CRUD 操作
   - 测试查询性能
   - 测试事务处理

### 7.2 验证清单

- [ ] 所有表都正确创建
- [ ] 所有索引都存在
- [ ] 外键约束正确
- [ ] 枚举值正确转换
- [ ] 日期时间字段正确
- [ ] JSON 字段正确存储和读取
- [ ] 用户认证功能正常
- [ ] 所有 API 端点正常工作

---

## 🚀 第八步：生产环境迁移

### 8.1 迁移前准备

1. **备份 SQLite 数据库**
   ```bash
   # 备份所有环境数据库
   cp database_system/data_storage/data/dev.db dev.db.backup
   cp database_system/data_storage/data/test.db test.db.backup
   cp database_system/data_storage/data/language_learning.db prod.db.backup
   ```

2. **准备回滚方案**
   - 保留 SQLite 数据库备份
   - 准备快速切换回 SQLite 的配置

### 8.2 迁移顺序

1. **开发环境** → 先迁移，充分测试
2. **测试环境** → 验证所有功能
3. **生产环境** → 最后迁移，在低峰期执行

### 8.3 生产环境注意事项

- 使用连接池配置（SQLAlchemy 支持）
- 设置合理的超时时间
- 监控数据库连接数
- 准备性能优化（索引、查询优化）
- 考虑使用 PostgreSQL 的备份和恢复工具

---

## 🔍 第九步：常见问题和解决方案

### 9.1 连接问题

**问题**: 无法连接到 PostgreSQL
- 检查 PostgreSQL 服务是否运行
- 检查防火墙设置（端口 5432）
- 检查用户权限
- 检查 `pg_hba.conf` 配置（允许本地连接）

### 9.2 编码问题

**问题**: 中文或其他特殊字符乱码
- 确保 PostgreSQL 数据库使用 UTF-8 编码：
  ```sql
  CREATE DATABASE dbname WITH ENCODING 'UTF8';
  ```
- 确保连接字符串指定了正确的编码

### 9.3 性能问题

**问题**: 查询变慢
- PostgreSQL 与 SQLite 的查询优化器不同
- 检查索引是否正确创建
- 使用 `EXPLAIN ANALYZE` 分析查询计划
- 考虑添加缺失的索引

### 9.4 数据类型差异

**问题**: 某些数据类型不兼容
- SQLite 的 TEXT 可以存储任意长度，PostgreSQL 的 VARCHAR 有长度限制
- 检查模型定义中的 String 字段长度
- 使用 Text 类型存储长文本

---

## 📚 第十步：文档和清理

### 10.1 更新文档

- 更新 `DATABASE_STRUCTURE.md`
- 更新 `ENV_VARIABLES_EXPLANATION.md`
- 更新 `README.md`（如果有数据库相关说明）

### 10.2 清理

- 移除不再需要的 SQLite 特定代码
- 更新迁移脚本
- 清理旧数据库文件（保留备份）

---

## 🎯 快速检查清单

在开始迁移前，请确认：

- [ ] PostgreSQL 已安装并运行
- [ ] Python 驱动 (`psycopg2-binary`) 已安装
- [ ] 已创建所有需要的数据库（dev/test/prod）
- [ ] 已创建数据库用户并授予权限
- [ ] 已备份所有 SQLite 数据库
- [ ] 已准备好迁移脚本或工具
- [ ] 已准备好回滚方案
- [ ] 已通知团队成员（如果适用）

---

## 🔗 有用的资源

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [SQLAlchemy PostgreSQL 文档](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)
- [psycopg2 文档](https://www.psycopg.org/docs/)
- [Alembic 迁移工具](https://alembic.sqlalchemy.org/)

---

## 📞 下一步

完成上述步骤后，您可以：
1. 开始修改代码以支持 PostgreSQL
2. 执行数据迁移
3. 进行全面测试
4. 逐步切换到生产环境

**重要提示**: 建议先在开发环境中完整测试所有步骤，确认无误后再迁移测试和生产环境。
